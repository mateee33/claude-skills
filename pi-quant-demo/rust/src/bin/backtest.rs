//! backtest — step 5: turn forecasts into trades, charge costs, and report honestly.
//!
//! For every model column in `predictions.csv` and every weekly date:
//!   * rank stocks by forecast (within each sector by default, so the book holds no sector bet),
//!   * buy the top QUANTILE, short the bottom QUANTILE, size by inverse volatility,
//!   * scale to $1 long and $1 short per $1 of capital (dollar-neutral, gross exposure 2x),
//!   * charge COST-BPS on every dollar traded, plus a short-borrow fee,
//!   * realise the stocks' actual forward returns.
//!
//! Luck check: the same rules are then run on many sets of purely random forecasts. That shows
//! what zero skill looks like on this exact data — and how good it can look by chance.
//!
//! Turnover is measured against last week's target weights (price drift between rebalances is
//! ignored — a simplification that slightly understates trading).

use quant_pipeline::cli::{die, Args};
use quant_pipeline::rng::Rng;
use quant_pipeline::table::{col, parse_f64, CsvText};
use quant_pipeline::{date, stats};
use std::collections::HashMap;
use std::fmt::Write as _;
use std::path::{Path, PathBuf};

const USAGE: &str = "\
backtest: long/short portfolio simulation with transaction costs and a luck check

USAGE:
    backtest --pred data/real/predictions.csv --out data/real/results [options]

OPTIONS:
    --pred FILE         predictions CSV from `train` (required)
    --out DIR           where report.txt and CSV results go (required)
    --quantile Q        fraction of each group bought / shorted  [default: 0.2]
    --cost-bps X        cost per dollar traded, in basis points  [default: 5]
    --borrow-bps X      annual fee on the short side, in bps     [default: 50]
    --weighting W       invvol | equal                           [default: invvol]
    --min-sector N      smallest sector traded when neutral      [default: 5]
    --random-trials N   random-forecast portfolios for the luck check [default: 200]
    --seed N            seed for the random forecasts           [default: 2024]
    --chart MODEL       model drawn in the equity chart          [default: ensemble]
    --no-sector-neutral rank across all stocks instead of within sectors";

struct Row {
    ticker: usize,
    sector: usize,
    fwd: f64,
    vol: f64,
    scores: Vec<f64>,
}

#[derive(Clone, Default)]
struct Period {
    ic: f64,
    gross: f64,
    turnover: f64,
    borrow: f64,
    n_long: usize,
    n_short: usize,
}

struct Settings {
    quantile: f64,
    cost: f64,       // fraction per dollar traded
    borrow_bps: f64, // annual
    invvol: bool,
    sector_neutral: bool,
    min_sector: usize,
}

struct Data {
    models: Vec<String>,
    dates: Vec<i32>,
    groups: Vec<(usize, usize)>, // row range of each date
    rows: Vec<Row>,
    n_tickers: usize,
    n_sectors: usize,
}

