//! synth — generate a synthetic stock market whose answer is known in advance.
//!
//! Why: on real data you never know whether a model *should* have found something. Here you do.
//! * `--signal 1` plants weak, realistic-sized patterns (see `truth.txt` written next to the data):
//!   1. short-term reversal: last week's idiosyncratic move tends to partly undo itself,
//!   2. but much less so when trading volume was unusually high (a non-linear interaction a
//!      linear model cannot represent),
//!   3. a small upward drift for stocks within 2% of their 52-week high (a threshold effect).
//! * `--signal 0` uses the *same random numbers* with the patterns switched off. A pipeline that
//!   reports an edge here is fooling itself — that is the point of the test.
//!
//! Everything else mimics real markets loosely: a market factor with volatility clustering
//! (GARCH), sector factors, stock-specific GARCH volatility, occasional jumps, late listings,
//! and volume that rises with surprises. Only +, −, ×, ÷ and √ touch the price path, so a given
//! seed produces identical files on x86 and on a Raspberry Pi.

use quant_pipeline::bars::{write_bars, Bars};
use quant_pipeline::cli::{die, Args};
use quant_pipeline::date;
use quant_pipeline::rng::Rng;
use quant_pipeline::stats;
use std::collections::VecDeque;
use std::fmt::Write as _;
use std::path::{Path, PathBuf};

const USAGE: &str = "\
synth: generate a synthetic stock market (with or without a planted signal)

USAGE:
    synth --out data/synth-planted/raw [options]

OPTIONS:
    --out DIR        where TICKER.csv files are written; universe.csv and truth.txt go to its parent (required)
    --assets N       number of stocks                        [default: 120]
    --years N        years of business days (252 per year)   [default: 22]
    --start DATE     first business day, YYYY-MM-DD          [default: 2004-01-05]
    --signal X       strength of the planted patterns, 0 = none  [default: 1]
    --seed N         random seed (same seed = same noise)    [default: 7]
    --sectors N      number of sectors                       [default: 10]";

// Market factor GARCH(1,1): long-run daily vol 1%.
const MKT_A: f64 = 0.08;
const MKT_B: f64 = 0.90;
const MKT_VAR: f64 = 1.0e-4;
const MKT_DRIFT: f64 = 0.0003;
const SECTOR_VOL: f64 = 0.006;
// Stock-specific GARCH(1,1).
const IDIO_A: f64 = 0.06;
const IDIO_B: f64 = 0.92;
const JUMP_PROB: f64 = 0.003;
const JUMP_SIZE: f64 = 4.0;
// Planted effects, per day, in units of the stock's own daily volatility.
const REVERSAL: f64 = 0.05;
const VOLUME_DAMPING: f64 = 0.9;
const HIGH_DRIFT: f64 = 0.04;

struct Asset {
    beta: f64,
    sigma: f64,
    base_volume: f64,
    sector: usize,
    start_t: usize,
    price: f64,
    var: f64,
    e_prev: f64,
    e_hist: [f64; 5],
    eta: f64,
    maxq: VecDeque<(usize, f64)>,
    bars: Bars,
    closes: Vec<f64>,
}

impl Asset {
    fn max252(&self) -> f64 {
        match self.maxq.front() {
            Some(&(_, p)) => p,
            None => self.price,
        }
    }
    fn push_close(&mut self, t: usize, p: f64) {
        while let Some(&(_, q)) = self.maxq.back() {
            if q <= p {
                self.maxq.pop_back();
            } else {
                break;
            }
        }
        self.maxq.push_back((t, p));
        while let Some(&(s, _)) = self.maxq.front() {
            if s + 252 <= t {
                self.maxq.pop_front();
            } else {
                break;
            }
        }
    }
}

