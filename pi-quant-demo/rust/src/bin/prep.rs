//! prep — steps 1 and 2: define the target and build point-in-time features.
//!
//! Input: one `TICKER.csv` of daily bars per stock. Output: a weekly panel (`panel.csv`) with,
//! for each rebalance date and stock, 12 features computed ONLY from data up to that day's close,
//! plus the return the stock went on to make.
//!
//! Timing (the source of most backtest bugs, so spelled out):
//!   features use closes up to and including day t;
//!   you are assumed to trade at the close of day t+LAG (default 1 day later, never the same close);
//!   the target is the return from close t+LAG to close t+LAG+HORIZON (default 5 trading days).
//! A row whose holding window is incomplete (the most recent week, gaps in the data) is dropped.
//!
//! Every feature and the target are converted to cross-sectional ranks each week (scaled to
//! mean 0, variance ≈ 1). The models therefore predict which stocks beat the others that week —
//! not where the market as a whole is going.

use quant_pipeline::bars::read_bars;
use quant_pipeline::cli::{die, Args};
use quant_pipeline::{date, read_universe, stats};
use std::collections::HashMap;
use std::fmt::Write as _;
use std::path::{Path, PathBuf};

const USAGE: &str = "\
prep: validate daily bars and build the weekly feature/target panel

USAGE:
    prep --raw data/real/raw --out data/real/panel.csv [options]

OPTIONS:
    --raw DIR            folder of TICKER.csv bar files (required)
    --out FILE           panel CSV to write; FILE.meta gets the settings (required)
    --universe FILE      ticker,sector CSV; restricts tickers and supplies sectors
    --horizon N          holding period in trading days           [default: 5]
    --lag N              days between signal and trade            [default: 1]
    --step N             trading days between rebalances          [default: 5]
    --min-assets N       skip dates with fewer eligible stocks    [default: 30]
    --min-price X        skip stocks trading below this price     [default: 1]
    --report-moves X     list one-day moves bigger than this      [default: 0.3]";

const HISTORY: usize = 252; // one year of bars before a stock gets features
const FEATURES: [&str; 12] = [
    "r1", "r5", "r21", "mom_12_1", "vol21", "vol63", "vshock", "hi52", "range5", "clv5", "illiq21", "dvol63",
];

struct Stock {
    ticker: String,
    sector: String,
    dates: Vec<i32>,
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>, // dividend- and split-adjusted
    raw_close: Vec<f64>,
    volume: Vec<f64>,
    cal: Vec<usize>, // calendar index of each bar
}

struct Row {
    cal_idx: usize,
    stock: usize,
    feats: [f64; 12],
    vol: f64,
    fwd: f64,
}

