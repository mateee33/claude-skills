// A small neural network (multi-layer perceptron), written from scratch.
//
// features -> H1 ReLU units -> H2 ReLU units -> 1 output, squared loss, AdamW optimiser,
// mini-batches, early stopping on validation IC, and an average over several random seeds
// (single nets trained on noisy data disagree a lot; averaging is the cheapest fix).
//
// Only +, -, *, / and sqrt are used (no exp/tanh from the C math library), and the build uses
// -ffp-contract=off, so a given seed produces the same weights on x86 and ARM.
#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <vector>

#include "panel.hpp"

namespace pq {

struct MlpParams {
  int h1 = 24, h2 = 12;
  int max_epochs = 25;
  int patience = 3;
  int batch = 256;
  double lr = 1e-3;
  double wd = 1e-4;  // decoupled weight decay (AdamW)
  int seeds = 3;
};

struct Net {
  int F = 0, H1 = 0, H2 = 0;
  std::vector<double> W1, b1, W2, b2, W3;  // W1: F x H1, W2: H1 x H2, W3: H2 (row-major)
  double b3 = 0.0;

  void init(int f, int h1, int h2, Rng& rng) {
    F = f;
    H1 = h1;
    H2 = h2;
    auto fill = [&](std::vector<double>& w, size_t n, double sd) {
      w.resize(n);
      for (auto& v : w) v = sd * rng.normal();
    };
    fill(W1, size_t(F) * size_t(H1), std::sqrt(2.0 / F));
    fill(W2, size_t(H1) * size_t(H2), std::sqrt(2.0 / H1));
    fill(W3, size_t(H2), 0.1 * std::sqrt(1.0 / H2));
    b1.assign(size_t(H1), 0.0);
    b2.assign(size_t(H2), 0.0);
    b3 = 0.0;
  }

  // Forward pass; fills the activations needed for backprop.
  double forward(const float* x, double* a1, double* h1, double* a2, double* h2) const {
    const size_t nh1 = size_t(H1), nh2 = size_t(H2);
    for (size_t k = 0; k < nh1; ++k) a1[k] = b1[k];
    for (size_t j = 0; j < size_t(F); ++j) {
      const double xj = x[j];
      const double* w = &W1[j * nh1];
      for (size_t k = 0; k < nh1; ++k) a1[k] += xj * w[k];
    }
    for (size_t k = 0; k < nh1; ++k) h1[k] = a1[k] > 0.0 ? a1[k] : 0.0;
    for (size_t k = 0; k < nh2; ++k) a2[k] = b2[k];
    for (size_t j = 0; j < nh1; ++j) {
      const double hj = h1[j];
      if (hj == 0.0) continue;
      const double* w = &W2[j * nh2];
      for (size_t k = 0; k < nh2; ++k) a2[k] += hj * w[k];
    }
    double out = b3;
    for (size_t k = 0; k < nh2; ++k) {
      h2[k] = a2[k] > 0.0 ? a2[k] : 0.0;
      out += h2[k] * W3[k];
    }
    return out;
  }
};

struct Grads {
  std::vector<double> W1, b1, W2, b2, W3;
  double b3 = 0.0;
  void zero(const Net& n) {
    W1.assign(n.W1.size(), 0.0);
    b1.assign(n.b1.size(), 0.0);
    W2.assign(n.W2.size(), 0.0);
    b2.assign(n.b2.size(), 0.0);
    W3.assign(n.W3.size(), 0.0);
    b3 = 0.0;
  }
};

struct Adam {
  Grads m, v;
  double p1 = 1.0, p2 = 1.0;  // running beta1^t, beta2^t
  static constexpr double b1 = 0.9, b2 = 0.999, eps = 1e-8;