fn main() {
    let args = Args::parse(USAGE, &["out", "assets", "years", "start", "signal", "seed", "sectors"], &[]);
    let out = PathBuf::from(args.req("out"));
    let n = args.usize_or("assets", 120);
    let years = args.usize_or("years", 22);
    let start = date::parse(&args.str_or("start", "2004-01-05")).unwrap_or_else(|e| die(&e));
    let signal = args.f64_or("signal", 1.0);
    let seed = args.u64_or("seed", 7);
    let n_sec = args.usize_or("sectors", 10);
    if n < 20 {
        die("--assets must be at least 20");
    }
    if years < 6 {
        die("--years must be at least 6 (features need one year of history, training needs several)");
    }
    if n_sec == 0 || n_sec > n {
        die("--sectors must be between 1 and --assets");
    }

    let mut days = Vec::with_capacity(years * 252);
    let mut d = start;
    while days.len() < years * 252 {
        let w = date::weekday(d);
        if (1..=5).contains(&w) {
            days.push(d);
        }
        d += 1;
    }
    let t_len = days.len();

    let mut rng = Rng::new(seed);
    let mut assets: Vec<Asset> = (0..n)
        .map(|i| {
            let beta = rng.range(0.6, 1.4);
            let sigma = rng.range(0.010, 0.025);
            let base_volume = 1.0e6 * rng.range(0.3, 4.0);
            let late = rng.uniform() < 0.15;
            let late_t = (rng.uniform() * 0.6 * t_len as f64) as usize;
            let price = rng.range(20.0, 200.0);
            Asset {
                beta,
                sigma,
                base_volume,
                sector: i % n_sec,
                start_t: if late { late_t } else { 0 },
                price,
                var: sigma * sigma,
                e_prev: 0.0,
                e_hist: [0.0; 5],
                eta: 0.0,
                maxq: VecDeque::new(),
                bars: Bars::default(),
                closes: Vec::with_capacity(t_len),
            }
        })
        .collect();

    let sqrt5 = 5f64.sqrt();
    // Hidden states, kept for the ceiling diagnostic at the end.
    let mut e_store: Vec<Vec<f64>> = vec![vec![0.0; t_len]; n];
    let mut eta_store: Vec<Vec<f64>> = vec![vec![0.0; t_len]; n];
    let mut high_store: Vec<Vec<bool>> = vec![vec![false; t_len]; n];
    let mut mkt_var = MKT_VAR;
    let mut mkt_prev = 0.0f64;
    let mut sector_ret = vec![0.0; n_sec];
    for t in 0..t_len {
        mkt_var = MKT_VAR * (1.0 - MKT_A - MKT_B) + MKT_A * mkt_prev * mkt_prev + MKT_B * mkt_var;
        let mkt_shock = mkt_var.sqrt() * rng.normal();
        mkt_prev = mkt_shock;
        let mkt = MKT_DRIFT + mkt_shock;
        for s in sector_ret.iter_mut() {
            *s = SECTOR_VOL * rng.normal();
        }
        for (i, a) in assets.iter_mut().enumerate() {
            // 1) Planted drift, computed only from information available at the previous close.
            let z5 = a.e_hist.iter().sum::<f64>() / (a.sigma * sqrt5);
            let near_high = a.price >= 0.98 * a.max252();
            let damp = 1.0 - VOLUME_DAMPING * (a.eta / 0.6).max(-1.0).min(1.0);
            let drift = signal * a.sigma * (-REVERSAL * z5 * damp + if near_high { HIGH_DRIFT } else { 0.0 });

            // 2) Today's random shocks (drawn identically whatever the signal strength).
            a.var = a.sigma * a.sigma * (1.0 - IDIO_A - IDIO_B) + IDIO_A * a.e_prev * a.e_prev + IDIO_B * a.var;
            let z = rng.normal();
            let jump_u = rng.uniform();
            let jump_z = rng.normal();
            let shock = z + if jump_u < JUMP_PROB { JUMP_SIZE * jump_z } else { 0.0 };
            let e = a.var.sqrt() * shock;
            let r = (a.beta * mkt + sector_ret[a.sector] + drift + e).max(-0.9);
            let prev = a.price;
            let close = prev * (1.0 + r);

            // 3) Bar shape: part of the move happens overnight; high/low add an intraday range.
            let gap = 0.3 * r + 0.003 * rng.normal();
            let open = (prev * (1.0 + gap)).max(0.01);
            let high = open.max(close) * (1.0 + 0.5 * a.sigma * rng.normal().abs());
            let low = open.min(close) * (1.0 - (0.5 * a.sigma * rng.normal().abs()).min(0.5));

            // 4) Volume: persistent, and higher after big stock-specific surprises.
            a.eta = 0.85 * a.eta + 0.25 * rng.normal() + 0.35 * (shock.abs() - 0.8);
            let volume = (a.base_volume * a.eta.exp()).round();

            a.e_prev = e;
            a.e_hist[t % 5] = e;
            a.price = close;
            a.push_close(t, close);
            a.closes.push(close);
            e_store[i][t] = e;
            eta_store[i][t] = a.eta;
            high_store[i][t] = a.price >= 0.98 * a.max252();
            if t >= a.start_t {
                a.bars.push(days[t], open, high, low, close, close, volume);
            }
        }
    }

    std::fs::create_dir_all(&out).unwrap_or_else(|e| die(&format!("cannot create {}: {}", out.display(), e)));
    let dataset_dir: &Path = out.parent().filter(|p| !p.as_os_str().is_empty()).unwrap_or(&out);
    let mut universe = String::from("ticker,sector\n");
    for (i, a) in assets.iter().enumerate() {
        let ticker = format!("SYN{:03}", i + 1);
        write_bars(&out.join(format!("{}.csv", ticker)), &a.bars).unwrap_or_else(|e| die(&e));
        let _ = writeln!(universe, "{},S{:02}", ticker, a.sector + 1);
    }
    let upath = dataset_dir.join("universe.csv");
    std::fs::write(&upath, universe).unwrap_or_else(|e| die(&format!("cannot write {}: {}", upath.display(), e)));

    // Diagnostic: the best forecast anyone could make at the signal date (close of day t), knowing
    // the true formulas and the hidden states (stock-specific shocks, volume state) up to day t.
    // It is the expected planted drift over the holding window (close t+1 -> close t+6) given
    // what is known at t: shocks after t are unknown, the volume state decays at its known rate.
    // It is an approximation (it ignores how the drift reacts to shocks inside the window), and
    // nothing that only sees prices and volumes can match it — so it is a ceiling, not a target.
    let mut ics = Vec::new();
    if signal != 0.0 {
        let mut t = 260;
        while t + 6 < t_len {
            let (mut x, mut y) = (Vec::new(), Vec::new());
            for (i, a) in assets.iter().enumerate() {
                if a.start_t + 252 > t {
                    continue;
                }
                let mut expected = 0.0;
                for j in t + 2..=t + 6 {
                    // z5 behind day j's drift covers shocks j-5 ..= j-1; only those up to t are known.
                    let lo = j - 5;
                    let known: f64 = if lo <= t { e_store[i][lo..=t].iter().sum() } else { 0.0 };
                    let mut eta = eta_store[i][t];
                    for _ in 0..(j - 1 - t) {
                        eta *= 0.85; // expected decay of the volume state (plain multiplies: same on every CPU)
                    }
                    let damp = 1.0 - VOLUME_DAMPING * (eta / 0.6).max(-1.0).min(1.0);
                    let high = if high_store[i][t] { HIGH_DRIFT } else { 0.0 };
                    expected += a.sigma * (-REVERSAL * known / (a.sigma * sqrt5) * damp + high);
                }
                x.push(signal * expected);
                y.push(a.closes[t + 6] / a.closes[t + 1] - 1.0);
            }
            if x.len() >= 20 {
                ics.push(stats::spearman(&x, &y));
            }
            t += 5;
        }
    }
    let ceiling = if ics.is_empty() { 0.0 } else { stats::mean(&ics) };

    let mut truth = String::new();
    let _ = writeln!(truth, "Synthetic market: {} stocks, {} business days ({} .. {}), seed {}, signal strength {}", n, t_len, date::format(days[0]), date::format(days[t_len - 1]), seed, signal);
    let _ = writeln!(truth, "Late listings: {} of {} stocks start trading after the first day.", assets.iter().filter(|a| a.start_t > 0).count(), n);
    let _ = writeln!(truth, "\nPlanted daily drift (in units of each stock's daily volatility), times the signal strength:");
    let _ = writeln!(truth, "  reversal:  -{:.2} x (last 5 days' stock-specific move, standardised)", REVERSAL);
    let _ = writeln!(truth, "             x (1 - {:.1} x clip(volume shock / 0.6, -1, 1))  -> weak when volume was high", VOLUME_DAMPING);
    let _ = writeln!(truth, "  52w-high:  +{:.2} when the price is within 2% of its 252-day high", HIGH_DRIFT);
    if signal != 0.0 {
        let _ = writeln!(truth, "\nApproximate ceiling: mean weekly rank IC of the best forecast possible at the signal date = {:.4}", ceiling);
        let _ = writeln!(truth, "(It knows the true formulas and hidden states; a model that only sees prices and volumes should land below it.)");
    } else {
        let _ = writeln!(truth, "\nNo patterns planted: any model's true IC is zero. Whatever the backtest shows is noise.");
    }
    let tpath = dataset_dir.join("truth.txt");
    std::fs::write(&tpath, &truth).unwrap_or_else(|e| die(&format!("cannot write {}: {}", tpath.display(), e)));
    print!("{}", truth);
    println!("Wrote {} files to {} (+ universe.csv, truth.txt in {})", n, out.display(), dataset_dir.display());
}