fn main() {
    let args = Args::parse(
        USAGE,
        &["pred", "out", "quantile", "cost-bps", "borrow-bps", "weighting", "min-sector", "random-trials", "seed", "chart"],
        &["no-sector-neutral"],
    );
    let pred_path = PathBuf::from(args.req("pred"));
    let out_dir = PathBuf::from(args.req("out"));
    let weighting = args.str_or("weighting", "invvol");
    if weighting != "invvol" && weighting != "equal" {
        die("--weighting must be 'invvol' or 'equal'");
    }
    let cost_bps = args.f64_or("cost-bps", 5.0);
    let set = Settings {
        quantile: args.f64_or("quantile", 0.2),
        cost: cost_bps * 1e-4,
        borrow_bps: args.f64_or("borrow-bps", 50.0),
        invvol: weighting == "invvol",
        sector_neutral: !args.flag("no-sector-neutral"),
        min_sector: args.usize_or("min-sector", 5).max(2),
    };
    if !(set.quantile > 0.0 && set.quantile <= 0.5) {
        die("--quantile must be in (0, 0.5]");
    }
    if cost_bps < 0.0 || set.borrow_bps < 0.0 {
        die("costs cannot be negative");
    }
    let trials = args.usize_or("random-trials", 200);
    let chart_model = args.str_or("chart", "ensemble");

    let data = load(&pred_path).unwrap_or_else(|e| die(&e));
    let (models, dates) = (&data.models, &data.dates);
    if dates.len() < 10 {
        die("need at least 10 rebalance dates");
    }
    let gap_days = (dates[dates.len() - 1] - dates[0]) as f64 / (dates.len() - 1) as f64;
    let per_year = 365.25 / gap_days;

    // ---- the models ----------------------------------------------------------------------
    let periods: Vec<Vec<Period>> =
        (0..models.len()).map(|m| simulate(&data, &|i: usize| data.rows[i].scores[m], &set, per_year)).collect();
    let sums: Vec<Summary> = periods.iter().map(|p| summarize(p, set.cost, per_year)).collect();

    // ---- the luck check: identical rules, random forecasts -------------------------------
    let mut rng = Rng::new(args.u64_or("seed", 2024));
    let mut random_runs: Vec<(Summary, Vec<Period>)> = Vec::with_capacity(trials);
    for _ in 0..trials {
        let noise: Vec<f64> = (0..data.rows.len()).map(|_| rng.uniform()).collect();
        let ps = simulate(&data, &|i: usize| noise[i], &set, per_year);
        random_runs.push((summarize(&ps, set.cost, per_year), ps));
    }

    // ---- report ----------------------------------------------------------------------------
    let mut rep = String::new();
    let _ = writeln!(
        rep,
        "Backtest: {} weekly rebalances, {} .. {}, avg {:.0} stocks per date ({} tickers, {} sectors).",
        dates.len(),
        date::format(dates[0]),
        date::format(dates[dates.len() - 1]),
        data.rows.len() as f64 / dates.len() as f64,
        data.n_tickers,
        data.n_sectors
    );
    let _ = writeln!(
        rep,
        "Portfolio: long top {:.0}% / short bottom {:.0}% {}, {} weights, $1 long + $1 short per $1 of capital.",
        set.quantile * 100.0,
        set.quantile * 100.0,
        if set.sector_neutral { "within each sector" } else { "of all stocks" },
        if set.invvol { "inverse-volatility" } else { "equal" }
    );
    let _ = writeln!(
        rep,
        "Costs: {:.1} bps per dollar traded + {:.2}%/yr short borrow. All returns are out-of-sample (walk-forward).\n",
        cost_bps,
        set.borrow_bps / 100.0
    );

    let beats = |m: usize| -> Option<f64> {
        if random_runs.is_empty() {
            return None;
        }
        let k = random_runs.iter().filter(|(s, _)| s.mean_gross < sums[m].mean_gross).count();
        Some(k as f64 / random_runs.len() as f64)
    };
    let _ = writeln!(
        rep,
        "{:<10} {:>8} {:>7} {:>5} {:>9} {:>8} {:>7} {:>7} {:>7} {:>9} {:>10} {:>11}",
        "model", "IC mean", "IC t", "IC>0", "gross/yr", "net/yr", "vol/yr", "Sharpe", "max DD", "turnover", "break-even", "beats luck"
    );
    let mut summary_csv = String::from("model,ic_mean,ic_tstat,ic_positive,gross_ann,net_ann,vol_ann,sharpe_net,max_drawdown,turnover_per_rebalance,breakeven_bps,net_tstat,beats_random,periods\n");
    for (m, name) in models.iter().enumerate() {
        let s = &sums[m];
        let be = breakeven(s);
        let b = beats(m);
        let _ = writeln!(
            rep,
            "{:<10} {:>8.4} {:>7.2} {:>4.0}% {:>8.1}% {:>7.1}% {:>6.1}% {:>7.2} {:>6.1}% {:>8.0}% {:>10} {:>11}",
            name,
            s.ic_mean,
            s.ic_t,
            s.ic_pos * 100.0,
            s.mean_gross * per_year * 100.0,
            s.mean_net * per_year * 100.0,
            s.std_net * per_year.sqrt() * 100.0,
            s.sharpe,
            s.max_dd * 100.0,
            s.mean_turnover * 100.0,
            be.map(|x| format!("{:.1} bps", x)).unwrap_or_else(|| "none".into()),
            b.map(|x| format!("{:.1}%", x * 100.0)).unwrap_or_else(|| "-".into())
        );
        let _ = writeln!(
            summary_csv,
            "{},{:.6},{:.4},{:.4},{:.6},{:.6},{:.6},{:.4},{:.6},{:.6},{},{:.4},{},{}",
            name,
            s.ic_mean,
            s.ic_t,
            s.ic_pos,
            s.mean_gross * per_year,
            s.mean_net * per_year,
            s.std_net * per_year.sqrt(),
            s.sharpe,
            s.max_dd,
            s.mean_turnover,
            be.map(|x| format!("{:.2}", x)).unwrap_or_default(),
            s.net_t,
            b.map(|x| format!("{:.4}", x)).unwrap_or_default(),
            periods[m].len()
        );
    }

    let mut median_run: Option<usize> = None;
    if !random_runs.is_empty() {
        let pick = |f: &dyn Fn(&Summary) -> f64| -> (f64, f64, f64) {
            let mut v: Vec<f64> = random_runs.iter().map(|(s, _)| f(s)).collect();
            v.sort_by(|a, b| a.total_cmp(b));
            let q = |p: f64| v[((v.len() - 1) as f64 * p).round() as usize];
            (q(0.05), q(0.5), q(0.95))
        };
        let ic = pick(&|s| s.ic_mean);
        let ict = pick(&|s| s.ic_t);
        let gr = pick(&|s| s.mean_gross * per_year * 100.0);
        let nt = pick(&|s| s.mean_net * per_year * 100.0);
        let sh = pick(&|s| s.sharpe);
        let _ = writeln!(
            rep,
            "\nLuck check: {} portfolios built from RANDOM forecasts with the same rules and costs.",
            random_runs.len()
        );
        let _ = writeln!(rep, "{:<10} {:>8} {:>7} {:>9} {:>8} {:>7}", "", "IC mean", "IC t", "gross/yr", "net/yr", "Sharpe");
        for (label, idx) in [("5th pct", 0usize), ("median", 1), ("95th pct", 2)] {
            let g = |t: (f64, f64, f64)| [t.0, t.1, t.2][idx];
            let _ = writeln!(
                rep,
                "{:<10} {:>8.4} {:>7.2} {:>8.1}% {:>7.1}% {:>7.2}",
                label,
                g(ic),
                g(ict),
                g(gr),
                g(nt),
                g(sh)
            );
        }
        let _ = writeln!(
            rep,
            "'beats luck' = share of these random portfolios whose gross return the model beat. 1 in 20 random\nportfolios lands above the 95th percentile by definition, so beating it once is not proof of skill."
        );
        let mut order: Vec<usize> = (0..random_runs.len()).collect();
        order.sort_by(|&a, &b| random_runs[a].0.mean_net.total_cmp(&random_runs[b].0.mean_net));
        median_run = Some(order[order.len() / 2]);
    }

    let levels = [0.0, 2.0, 5.0, 10.0, 20.0];
    let _ = writeln!(rep, "\nNet Sharpe ratio at other trading-cost levels (bps per dollar traded):");
    let _ = write!(rep, "{:<10}", "model");
    for l in levels.iter() {
        let _ = write!(rep, " {:>7}", format!("{} bps", l));
    }
    let _ = writeln!(rep);
    for (m, name) in models.iter().enumerate() {
        let _ = write!(rep, "{:<10}", name);
        for l in levels.iter() {
            let _ = write!(rep, " {:>7.2}", summarize(&periods[m], l * 1e-4, per_year).sharpe);
        }
        let _ = writeln!(rep);
    }

    // Calendar-year breakdown.
    let years: Vec<i64> = dates.iter().map(|d| date::year(*d)).collect();
    let mut uniq_years = years.clone();
    uniq_years.dedup();
    let ens_idx = models.iter().position(|m| m == "ensemble");
    let _ = writeln!(
        rep,
        "\nNet return by calendar year (%){}:",
        if ens_idx.is_some() { ", and the ensemble's mean IC that year" } else { "" }
    );
    let _ = write!(rep, "{:<6}", "year");
    for name in models.iter() {
        let _ = write!(rep, " {:>9}", name);
    }
    let _ = writeln!(rep, "{}", if ens_idx.is_some() { format!(" {:>9}", "ens. IC") } else { String::new() });
    let mut yearly_csv = String::from("year,model,net_return,ic_mean,periods\n");
    for y in uniq_years.iter() {
        let _ = write!(rep, "{:<6}", y);
        let idx: Vec<usize> = (0..dates.len()).filter(|&i| years[i] == *y).collect();
        let year_ic = |m: usize| stats::mean(&idx.iter().map(|&i| periods[m][i].ic).filter(|x| x.is_finite()).collect::<Vec<_>>());
        for (m, name) in models.iter().enumerate() {
            let comp = idx.iter().fold(1.0, |acc, &i| acc * (1.0 + net(&periods[m][i], set.cost))) - 1.0;
            let _ = write!(rep, " {:>8.1}%", comp * 100.0);
            let _ = writeln!(yearly_csv, "{},{},{:.6},{:.6},{}", y, name, comp, year_ic(m), idx.len());
        }
        match ens_idx {
            Some(e) => {
                let _ = writeln!(rep, " {:>9.4}", year_ic(e));
            }
            None => {
                let _ = writeln!(rep);
            }
        }
    }

    // Equity chart.
    if let Some(cm) = models.iter().position(|m| *m == chart_model) {
        let a: Vec<f64> = periods[cm].iter().map(|p| net(p, set.cost)).collect();
        let b: Option<Vec<f64>> = median_run.map(|k| random_runs[k].1.iter().map(|p| net(p, set.cost)).collect());
        let _ = writeln!(
            rep,
            "\nGrowth of $1 after costs (log scale): {} = *{}",
            chart_model,
            if b.is_some() { ", median random-forecast portfolio = ." } else { "" }
        );
        rep.push_str(&ascii_chart(&a, b.as_deref(), dates));
    }

    let _ = writeln!(rep, "\nHow to read this");
    let _ = writeln!(rep, "  IC          rank correlation between a forecast and what the stocks then did, averaged over weeks.");
    let _ = writeln!(rep, "              0 = no skill. Signals worth trading in real markets are often only 0.01-0.05.");
    let _ = writeln!(rep, "  IC t        mean IC divided by its standard error. |t| below ~2 is easily produced by luck.");
    let _ = writeln!(rep, "  turnover    dollars traded per rebalance as % of capital (a full flip of the 2x book is 400%).");
    let _ = writeln!(rep, "  break-even  the cost per dollar traded at which the gross edge is fully eaten.");
    let weak: Vec<&str> =
        models.iter().zip(sums.iter()).filter(|(_, s)| s.ic_t.abs() < 2.0).map(|(m, _)| m.as_str()).collect();
    if !weak.is_empty() {
        let _ = writeln!(rep, "  -> IC not distinguishable from zero (|t| < 2): {}", weak.join(", "));
    }
    let losers: Vec<&str> =
        models.iter().zip(sums.iter()).filter(|(_, s)| s.mean_net <= 0.0).map(|(m, _)| m.as_str()).collect();
    if !losers.is_empty() {
        let _ = writeln!(rep, "  -> lose money after costs: {}", losers.join(", "));
    }
    let _ = writeln!(
        rep,
        "  -> {} models were compared on the same data; the best of them looks better than it would live.",
        models.len()
    );

    print!("{}", rep);
    std::fs::create_dir_all(&out_dir).unwrap_or_else(|e| die(&format!("cannot create {}: {}", out_dir.display(), e)));
    write(&out_dir.join("report.txt"), &rep);
    write(&out_dir.join("summary.csv"), &summary_csv);
    write(&out_dir.join("yearly.csv"), &yearly_csv);
    let mut pcsv = String::from("date,model,ic,gross,net,turnover,n_long,n_short\n");
    let mut ecsv = format!("date,{}\n", models.join(","));
    let mut eq = vec![1.0f64; models.len()];
    for (i, d) in dates.iter().enumerate() {
        let ds = date::format(*d);
        for (m, name) in models.iter().enumerate() {
            let p = &periods[m][i];
            let _ = writeln!(pcsv, "{},{},{:.6},{:.8},{:.8},{:.6},{},{}", ds, name, p.ic, p.gross, net(p, set.cost), p.turnover, p.n_long, p.n_short);
            eq[m] *= 1.0 + net(p, set.cost);
        }
        let _ = writeln!(ecsv, "{},{}", ds, eq.iter().map(|x| format!("{:.6}", x)).collect::<Vec<_>>().join(","));
    }
    write(&out_dir.join("periods.csv"), &pcsv);
    write(&out_dir.join("equity.csv"), &ecsv);
    let mut rcsv = String::from("trial,ic_mean,ic_tstat,gross_ann,net_ann,sharpe_net\n");
    for (k, (s, _)) in random_runs.iter().enumerate() {
        let _ = writeln!(rcsv, "{},{:.6},{:.4},{:.6},{:.6},{:.4}", k, s.ic_mean, s.ic_t, s.mean_gross * per_year, s.mean_net * per_year, s.sharpe);
    }
    write(&out_dir.join("random_trials.csv"), &rcsv);
    println!("\nWrote report.txt, summary.csv, yearly.csv, periods.csv, equity.csv, random_trials.csv to {}", out_dir.display());
}

