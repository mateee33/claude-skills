//! Calendar dates as `i32` days since 1970-01-01 (proleptic Gregorian).
//! Conversions follow Howard Hinnant's `days_from_civil` / `civil_from_days` algorithms.

pub fn days_from_civil(y: i64, m: u32, d: u32) -> i32 {
    let y = if m <= 2 { y - 1 } else { y };
    let era = (if y >= 0 { y } else { y - 399 }) / 400;
    let yoe = y - era * 400; // [0, 399]
    let m = m as i64;
    let d = d as i64;
    let mp = if m > 2 { m - 3 } else { m + 9 }; // March = 0
    let doy = (153 * mp + 2) / 5 + d - 1; // [0, 365]
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy; // [0, 146096]
    (era * 146097 + doe - 719468) as i32
}

pub fn civil_from_days(z: i32) -> (i64, u32, u32) {
    let z = z as i64 + 719468;
    let era = (if z >= 0 { z } else { z - 146096 }) / 146097;
    let doe = z - era * 146097;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = (doy - (153 * mp + 2) / 5 + 1) as u32;
    let m = (if mp < 10 { mp + 3 } else { mp - 9 }) as u32;
    (if m <= 2 { y + 1 } else { y }, m, d)
}

/// 0 = Sunday ... 6 = Saturday.
pub fn weekday(z: i32) -> u32 {
    ((z as i64 % 7 + 7 + 4) % 7) as u32
}

/// Parse `YYYY-MM-DD`.
pub fn parse(s: &str) -> Result<i32, String> {
    let s = s.trim();
    let b = s.as_bytes();
    if b.len() != 10 || b[4] != b'-' || b[7] != b'-' {
        return Err(format!("bad date '{}' (expected YYYY-MM-DD)", s));
    }
    let y: i64 = s[0..4].parse().map_err(|_| format!("bad year in '{}'", s))?;
    let m: u32 = s[5..7].parse().map_err(|_| format!("bad month in '{}'", s))?;
    let d: u32 = s[8..10].parse().map_err(|_| format!("bad day in '{}'", s))?;
    if !(1..=12).contains(&m) || d == 0 || d > days_in_month(y, m) {
        return Err(format!("invalid date '{}'", s));
    }
    Ok(days_from_civil(y, m, d))
}

pub fn format(z: i32) -> String {
    let (y, m, d) = civil_from_days(z);
    format!("{:04}-{:02}-{:02}", y, m, d)
}

pub fn year(z: i32) -> i64 {
    civil_from_days(z).0
}

fn days_in_month(y: i64, m: u32) -> u32 {
    match m {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        _ => {
            if (y % 4 == 0 && y % 100 != 0) || y % 400 == 0 {
                29
            } else {
                28
            }
        }
    }
}

/// Today's date in UTC, from the system clock.
pub fn today_utc() -> i32 {
    let secs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    (secs / 86_400) as i32
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn round_trip() {
        assert_eq!(days_from_civil(1970, 1, 1), 0);
        assert_eq!(weekday(0), 4); // Thursday
        assert_eq!(format(parse("2024-02-29").unwrap()), "2024-02-29");
        assert!(parse("2023-02-29").is_err());
        for z in -800_000..800_000 {
            let (y, m, d) = civil_from_days(z);
            assert_eq!(days_from_civil(y, m, d), z);
        }
    }
}