  void step_vec(std::vector<double>& w, std::vector<double>& g, std::vector<double>& m1, std::vector<double>& v1,
                double lr, double c1, double c2, double decay) {
    for (size_t i = 0; i < w.size(); ++i) {
      m1[i] = b1 * m1[i] + (1.0 - b1) * g[i];
      v1[i] = b2 * v1[i] + (1.0 - b2) * g[i] * g[i];
      const double mh = m1[i] / c1, vh = v1[i] / c2;
      w[i] -= lr * (mh / (std::sqrt(vh) + eps) + decay * w[i]);
    }
  }
  void step(Net& n, Grads& g, double lr, double wd) {
    p1 *= b1;
    p2 *= b2;
    const double c1 = 1.0 - p1, c2 = 1.0 - p2;
    step_vec(n.W1, g.W1, m.W1, v.W1, lr, c1, c2, wd);
    step_vec(n.b1, g.b1, m.b1, v.b1, lr, c1, c2, 0.0);
    step_vec(n.W2, g.W2, m.W2, v.W2, lr, c1, c2, wd);
    step_vec(n.b2, g.b2, m.b2, v.b2, lr, c1, c2, 0.0);
    step_vec(n.W3, g.W3, m.W3, v.W3, lr, c1, c2, wd);
    m.b3 = b1 * m.b3 + (1.0 - b1) * g.b3;
    v.b3 = b2 * v.b3 + (1.0 - b2) * g.b3 * g.b3;
    n.b3 -= lr * ((m.b3 / c1) / (std::sqrt(v.b3 / c2) + eps));
  }
};

struct MlpModel {
  std::vector<Net> nets;
  std::vector<int> epochs;  // best epoch of each seed
  double val_ic = 0.0;      // validation IC of the seed average
};

inline void net_predict(const Net& net, const Panel& P, size_t r0, size_t r1, double* out) {
  std::vector<double> a1(size_t(net.H1)), h1(size_t(net.H1)), a2(size_t(net.H2)), h2(size_t(net.H2));
  for (size_t r = r0; r < r1; ++r)
    out[r - r0] = net.forward(&P.X[r * size_t(P.F)], a1.data(), h1.data(), a2.data(), h2.data());
}

inline MlpModel mlp_fit(const Panel& P, size_t tr0, size_t tr1, int vd0, int vd1, const MlpParams& prm,
                        uint64_t seed) {
  const size_t F = size_t(P.F), ntr = tr1 - tr0;
  const size_t vr0 = P.date_start[size_t(vd0)], vr1 = P.date_start[size_t(vd1)], nval = vr1 - vr0;
  const size_t H1 = size_t(prm.h1), H2 = size_t(prm.h2);
  MlpModel model;
  std::vector<double> avg(nval, 0.0), pv(nval);
  std::vector<double> a1(H1), h1(H1), a2(H2), h2(H2), d2(H2), d1(H1);
  for (int s = 0; s < prm.seeds; ++s) {
    Rng rng(Rng::mix(seed, uint64_t(s), 77));
    Net net, best;
    net.init(P.F, prm.h1, prm.h2, rng);
    best = net;
    Grads g;
    Adam opt;
    opt.m.zero(net);
    opt.v.zero(net);
    std::vector<size_t> order(ntr);
    std::iota(order.begin(), order.end(), size_t(0));
    double best_ic = -std::numeric_limits<double>::infinity();
    int best_epoch = 0, bad = 0;
    for (int epoch = 1; epoch <= prm.max_epochs; ++epoch) {
      for (size_t i = ntr; i > 1; --i) std::swap(order[i - 1], order[rng.below(i)]);  // Fisher-Yates
      for (size_t start = 0; start < ntr; start += size_t(prm.batch)) {
        const size_t end = std::min(ntr, start + size_t(prm.batch));
        g.zero(net);
        for (size_t bi = start; bi < end; ++bi) {
          const size_t r = tr0 + order[bi];
          const float* x = &P.X[r * F];
          const double out = net.forward(x, a1.data(), h1.data(), a2.data(), h2.data());
          const double d = out - double(P.y[r]);  // d(0.5*(out-y)^2)/d out
          g.b3 += d;
          for (size_t k = 0; k < H2; ++k) {
            g.W3[k] += d * h2[k];
            d2[k] = a2[k] > 0.0 ? d * net.W3[k] : 0.0;
            g.b2[k] += d2[k];
          }
          for (size_t j = 0; j < H1; ++j) {
            if (h1[j] == 0.0) {
              d1[j] = 0.0;
              continue;
            }
            const double hj = h1[j];
            double* gw = &g.W2[j * H2];
            const double* w = &net.W2[j * H2];
            double s2 = 0.0;
            for (size_t k = 0; k < H2; ++k) {
              gw[k] += hj * d2[k];
              s2 += w[k] * d2[k];
            }
            d1[j] = s2;
          }
          for (size_t k = 0; k < H1; ++k) g.b1[k] += d1[k];
          for (size_t j = 0; j < F; ++j) {
            const double xj = x[j];
            double* gw = &g.W1[j * H1];
            for (size_t k = 0; k < H1; ++k) gw[k] += xj * d1[k];
          }
        }
        const double inv = 1.0 / double(end - start);
        for (auto* vec : {&g.W1, &g.b1, &g.W2, &g.b2, &g.W3})
          for (auto& v : *vec) v *= inv;
        g.b3 *= inv;
        opt.step(net, g, prm.lr, prm.wd);
      }
      net_predict(net, P, vr0, vr1, pv.data());
      const double ic = mean_ic(P, vd0, vd1, pv.data());
      if (ic > best_ic + 1e-6) {
        best_ic = ic;
        best = net;
        best_epoch = epoch;
        bad = 0;
      } else if (++bad >= prm.patience) {
        break;
      }
    }
    net_predict(best, P, vr0, vr1, pv.data());
    for (size_t i = 0; i < nval; ++i) avg[i] += pv[i];
    model.nets.push_back(best);
    model.epochs.push_back(best_epoch);
  }
  model.val_ic = mean_ic(P, vd0, vd1, avg.data());
  return model;
}

inline void mlp_predict(const Panel& P, const MlpModel& m, size_t r0, size_t r1, double* out) {
  std::vector<double> tmp(r1 - r0);
  for (size_t i = 0; i < r1 - r0; ++i) out[i] = 0.0;
  for (const Net& net : m.nets) {
    net_predict(net, P, r0, r1, tmp.data());
    for (size_t i = 0; i < r1 - r0; ++i) out[i] += tmp[i] / double(m.nets.size());
  }
}

}  // namespace pq