/// Run the portfolio rules over every date, with `score(row)` as the forecast.
fn simulate(data: &Data, score: &dyn Fn(usize) -> f64, set: &Settings, per_year: f64) -> Vec<Period> {
    let mut prev: HashMap<usize, f64> = HashMap::new();
    let mut out = Vec::with_capacity(data.groups.len());
    for &(s, e) in &data.groups {
        let sc: Vec<f64> = (s..e).map(score).collect();
        let fwd: Vec<f64> = data.rows[s..e].iter().map(|r| r.fwd).collect();
        let w = weights(&data.rows[s..e], &sc, set);
        let mut turnover = 0.0;
        for (t, wt) in &w {
            turnover += (wt - prev.get(t).copied().unwrap_or(0.0)).abs();
        }
        for (t, wp) in &prev {
            if !w.contains_key(t) {
                turnover += wp.abs();
            }
        }
        let mut gross = 0.0;
        for r in &data.rows[s..e] {
            if let Some(wt) = w.get(&r.ticker) {
                gross += wt * r.fwd;
            }
        }
        let short_notional: f64 = w.values().filter(|x| **x < 0.0).map(|x| -x).sum();
        out.push(Period {
            ic: stats::spearman(&sc, &fwd),
            gross,
            turnover,
            borrow: short_notional * set.borrow_bps * 1e-4 / per_year,
            n_long: w.values().filter(|x| **x > 0.0).count(),
            n_short: w.values().filter(|x| **x < 0.0).count(),
        });
        prev = w;
    }
    out
}

