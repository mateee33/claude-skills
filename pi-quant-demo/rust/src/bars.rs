//! Daily price bars and their on-disk format.
//!
//! File format (one file per ticker, `TICKER.csv`):
//! `date,open,high,low,close,adj_close,volume` — dates `YYYY-MM-DD`, ascending.
//! `adj_close` includes dividends and splits; open/high/low/close/volume are split-adjusted.

use crate::date;
use crate::table::{col, parse_f64, CsvText};
use std::io::Write;
use std::path::Path;

#[derive(Default, Clone)]
pub struct Bars {
    pub dates: Vec<i32>,
    pub open: Vec<f64>,
    pub high: Vec<f64>,
    pub low: Vec<f64>,
    pub close: Vec<f64>,
    pub adj_close: Vec<f64>,
    pub volume: Vec<f64>,
}

impl Bars {
    pub fn len(&self) -> usize {
        self.dates.len()
    }
    pub fn is_empty(&self) -> bool {
        self.dates.is_empty()
    }
    pub fn push(&mut self, d: i32, o: f64, h: f64, l: f64, c: f64, a: f64, v: f64) {
        self.dates.push(d);
        self.open.push(o);
        self.high.push(h);
        self.low.push(l);
        self.close.push(c);
        self.adj_close.push(a);
        self.volume.push(v);
    }
}

pub fn write_bars(path: &Path, b: &Bars) -> Result<(), String> {
    let mut s = String::with_capacity(b.len() * 72);
    s.push_str("date,open,high,low,close,adj_close,volume\n");
    for i in 0..b.len() {
        s.push_str(&format!(
            "{},{:.6},{:.6},{:.6},{:.6},{:.6},{:.0}\n",
            date::format(b.dates[i]),
            b.open[i],
            b.high[i],
            b.low[i],
            b.close[i],
            b.adj_close[i],
            b.volume[i]
        ));
    }
    let tmp = path.with_extension("csv.tmp");
    let mut f = std::fs::File::create(&tmp).map_err(|e| format!("cannot create {}: {}", tmp.display(), e))?;
    f.write_all(s.as_bytes()).map_err(|e| format!("write {}: {}", tmp.display(), e))?;
    drop(f);
    std::fs::rename(&tmp, path).map_err(|e| format!("rename to {}: {}", path.display(), e))
}

/// What `read_bars` had to throw away, so the caller can report it.
#[derive(Default)]
pub struct ReadReport {
    pub rows_read: usize,
    pub rows_dropped: usize,
    pub first_problem: Option<String>,
}

/// Read a bar file, dropping rows that fail basic sanity checks rather than trusting them.
pub fn read_bars(path: &Path) -> Result<(Bars, ReadReport), String> {
    let csv = CsvText::open(path)?;
    let h = csv.header();
    let (id, io, ih, il, ic, iv) = (
        col(&h, "date", path)?,
        col(&h, "open", path)?,
        col(&h, "high", path)?,
        col(&h, "low", path)?,
        col(&h, "close", path)?,
        col(&h, "volume", path)?,
    );
    let ia = col(&h, "adj_close", path).ok(); // optional: fall back to close
    let need = [id, io, ih, il, ic, iv].iter().copied().max().unwrap_or(0).max(ia.unwrap_or(0));
    let mut bars = Bars::default();
    let mut rep = ReadReport::default();
    for (line, rec) in csv.records() {
        rep.rows_read += 1;
        let parsed = (|| -> Result<(i32, [f64; 6]), String> {
            if rec.len() <= need {
                return Err(format!("line {}: too few columns", line));
            }
            let d = date::parse(rec[id]).map_err(|e| format!("line {}: {}", line, e))?;
            let o = parse_f64(rec[io], "open", line)?;
            let hi = parse_f64(rec[ih], "high", line)?;
            let lo = parse_f64(rec[il], "low", line)?;
            let c = parse_f64(rec[ic], "close", line)?;
            let a = match ia {
                Some(k) => parse_f64(rec[k], "adj_close", line)?,
                None => c,
            };
            let v = parse_f64(rec[iv], "volume", line)?;
            let vals = [o, hi, lo, c, a, v];
            if vals.iter().any(|x| !x.is_finite()) || o <= 0.0 || hi <= 0.0 || lo <= 0.0 || c <= 0.0 || a <= 0.0 || v < 0.0
            {
                return Err(format!("line {}: non-positive or non-finite value", line));
            }
            // Allow tiny rounding slack, reject clearly inconsistent bars.
            let tol = 1e-4 * c;
            if hi + tol < lo || hi + tol < o.max(c) || lo - tol > o.min(c) {
                return Err(format!("line {}: high/low inconsistent with open/close", line));
            }
            Ok((d, vals))
        })();
        match parsed {
            Ok((d, v)) => {
                if let Some(&last) = bars.dates.last() {
                    if d <= last {
                        rep.rows_dropped += 1;
                        if rep.first_problem.is_none() {
                            rep.first_problem = Some(format!("line {}: date not increasing", line));
                        }
                        continue;
                    }
                }
                bars.push(d, v[0], v[1], v[2], v[3], v[4], v[5]);
            }
            Err(e) => {
                rep.rows_dropped += 1;
                if rep.first_problem.is_none() {
                    rep.first_problem = Some(e);
                }
            }
        }
    }
    Ok((bars, rep))
}
