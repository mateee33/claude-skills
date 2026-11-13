//! Small statistics helpers used by `synth`, `prep` and `backtest`.

pub fn mean(x: &[f64]) -> f64 {
    if x.is_empty() {
        return f64::NAN;
    }
    x.iter().sum::<f64>() / x.len() as f64
}

/// Sample standard deviation (n - 1 in the denominator).
pub fn std_dev(x: &[f64]) -> f64 {
    if x.len() < 2 {
        return f64::NAN;
    }
    let m = mean(x);
    let ss: f64 = x.iter().map(|v| (v - m) * (v - m)).sum();
    (ss / (x.len() - 1) as f64).sqrt()
}

pub fn pearson(x: &[f64], y: &[f64]) -> f64 {
    let n = x.len();
    if n < 3 || n != y.len() {
        return f64::NAN;
    }
    let mx = mean(x);
    let my = mean(y);
    let (mut sxy, mut sxx, mut syy) = (0.0, 0.0, 0.0);
    for i in 0..n {
        let a = x[i] - mx;
        let b = y[i] - my;
        sxy += a * b;
        sxx += a * a;
        syy += b * b;
    }
    if sxx <= 0.0 || syy <= 0.0 {
        return f64::NAN;
    }
    sxy / (sxx * syy).sqrt()
}

/// 0-based ranks; tied values share the average of their ranks.
pub fn average_ranks(x: &[f64]) -> Vec<f64> {
    let n = x.len();
    let mut idx: Vec<usize> = (0..n).collect();
    idx.sort_by(|&a, &b| x[a].total_cmp(&x[b]).then(a.cmp(&b)));
    let mut ranks = vec![0.0; n];
    let mut i = 0;
    while i < n {
        let mut j = i;
        while j + 1 < n && x[idx[j + 1]] == x[idx[i]] {
            j += 1;
        }
        let r = (i + j) as f64 / 2.0;
        for k in i..=j {
            ranks[idx[k]] = r;
        }
        i = j + 1;
    }
    ranks
}

/// Spearman rank correlation.
pub fn spearman(x: &[f64], y: &[f64]) -> f64 {
    pearson(&average_ranks(x), &average_ranks(y))
}

/// Ranks rescaled to a uniform distribution with mean 0 and variance ≈ 1 (range ±√3).
/// This is how every feature and the training target are normalised each week.
pub fn rank_unit_uniform(x: &[f64]) -> Vec<f64> {
    let n = x.len();
    if n < 2 {
        return vec![0.0; n];
    }
    let s12 = 12f64.sqrt();
    average_ranks(x)
        .into_iter()
        .map(|r| (r / (n - 1) as f64 - 0.5) * s12)
        .collect()
}

/// Largest peak-to-trough fall of the compounded equity curve, as a positive fraction.
pub fn max_drawdown(period_returns: &[f64]) -> f64 {
    let mut eq = 1.0f64;
    let mut peak = 1.0f64;
    let mut mdd = 0.0f64;
    for r in period_returns {
        eq *= 1.0 + r;
        if eq > peak {
            peak = eq;
        }
        let dd = 1.0 - eq / peak;
        if dd > mdd {
            mdd = dd;
        }
    }
    mdd
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn ranks_and_corr() {
        assert_eq!(average_ranks(&[10.0, 30.0, 20.0, 20.0]), vec![0.0, 3.0, 1.5, 1.5]);
        let r = spearman(&[1.0, 2.0, 3.0, 4.0], &[10.0, 20.0, 30.0, 40.0]);
        assert!((r - 1.0).abs() < 1e-12);
        let u = rank_unit_uniform(&[3.0, 1.0, 2.0]);
        assert!((u[1] + 3f64.sqrt()).abs() < 1e-12 && u[2].abs() < 1e-12);
        assert!((max_drawdown(&[0.1, -0.5, 0.2]) - 0.5).abs() < 1e-12);
    }
}