fn main() {
    let args = Args::parse(
        USAGE,
        &["raw", "out", "universe", "horizon", "lag", "step", "min-assets", "min-price", "report-moves"],
        &[],
    );
    let raw = PathBuf::from(args.req("raw"));
    let out = PathBuf::from(args.req("out"));
    let horizon = args.usize_or("horizon", 5);
    let lag = args.usize_or("lag", 1);
    let step = args.usize_or("step", 5);
    let min_assets = args.usize_or("min-assets", 30);
    let min_price = args.f64_or("min-price", 1.0);
    let report_moves = args.f64_or("report-moves", 0.3);
    if horizon == 0 || step == 0 {
        die("--horizon and --step must be positive");
    }
    if lag == 0 {
        die("--lag 0 means trading at the same close the signal was computed from, which is not achievable; use 1 or more");
    }
    if min_assets < 10 {
        die("--min-assets must be at least 10 (ranks over fewer stocks are mostly noise)");
    }

    // ---- 1. Load and validate ------------------------------------------------------------
    let universe = args.opt("universe").map(|u| read_universe(Path::new(&u)).unwrap_or_else(|e| die(&e)));
    let mut files: Vec<(String, PathBuf)> = std::fs::read_dir(&raw)
        .unwrap_or_else(|e| die(&format!("cannot read {}: {}", raw.display(), e)))
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.extension().map(|x| x == "csv").unwrap_or(false))
        .filter_map(|p| p.file_stem().and_then(|s| s.to_str()).map(|s| (s.to_string(), p.clone())))
        .collect();
    files.sort();
    let mut sector_of: HashMap<String, String> = HashMap::new();
    if let Some(u) = &universe {
        for m in u {
            sector_of.insert(m.ticker.clone(), m.sector.clone());
        }
        let present: Vec<&String> = files.iter().map(|(t, _)| t).collect();
        let missing: Vec<&str> = u.iter().map(|m| m.ticker.as_str()).filter(|t| !present.iter().any(|p| p == t)).collect();
        if !missing.is_empty() {
            println!("note: {} universe tickers have no data file: {}", missing.len(), missing.join(" "));
        }
        let extra = files.iter().filter(|(t, _)| !sector_of.contains_key(t)).count();
        if extra > 0 {
            println!("note: ignoring {} files not listed in the universe", extra);
        }
        files.retain(|(t, _)| sector_of.contains_key(t));
    }
    if files.is_empty() {
        die(&format!("no usable .csv files in {}", raw.display()));
    }

    let mut stocks: Vec<Stock> = Vec::new();
    let mut big_moves: Vec<(f64, String, i32)> = Vec::new();
    let mut quality = String::new();
    for (ticker, path) in &files {
        let (b, rep) = read_bars(path).unwrap_or_else(|e| die(&e));
        if rep.rows_dropped > 0 {
            let _ = writeln!(
                quality,
                "  {}: dropped {} of {} rows (first: {})",
                ticker,
                rep.rows_dropped,
                rep.rows_read,
                rep.first_problem.as_deref().unwrap_or("?")
            );
        }
        if b.len() < HISTORY + 20 {
            let _ = writeln!(quality, "  {}: skipped, only {} usable bars", ticker, b.len());
            continue;
        }
        let n = b.len();
        let mut st = Stock {
            ticker: ticker.clone(),
            sector: sector_of.get(ticker).cloned().unwrap_or_else(|| "NA".into()),
            dates: b.dates.clone(),
            open: vec![0.0; n],
            high: vec![0.0; n],
            low: vec![0.0; n],
            close: b.adj_close.clone(),
            raw_close: b.close.clone(),
            volume: b.volume.clone(),
            cal: Vec::new(),
        };
        for k in 0..n {
            let f = b.adj_close[k] / b.close[k]; // put open/high/low on the adjusted scale
            st.open[k] = b.open[k] * f;
            st.high[k] = b.high[k] * f;
            st.low[k] = b.low[k] * f;
            if k > 0 {
                let r = st.close[k] / st.close[k - 1] - 1.0;
                if r.abs() > report_moves {
                    big_moves.push((r, ticker.clone(), st.dates[k]));
                }
            }
        }
        stocks.push(st);
    }
    if stocks.len() < min_assets {
        die(&format!("only {} stocks with enough history; need --min-assets {}", stocks.len(), min_assets));
    }

    // ---- 2. Common trading calendar ------------------------------------------------------
    let mut calendar: Vec<i32> = stocks.iter().flat_map(|s| s.dates.iter().copied()).collect();
    calendar.sort_unstable();
    calendar.dedup();
    let mut stocks_with_gaps = 0;
    for s in stocks.iter_mut() {
        s.cal = s.dates.iter().map(|d| calendar.binary_search(d).expect("date in calendar")).collect();
        let span = s.cal[s.cal.len() - 1] - s.cal[0] + 1;
        if span != s.cal.len() {
            stocks_with_gaps += 1;
            let _ = writeln!(quality, "  {}: missing {} trading days inside its history", s.ticker, span - s.cal.len());
        }
    }
    // For each stock: calendar index -> bar index (or none).
    let lookup: Vec<Vec<i32>> = stocks
        .iter()
        .map(|s| {
            let mut v = vec![-1i32; calendar.len()];
            for (k, &c) in s.cal.iter().enumerate() {
                v[c] = k as i32;
            }
            v
        })
        .collect();

    // ---- 3. Weekly snapshots: features, target, cross-sectional ranks --------------------
    let mut rows: Vec<Row> = Vec::new();
    let mut thin_dates = 0usize;
    let mut no_target = 0usize;
    let mut used_dates = 0usize;
    let mut j = 0usize;
    while j < calendar.len() {
        let mut cand: Vec<(usize, [f64; 12], f64, Option<f64>)> = Vec::new();
        for (si, s) in stocks.iter().enumerate() {
            let k = lookup[si][j];
            if k < 0 {
                continue;
            }
            let k = k as usize;
            if k < HISTORY || s.raw_close[k] < min_price {
                continue;
            }
            let f = features(s, k);
            if f.iter().any(|x| !x.is_finite()) {
                continue;
            }
            let (kb, ke) = (k + lag, k + lag + horizon);
            let fwd = if ke < s.close.len() && s.cal[ke] - s.cal[k] == lag + horizon {
                Some(s.close[ke] / s.close[kb] - 1.0)
            } else {
                None
            };
            cand.push((si, f, f[5], fwd));
        }
        if cand.len() < min_assets {
            if !cand.is_empty() {
                thin_dates += 1;
            }
            j += step;
            continue;
        }
        // Rank features across every eligible stock (no peeking at who has a future return)...
        let mut ranked = vec![[0.0f64; 12]; cand.len()];
        for fi in 0..12 {
            let col: Vec<f64> = cand.iter().map(|c| c.1[fi]).collect();
            for (r, v) in ranked.iter_mut().zip(stats::rank_unit_uniform(&col)) {
                r[fi] = v;
            }
        }
        // ...then keep the rows whose holding window is complete.
        let with_target = cand.iter().filter(|c| c.3.is_some()).count();
        no_target += cand.len() - with_target;
        if with_target >= min_assets {
            used_dates += 1;
            for (c, f) in cand.iter().zip(ranked.iter()) {
                if let Some(fwd) = c.3 {
                    rows.push(Row { cal_idx: j, stock: c.0, feats: *f, vol: c.2, fwd });
                }
            }
        }
        j += step;
    }
    if rows.is_empty() {
        die("no complete rows produced; is there at least ~2 years of data?");
    }

    // ---- 4. Write -------------------------------------------------------------------------
    // The training target is the weekly cross-sectional rank of the forward return.
    let mut text = String::with_capacity(rows.len() * 150);
    let _ = writeln!(text, "date,ticker,sector,{},vol,fwd_ret,target", FEATURES.join(","));
    let mut start = 0;
    while start < rows.len() {
        let mut end = start;
        while end < rows.len() && rows[end].cal_idx == rows[start].cal_idx {
            end += 1;
        }
        let mut block: Vec<&Row> = rows[start..end].iter().collect();
        block.sort_by(|a, b| stocks[a.stock].ticker.cmp(&stocks[b.stock].ticker));
        let fwd: Vec<f64> = block.iter().map(|r| r.fwd).collect();
        let target = stats::rank_unit_uniform(&fwd);
        let d = date::format(calendar[rows[start].cal_idx]);
        for (r, t) in block.iter().zip(target) {
            let s = &stocks[r.stock];
            let _ = write!(text, "{},{},{}", d, s.ticker, s.sector);
            for v in r.feats.iter() {
                let _ = write!(text, ",{:.6}", v);
            }
            let _ = writeln!(text, ",{:.8},{:.8},{:.6}", r.vol, r.fwd, t);
        }
        start = end;
    }
    if let Some(parent) = out.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent).unwrap_or_else(|e| die(&format!("cannot create {}: {}", parent.display(), e)));
        }
    }
    std::fs::write(&out, text).unwrap_or_else(|e| die(&format!("cannot write {}: {}", out.display(), e)));
    let meta = format!(
        "horizon={}\nlag={}\nstep={}\nfeatures={}\nrows={}\ndates={}\nstocks={}\n",
        horizon,
        lag,
        step,
        FEATURES.join(","),
        rows.len(),
        used_dates,
        stocks.len()
    );
    let meta_path = PathBuf::from(format!("{}.meta", out.display()));
    std::fs::write(&meta_path, meta).unwrap_or_else(|e| die(&format!("cannot write {}: {}", meta_path.display(), e)));

    // ---- Report -----------------------------------------------------------------------------
    let first = date::format(calendar[rows[0].cal_idx]);
    let last = date::format(calendar[rows[rows.len() - 1].cal_idx]);
    println!(
        "Loaded {} stocks, {} trading days ({} .. {}).",
        stocks.len(),
        calendar.len(),
        date::format(calendar[0]),
        date::format(calendar[calendar.len() - 1])
    );
    println!(
        "Panel: {} weekly dates {} .. {}, {} rows (avg {:.0} stocks/date), {} features.",
        used_dates,
        first,
        last,
        rows.len(),
        rows.len() as f64 / used_dates.max(1) as f64,
        FEATURES.len()
    );
    println!(
        "Timing: features at close t, trade at close t+{}, hold {} days. Dropped {} rows whose holding window was incomplete.",
        lag, horizon, no_target
    );
    if thin_dates > 0 {
        println!("Skipped {} dates with fewer than {} eligible stocks (early history).", thin_dates, min_assets);
    }
    if stocks_with_gaps > 0 || !quality.is_empty() {
        println!("Data quality notes:\n{}", quality.trim_end());
    }
    if !big_moves.is_empty() {
        big_moves.sort_by(|a, b| b.0.abs().total_cmp(&a.0.abs()));
        println!(
            "{} one-day moves above {:.0}% (kept — check that they are real, not bad data; largest first):",
            big_moves.len(),
            report_moves * 100.0
        );
        for (r, t, d) in big_moves.iter().take(12) {
            println!("  {:<6} {}  {:+.1}%", t, date::format(*d), r * 100.0);
        }
    }
    println!("Wrote {} and {}", out.display(), meta_path.display());
}

