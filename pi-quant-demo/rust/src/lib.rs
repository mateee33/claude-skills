//! Shared code for the Rust stages of the pipeline (standard library only).
//!
//! Binaries:
//! * `fetch`    – download daily bars from Yahoo Finance's public chart endpoint (via `curl`)
//! * `synth`    – generate a synthetic stock market, with or without a planted signal
//! * `prep`     – validate bars, compute point-in-time features and forward-return targets
//! * `backtest` – turn model forecasts into a long/short portfolio, charge costs, report

pub mod bars;
pub mod cli;
pub mod date;
pub mod json;
pub mod rng;
pub mod stats;
pub mod table;

use std::path::Path;

/// One line of `universe.csv`: a ticker and the sector it belongs to.
#[derive(Clone, Debug)]
pub struct Member {
    pub ticker: String,
    pub sector: String,
}

/// Read a `ticker,sector` CSV (header required, `#` comments allowed).
pub fn read_universe(path: &Path) -> Result<Vec<Member>, String> {
    let csv = table::CsvText::open(path)?;
    let header = csv.header();
    let it = table::col(&header, "ticker", path)?;
    let is = table::col(&header, "sector", path)?;
    let mut out = Vec::new();
    for (line, rec) in csv.records() {
        if rec.len() <= it.max(is) {
            return Err(format!("{}:{}: expected ticker,sector", path.display(), line));
        }
        let ticker = rec[it].trim().to_string();
        if ticker.is_empty() {
            continue;
        }
        if !ticker
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '.' || c == '_' || c == '^' || c == '=')
        {
            return Err(format!("{}:{}: suspicious ticker '{}'", path.display(), line, ticker));
        }
        out.push(Member { ticker, sector: rec[is].trim().to_string() });
    }
    if out.is_empty() {
        return Err(format!("{}: no tickers found", path.display()));
    }
    Ok(out)
}