fn net(p: &Period, cost: f64) -> f64 {
    p.gross - p.turnover * cost - p.borrow
}

struct Summary {
    ic_mean: f64,
    ic_t: f64,
    ic_pos: f64,
    mean_gross: f64,
    mean_net: f64,
    std_net: f64,
    sharpe: f64,
    net_t: f64,
    max_dd: f64,
    mean_turnover: f64,
}

fn breakeven(s: &Summary) -> Option<f64> {
    if s.mean_turnover > 0.0 && s.mean_gross > 0.0 {
        Some(s.mean_gross / s.mean_turnover * 1e4)
    } else {
        None
    }
}

fn summarize(ps: &[Period], cost: f64, per_year: f64) -> Summary {
    let ics: Vec<f64> = ps.iter().map(|p| p.ic).filter(|x| x.is_finite()).collect();
    let nets: Vec<f64> = ps.iter().map(|p| net(p, cost)).collect();
    let gross: Vec<f64> = ps.iter().map(|p| p.gross).collect();
    let turn: Vec<f64> = ps.iter().map(|p| p.turnover).collect();
    let ic_mean = stats::mean(&ics);
    let ic_sd = stats::std_dev(&ics);
    let mean_net = stats::mean(&nets);
    let std_net = stats::std_dev(&nets);
    Summary {
        ic_mean,
        ic_t: ic_mean / (ic_sd / (ics.len() as f64).sqrt()),
        ic_pos: ics.iter().filter(|x| **x > 0.0).count() as f64 / ics.len().max(1) as f64,
        mean_gross: stats::mean(&gross),
        mean_net,
        std_net,
        sharpe: if std_net > 0.0 { mean_net / std_net * per_year.sqrt() } else { 0.0 },
        net_t: mean_net / (std_net / (nets.len() as f64).sqrt()),
        max_dd: stats::max_drawdown(&nets),
        mean_turnover: stats::mean(&turn),
    }
}

