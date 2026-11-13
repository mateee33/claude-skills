//! fetch — download daily bars for every ticker in a universe file.
//!
//! Uses Yahoo Finance's public chart endpoint through the `curl` command (Rust's standard library
//! has no TLS). The endpoint is unofficial and undocumented: it can change, rate-limit or disappear
//! without notice. Yahoo's terms of service govern what you may do with the data — read them before
//! using it for anything beyond personal experiments, and don't republish it. If the endpoint stops
//! working, put your own CSVs in the output folder (format in `bars.rs`) and skip this step.

use quant_pipeline::bars::{write_bars, Bars};
use quant_pipeline::cli::{die, Args};
use quant_pipeline::{date, json, read_universe};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;

const USAGE: &str = "\
fetch: download daily OHLCV bars from Yahoo Finance (unofficial endpoint, via curl)

USAGE:
    fetch --universe universe.csv --out data/real/raw [options]

OPTIONS:
    --universe FILE   ticker,sector CSV (required)
    --out DIR         where TICKER.csv files are written (required)
    --start DATE      first date to request, YYYY-MM-DD   [default: 2000-01-01]
    --end DATE        drop bars on/after this date        [default: today, UTC]
    --delay-ms N      pause between tickers               [default: 700]
    --retries N       retries per ticker on errors        [default: 3]
    --force           re-download files that already exist";

const USER_AGENT: &str = "Mozilla/5.0 (compatible; pi-quant-demo/1.0)";

fn main() {
    let args = Args::parse(USAGE, &["universe", "out", "start", "end", "delay-ms", "retries"], &["force"]);
    let universe = read_universe(Path::new(&args.req("universe"))).unwrap_or_else(|e| die(&e));
    let out = PathBuf::from(args.req("out"));
    std::fs::create_dir_all(&out).unwrap_or_else(|e| die(&format!("cannot create {}: {}", out.display(), e)));
    let start = date::parse(&args.str_or("start", "2000-01-01")).unwrap_or_else(|e| die(&e));
    // Bars dated today (UTC) may be an unfinished intraday snapshot, so the default end excludes them.
    let end = match args.opt("end") {
        Some(s) => date::parse(&s).unwrap_or_else(|e| die(&e)),
        None => date::today_utc(),
    };
    if end <= start {
        die("--end must be after --start");
    }
    let delay = Duration::from_millis(args.u64_or("delay-ms", 700));
    let retries = args.usize_or("retries", 3);
    let force = args.flag("force");

    println!(
        "Downloading {} tickers, {} .. {} (exclusive) into {}",
        universe.len(),
        date::format(start),
        date::format(end),
        out.display()
    );
    let mut ok = 0usize;
    let mut failed: Vec<String> = Vec::new();
    for (i, m) in universe.iter().enumerate() {
        let path = out.join(format!("{}.csv", m.ticker));
        let tag = format!("[{:>3}/{}] {:<6}", i + 1, universe.len(), m.ticker);
        if path.exists() && !force {
            println!("{} cached (use --force to re-download)", tag);
            ok += 1;
            continue;
        }
        match fetch_one(&m.ticker, start, end, retries) {
            Ok((bars, note)) => {
                if let Err(e) = write_bars(&path, &bars) {
                    die(&e);
                }
                println!(
                    "{} {:>5} bars {} .. {}{}",
                    tag,
                    bars.len(),
                    date::format(bars.dates[0]),
                    date::format(*bars.dates.last().unwrap()),
                    note
                );
                ok += 1;
            }
            Err(e) => {
                println!("{} FAILED: {}", tag, e);
                failed.push(m.ticker.clone());
            }
        }
        if i + 1 < universe.len() {
            std::thread::sleep(delay);
        }
    }
    println!("\n{} of {} tickers available.", ok, universe.len());
    if !failed.is_empty() {
        println!("Failed: {} — the pipeline will run without them.", failed.join(" "));
    }
    if ok == 0 {
        die("nothing downloaded; check your internet connection (see README: 'If the download fails')");
    }
}

fn url_encode(s: &str) -> String {
    let mut out = String::new();
    for b in s.bytes() {
        if b.is_ascii_alphanumeric() || b == b'-' || b == b'.' || b == b'_' {
            out.push(b as char);
        } else {
            out.push_str(&format!("%{:02X}", b));
        }
    }
    out
}

