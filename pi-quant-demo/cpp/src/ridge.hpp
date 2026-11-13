// Ridge regression: the linear baseline every fancier model has to beat.
#pragma once

#include <cmath>
#include <vector>

#include "panel.hpp"

namespace pq {

struct RidgeModel {
  double alpha = 0.0;
  std::vector<double> w;   // one coefficient per feature (features and target are unit-scale ranks)
  std::vector<double> mu;  // feature means on the training rows
};

// Solve A x = b for symmetric positive-definite A (n x n, row-major) by Cholesky.
inline bool cholesky_solve(std::vector<double> A, std::vector<double> b, int n, std::vector<double>& x) {
  const size_t N = size_t(n);
  for (size_t j = 0; j < N; ++j) {
    double d = A[j * N + j];
    for (size_t k = 0; k < j; ++k) d -= A[j * N + k] * A[j * N + k];
    if (!(d > 0.0)) return false;
    d = std::sqrt(d);
    A[j * N + j] = d;
    for (size_t i = j + 1; i < N; ++i) {
      double s = A[i * N + j];
      for (size_t k = 0; k < j; ++k) s -= A[i * N + k] * A[j * N + k];
      A[i * N + j] = s / d;
    }
  }
  for (size_t i = 0; i < N; ++i) {
    double s = b[i];
    for (size_t k = 0; k < i; ++k) s -= A[i * N + k] * b[k];
    b[i] = s / A[i * N + i];
  }
  for (size_t ii = N; ii-- > 0;) {
    double s = b[ii];
    for (size_t k = ii + 1; k < N; ++k) s -= A[k * N + ii] * b[k];
    b[ii] = s / A[ii * N + ii];
  }
  x = b;
  return true;
}

// Fit rows [r0, r1) once per alpha. The penalty is alpha * n_rows, so alpha is on the scale of
// the features' (unit) variance: alpha = 1 roughly halves every coefficient.
inline std::vector<RidgeModel> ridge_path(const Panel& P, size_t r0, size_t r1, const std::vector<double>& alphas) {
  const size_t F = size_t(P.F), n = r1 - r0;
  std::vector<double> mu(F, 0.0), XtX(F * F, 0.0), Xty(F, 0.0);
  double my = 0.0;
  for (size_t r = r0; r < r1; ++r) {
    for (size_t j = 0; j < F; ++j) mu[j] += P.X[r * F + j];
    my += P.y[r];
  }
  for (auto& m : mu) m /= double(n);
  my /= double(n);
  std::vector<double> xc(F);
  for (size_t r = r0; r < r1; ++r) {
    for (size_t j = 0; j < F; ++j) xc[j] = double(P.X[r * F + j]) - mu[j];
    const double yc = double(P.y[r]) - my;
    for (size_t i = 0; i < F; ++i) {
      Xty[i] += xc[i] * yc;
      for (size_t j = 0; j <= i; ++j) XtX[i * F + j] += xc[i] * xc[j];
    }
  }
  for (size_t i = 0; i < F; ++i)
    for (size_t j = 0; j < i; ++j) XtX[j * F + i] = XtX[i * F + j];

  std::vector<RidgeModel> out;
  for (double a : alphas) {
    std::vector<double> A = XtX;
    for (size_t i = 0; i < F; ++i) A[i * F + i] += a * double(n);
    RidgeModel m;
    m.alpha = a;
    m.mu = mu;
    if (!cholesky_solve(A, Xty, P.F, m.w)) m.w.assign(F, 0.0);
    out.push_back(m);
  }
  return out;
}

inline void ridge_predict(const Panel& P, const RidgeModel& m, size_t r0, size_t r1, double* out) {
  const size_t F = size_t(P.F);
  for (size_t r = r0; r < r1; ++r) {
    double s = 0.0;
    for (size_t j = 0; j < F; ++j) s += (double(P.X[r * F + j]) - m.mu[j]) * m.w[j];
    out[r - r0] = s;
  }
}

}  // namespace pq