/// Target weights for one date (`sc[i]` is the forecast of `block[i]`).
/// Positive = long, negative = short; the longs sum to +1 and the shorts to -1.
fn weights(block: &[Row], sc: &[f64], set: &Settings) -> HashMap<usize, f64> {
    let mut groups: HashMap<usize, Vec<usize>> = HashMap::new();
    for (i, r) in block.iter().enumerate() {
        let key = if set.sector_neutral { r.sector } else { 0 };
        groups.entry(key).or_default().push(i);
    }
    let mut keys: Vec<usize> = groups.keys().copied().collect();
    keys.sort_unstable();
    let mut w: HashMap<usize, f64> = HashMap::new();
    for key in keys {
        let mut g = groups.remove(&key).unwrap_or_default();
        if set.sector_neutral && g.len() < set.min_sector {
            continue; // too few names to build a neutral long/short pair
        }
        g.sort_by(|&a, &b| sc[b].total_cmp(&sc[a]).then(block[a].ticker.cmp(&block[b].ticker)));
        let mut k = ((set.quantile * g.len() as f64).round() as usize).max(1);
        if 2 * k > g.len() {
            k = g.len() / 2;
        }
        if k == 0 {
            continue;
        }
        let budget = g.len() as f64; // each side of a sector gets capital in proportion to its size
        let raw = |i: usize| if set.invvol { 1.0 / block[i].vol.max(1e-4) } else { 1.0 };
        let top = &g[..k];
        let bottom = &g[g.len() - k..];
        let st: f64 = top.iter().map(|&i| raw(i)).sum();
        let sb: f64 = bottom.iter().map(|&i| raw(i)).sum();
        for &i in top {
            *w.entry(block[i].ticker).or_insert(0.0) += budget * raw(i) / st;
        }
        for &i in bottom {
            *w.entry(block[i].ticker).or_insert(0.0) -= budget * raw(i) / sb;
        }
    }
    let long: f64 = w.values().filter(|x| **x > 0.0).sum();
    let short: f64 = w.values().filter(|x| **x < 0.0).map(|x| -x).sum();
    for v in w.values_mut() {
        if *v > 0.0 {
            *v /= long;
        } else if *v < 0.0 {
            *v /= short;
        }
    }
    w
}

