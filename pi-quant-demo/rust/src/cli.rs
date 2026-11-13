//! Tiny command-line parser: `--key value`, `--key=value` and `--flag`.
//! Unknown options are rejected so a typo never silently falls back to a default.

use std::collections::HashMap;

pub struct Args {
    values: HashMap<String, String>,
    flags: Vec<String>,
    usage: &'static str,
}

impl Args {
    pub fn parse(usage: &'static str, value_opts: &[&str], flag_opts: &[&str]) -> Args {
        let argv: Vec<String> = std::env::args().skip(1).collect();
        let mut values = HashMap::new();
        let mut flags = Vec::new();
        let mut i = 0;
        while i < argv.len() {
            let a = argv[i].as_str();
            if a == "-h" || a == "--help" {
                println!("{}", usage);
                std::process::exit(0);
            }
            let body = match a.strip_prefix("--") {
                Some(b) => b,
                None => usage_error(usage, &format!("unexpected argument '{}'", a)),
            };
            if let Some((k, v)) = body.split_once('=') {
                if !value_opts.contains(&k) {
                    usage_error(usage, &format!("unknown option '--{}'", k));
                }
                values.insert(k.to_string(), v.to_string());
                i += 1;
            } else if flag_opts.contains(&body) {
                flags.push(body.to_string());
                i += 1;
            } else if value_opts.contains(&body) {
                if i + 1 >= argv.len() {
                    usage_error(usage, &format!("option '--{}' needs a value", body));
                }
                values.insert(body.to_string(), argv[i + 1].clone());
                i += 2;
            } else {
                usage_error(usage, &format!("unknown option '--{}'", body));
            }
        }
        Args { values, flags, usage }
    }

    pub fn opt(&self, k: &str) -> Option<String> {
        self.values.get(k).cloned()
    }

    pub fn req(&self, k: &str) -> String {
        match self.values.get(k) {
            Some(v) => v.clone(),
            None => usage_error(self.usage, &format!("missing required option '--{}'", k)),
        }
    }

    pub fn str_or(&self, k: &str, d: &str) -> String {
        self.opt(k).unwrap_or_else(|| d.to_string())
    }

    pub fn f64_or(&self, k: &str, d: f64) -> f64 {
        match self.values.get(k) {
            None => d,
            Some(v) => match v.parse::<f64>() {
                Ok(x) if x.is_finite() => x,
                _ => usage_error(self.usage, &format!("'--{}' expects a number, got '{}'", k, v)),
            },
        }
    }

    pub fn usize_or(&self, k: &str, d: usize) -> usize {
        match self.values.get(k) {
            None => d,
            Some(v) => v
                .parse::<usize>()
                .unwrap_or_else(|_| usage_error(self.usage, &format!("'--{}' expects a whole number, got '{}'", k, v))),
        }
    }

    pub fn u64_or(&self, k: &str, d: u64) -> u64 {
        match self.values.get(k) {
            None => d,
            Some(v) => v
                .parse::<u64>()
                .unwrap_or_else(|_| usage_error(self.usage, &format!("'--{}' expects a whole number, got '{}'", k, v))),
        }
    }

    pub fn flag(&self, k: &str) -> bool {
        self.flags.iter().any(|f| f == k)
    }
}

fn usage_error(usage: &str, msg: &str) -> ! {
    eprintln!("error: {}\n\n{}", msg, usage);
    std::process::exit(2);
}

/// Print an error and exit with status 1.
pub fn die(msg: &str) -> ! {
    eprintln!("error: {}", msg);
    std::process::exit(1);
}