/// The 12 features for stock `s` at bar `k`, using bars k-252 ..= k only.
fn features(s: &Stock, k: usize) -> [f64; 12] {
    let c = &s.close;
    let lr = |i: usize| (c[i] / c[i - 1]).ln();
    let window_std = |len: usize| {
        let v: Vec<f64> = (k + 1 - len..=k).map(lr).collect();
        stats::std_dev(&v)
    };
    let mean_over = |len: usize, f: &dyn Fn(usize) -> f64| (k + 1 - len..=k).map(f).sum::<f64>() / len as f64;

    let r1 = lr(k);
    let r5 = (c[k] / c[k - 5]).ln();
    let r21 = (c[k] / c[k - 21]).ln();
    let mom = (c[k - 21] / c[k - 252]).ln(); // 12-month momentum, skipping the last month
    let vol21 = window_std(21);
    let vol63 = window_std(63);
    let vshock = ((mean_over(5, &|i| s.volume[i]) + 1.0) / (mean_over(63, &|i| s.volume[i]) + 1.0)).ln();
    let hi = (k + 1 - 252..=k).map(|i| c[i]).fold(f64::MIN, f64::max);
    let hi52 = (c[k] / hi).ln();
    let range5 = mean_over(5, &|i| (s.high[i] - s.low[i]) / c[i]);
    // Where the close sits in the day's range (WorldQuant "101 Formulaic Alphas", alpha #101).
    let clv5 = mean_over(5, &|i| (c[i] - s.open[i]) / (s.high[i] - s.low[i] + 1e-4 * c[i]));
    // Amihud illiquidity: price impact per dollar traded.
    let illiq = (mean_over(21, &|i| (c[i] / c[i - 1] - 1.0).abs() / (c[i] * s.volume[i] + 1.0)) + 1e-15).ln();
    let dvol = (mean_over(63, &|i| c[i] * s.volume[i]) + 1.0).ln();
    [r1, r5, r21, mom, vol21, vol63, vshock, hi52, range5, clv5, illiq, dvol]
}