fn load(path: &Path) -> Result<Data, String> {
    let csv = CsvText::open(path)?;
    let h = csv.header();
    let (id, it, is, ifw, iv) =
        (col(&h, "date", path)?, col(&h, "ticker", path)?, col(&h, "sector", path)?, col(&h, "fwd_ret", path)?, col(&h, "vol", path)?);
    let first_model = iv + 1;
    if h.len() <= first_model {
        return Err(format!("{}: no model columns after 'vol'", path.display()));
    }
    let models: Vec<String> = h[first_model..].iter().map(|s| s.to_string()).collect();
    let mut tmap: HashMap<String, usize> = HashMap::new();
    let mut smap: HashMap<String, usize> = HashMap::new();
    let mut dates: Vec<i32> = Vec::new();
    let mut groups: Vec<(usize, usize)> = Vec::new();
    let mut rows: Vec<Row> = Vec::new();
    for (line, rec) in csv.records() {
        if rec.len() != h.len() {
            return Err(format!("{}:{}: expected {} columns, got {}", path.display(), line, h.len(), rec.len()));
        }
        let d = date::parse(rec[id]).map_err(|e| format!("{}:{}: {}", path.display(), line, e))?;
        let n_t = tmap.len();
        let t = *tmap.entry(rec[it].to_string()).or_insert(n_t);
        let n_s = smap.len();
        let s = *smap.entry(rec[is].to_string()).or_insert(n_s);
        let mut scores = Vec::with_capacity(models.len());
        for k in first_model..h.len() {
            let v = parse_f64(rec[k], h[k], line)?;
            scores.push(if v.is_finite() { v } else { 0.0 });
        }
        let row = Row {
            ticker: t,
            sector: s,
            fwd: parse_f64(rec[ifw], "fwd_ret", line)?,
            vol: parse_f64(rec[iv], "vol", line)?,
            scores,
        };
        match dates.last() {
            Some(&last) if last == d => {}
            Some(&last) if d < last => return Err(format!("{}:{}: dates must be ascending", path.display(), line)),
            _ => {
                if let Some(g) = groups.last_mut() {
                    g.1 = rows.len();
                }
                dates.push(d);
                groups.push((rows.len(), rows.len()));
            }
        }
        rows.push(row);
    }
    if let Some(g) = groups.last_mut() {
        g.1 = rows.len();
    }
    if rows.is_empty() {
        return Err(format!("{}: no rows", path.display()));
    }
    Ok(Data { models, dates, groups, rows, n_tickers: tmap.len(), n_sectors: smap.len() })
}

