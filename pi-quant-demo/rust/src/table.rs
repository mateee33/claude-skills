//! Minimal CSV reading for the simple, unquoted files this pipeline writes.
//! Blank lines and lines starting with `#` are skipped.

use std::path::Path;

pub struct CsvText {
    text: String,
}

impl CsvText {
    pub fn open(path: &Path) -> Result<CsvText, String> {
        let text = std::fs::read_to_string(path).map_err(|e| format!("cannot read {}: {}", path.display(), e))?;
        Ok(CsvText { text })
    }

    fn lines(&self) -> impl Iterator<Item = (usize, &str)> {
        self.text
            .lines()
            .enumerate()
            .map(|(i, l)| (i + 1, l.trim_end_matches('\r')))
            .filter(|(_, l)| !l.trim().is_empty() && !l.starts_with('#'))
    }

    /// Column names of the first non-comment line.
    pub fn header(&self) -> Vec<&str> {
        match self.lines().next() {
            Some((_, l)) => l.split(',').map(|s| s.trim()).collect(),
            None => Vec::new(),
        }
    }

    /// Data records (everything after the header) with their 1-based line numbers.
    pub fn records(&self) -> impl Iterator<Item = (usize, Vec<&str>)> {
        self.lines().skip(1).map(|(n, l)| (n, l.split(',').collect()))
    }
}

/// Index of a named column, or a readable error.
pub fn col(header: &[&str], name: &str, path: &Path) -> Result<usize, String> {
    header
        .iter()
        .position(|h| h.eq_ignore_ascii_case(name))
        .ok_or_else(|| format!("{}: missing column '{}' (have: {})", path.display(), name, header.join(",")))
}

pub fn parse_f64(s: &str, what: &str, line: usize) -> Result<f64, String> {
    s.trim().parse::<f64>().map_err(|_| format!("line {}: bad {} '{}'", line, what, s))
}