/// Returns the bars plus a note for the progress line.
fn fetch_one(ticker: &str, start: i32, end: i32, retries: usize) -> Result<(Bars, String), String> {
    let url = format!(
        "https://query1.finance.yahoo.com/v8/finance/chart/{}?period1={}&period2={}&interval=1d&events=div%2Csplit&includeAdjustedClose=true",
        url_encode(ticker),
        start as i64 * 86_400,
        end as i64 * 86_400
    );
    let mut last_err = String::from("no attempt made");
    for attempt in 0..=retries {
        if attempt > 0 {
            std::thread::sleep(Duration::from_secs(2u64 << (attempt - 1).min(4)));
        }
        let output = Command::new("curl")
            .args(["-sS", "--max-time", "40", "-A", USER_AGENT, "-w", "\n%{http_code}", &url])
            .output()
            .map_err(|e| format!("could not run curl ({}); install it with: sudo apt install curl", e))?;
        if !output.status.success() {
            last_err = format!("curl failed: {}", String::from_utf8_lossy(&output.stderr).trim());
            continue;
        }
        let body = String::from_utf8_lossy(&output.stdout);
        let (text, code) = match body.rsplit_once('\n') {
            Some((t, c)) => (t, c.trim()),
            None => (&body[..], ""),
        };
        if code == "429" || code.starts_with('5') {
            last_err = format!("HTTP {} (rate limited or server error)", code);
            continue;
        }
        match parse_chart(text, end) {
            Ok(r) => return Ok(r),
            Err(e) => {
                last_err = format!("HTTP {}: {}", code, e);
                if code == "404" {
                    break; // unknown or delisted symbol: retrying will not help
                }
            }
        }
    }
    Err(last_err)
}

fn parse_chart(text: &str, end: i32) -> Result<(Bars, String), String> {
    let root = json::parse(text).map_err(|e| format!("response is not JSON ({})", e))?;
    let chart = root.get("chart").ok_or("no 'chart' object in response")?;
    if let Some(err) = chart.get("error") {
        if !err.is_null() {
            let d = err.get("description").and_then(|d| d.as_str()).unwrap_or("unknown error");
            return Err(format!("Yahoo says: {}", d));
        }
    }
    let res = chart.get("result").and_then(|r| r.idx(0)).ok_or("empty result")?;
    let ts = res.get("timestamp").and_then(|t| t.as_array()).ok_or("no timestamps (no data for this symbol)")?;
    let ind = res.get("indicators").ok_or("no indicators")?;
    let q = ind.get("quote").and_then(|q| q.idx(0)).ok_or("no quote data")?;
    let field = |name: &str| -> Result<&[json::Json], String> {
        let a = q.get(name).and_then(|a| a.as_array()).ok_or_else(|| format!("missing '{}' series", name))?;
        if a.len() != ts.len() {
            return Err(format!("'{}' has {} values for {} timestamps", name, a.len(), ts.len()));
        }
        Ok(a)
    };
    let (o, h, l, c, v) = (field("open")?, field("high")?, field("low")?, field("close")?, field("volume")?);
    let adj = ind
        .get("adjclose")
        .and_then(|a| a.idx(0))
        .and_then(|a| a.get("adjclose"))
        .and_then(|a| a.as_array())
        .filter(|a| a.len() == ts.len());
    let note = if adj.is_none() { "  (no adjusted close: dividends ignored)".to_string() } else { String::new() };

    let mut bars = Bars::default();
    let mut skipped = 0usize;
    for i in 0..ts.len() {
        let t = ts[i].as_f64().ok_or("non-numeric timestamp")?;
        // Daily bars are stamped at the 09:30 New York open (13:30/14:30 UTC), so the UTC
        // calendar date is the trading date.
        let day = (t / 86_400.0).floor() as i32;
        if day >= end {
            continue;
        }
        let vals = (o[i].as_f64(), h[i].as_f64(), l[i].as_f64(), c[i].as_f64());
        let (oo, hh, ll, cc) = match vals {
            (Some(a), Some(b), Some(cc2), Some(d)) if a > 0.0 && b > 0.0 && cc2 > 0.0 && d > 0.0 => (a, b, cc2, d),
            _ => {
                skipped += 1;
                continue;
            }
        };
        let aa = adj.and_then(|a| a[i].as_f64()).filter(|x| *x > 0.0).unwrap_or(cc);
        let vv = v[i].as_f64().filter(|x| *x >= 0.0).unwrap_or(0.0);
        if bars.dates.last() == Some(&day) {
            // Occasional duplicate of the latest bar: keep the later one.
            let n = bars.len() - 1;
            bars.open[n] = oo;
            bars.high[n] = hh;
            bars.low[n] = ll;
            bars.close[n] = cc;
            bars.adj_close[n] = aa;
            bars.volume[n] = vv;
            continue;
        }
        if let Some(&last) = bars.dates.last() {
            if day < last {
                return Err("timestamps out of order".into());
            }
        }
        bars.push(day, oo, hh, ll, cc, aa, vv);
    }
    if bars.len() < 300 {
        return Err(format!("only {} usable bars returned (need at least 300)", bars.len()));
    }
    let note = if skipped > 0 { format!("{}  ({} incomplete bars skipped)", note, skipped) } else { note };
    Ok((bars, note))
}