fn write(path: &Path, text: &str) {
    std::fs::write(path, text).unwrap_or_else(|e| die(&format!("cannot write {}: {}", path.display(), e)));
}

/// Plain-text chart of compounded growth of $1 (log scale), for terminals without graphics.
fn ascii_chart(a: &[f64], b: Option<&[f64]>, dates: &[i32]) -> String {
    const W: usize = 72;
    const H: usize = 14;
    let curve = |r: &[f64]| -> Vec<f64> {
        let mut eq = 1.0f64;
        r.iter()
            .map(|x| {
                eq *= 1.0 + x;
                eq.max(1e-9).ln()
            })
            .collect()
    };
    let ca = curve(a);
    let cb = b.map(curve);
    let mut lo = ca.iter().copied().fold(0.0f64, f64::min);
    let mut hi = ca.iter().copied().fold(0.0f64, f64::max);
    if let Some(c) = &cb {
        lo = c.iter().copied().fold(lo, f64::min);
        hi = c.iter().copied().fold(hi, f64::max);
    }
    if hi - lo < 1e-9 {
        hi = lo + 1.0;
    }
    let mut grid = vec![vec![' '; W]; H];
    let n = ca.len();
    let row_of = |v: f64| -> usize {
        let fr = (v - lo) / (hi - lo);
        (H - 1) - ((fr * (H - 1) as f64).round() as usize).min(H - 1)
    };
    let zero = row_of(0.0);
    for cell in grid[zero].iter_mut() {
        *cell = '-';
    }
    for x in 0..W {
        let i = (x * (n - 1)) / (W - 1);
        let ra = row_of(ca[i]);
        grid[ra][x] = '*';
        if let Some(c) = &cb {
            let rb = row_of(c[i]);
            grid[rb][x] = if rb == ra { '#' } else { '.' };
        }
    }
    let mut s = String::new();
    for (r, line) in grid.iter().enumerate() {
        let level = hi - (hi - lo) * r as f64 / (H - 1) as f64;
        let label = if r == 0 || r == H - 1 || r == zero { format!("{:>7.2}x", level.exp()) } else { " ".repeat(8) };
        let _ = writeln!(s, "{} |{}", label, line.iter().collect::<String>());
    }
    let (y0, y1) = (date::year(dates[0]), date::year(dates[dates.len() - 1]));
    let _ = writeln!(s, "{} +{}", " ".repeat(8), "-".repeat(W));
    let _ = writeln!(s, "{}  {}{}{}", " ".repeat(8), y0, " ".repeat(W.saturating_sub(8)), y1);
    s
}
