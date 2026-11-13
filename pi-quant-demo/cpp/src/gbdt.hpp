// Gradient-boosted regression trees (histogram-based, squared loss), written from scratch.
//
// Each tree is small (depth 3) and fitted to what the previous trees got wrong. Leaves need many
// rows (min_leaf) and are shrunk towards zero (lambda) because weekly stock returns are almost
// pure noise: an unconstrained tree memorises noise perfectly and predicts nothing.
#pragma once

#include <cmath>
#include <limits>
#include <vector>

#include "panel.hpp"

namespace pq {

struct GbdtParams {
  int max_trees = 300;
  int depth = 3;
  int min_leaf = 300;
  double lambda = 50.0;     // leaf shrinkage, in rows
  double lr = 0.05;         // learning rate (applied inside the leaf values)
  double subsample = 0.5;   // fraction of rows each tree sees
  int eval_every = 10;
  int patience = 60;        // stop when validation IC has not improved for this many trees
};

struct Node {
  int feat = -1;  // -1 = leaf
  int thr = 0;    // go left if bin <= thr
  int left = -1, right = -1;
  double value = 0.0;
};

struct Tree {
  std::vector<Node> nodes;
  double predict(const uint8_t* xb) const {
    int i = 0;
    while (nodes[size_t(i)].feat >= 0) {
      const Node& n = nodes[size_t(i)];
      i = (xb[n.feat] <= n.thr) ? n.left : n.right;
    }
    return nodes[size_t(i)].value;
  }
};

struct GbdtModel {
  double base = 0.0;
  std::vector<Tree> trees;
  double val_ic = 0.0;
};

class TreeBuilder {
 public:
  TreeBuilder(const uint8_t* bins, int F, const double* grad, const GbdtParams& p)
      : bins_(bins), F_(size_t(F)), g_(grad), p_(p) {}

  // Rows (local indices) in idx[0..n) are reordered in place.
  Tree build(std::vector<size_t>& idx) {
    Tree t;
    tmp_.resize(idx.size());
    node(t, idx, 0, idx.size(), 0);
    return t;
  }

 private:
  int node(Tree& t, std::vector<size_t>& idx, size_t b, size_t e, int depth) {
    const int id = int(t.nodes.size());
    t.nodes.push_back(Node{});
    double G = 0.0;
    for (size_t i = b; i < e; ++i) G += g_[idx[i]];
    const size_t N = e - b;
    const double leaf = p_.lr * G / (double(N) + p_.lambda);
    if (depth >= p_.depth || N < 2 * size_t(p_.min_leaf)) {
      t.nodes[size_t(id)].value = leaf;
      return id;
    }
    std::vector<double> hg(F_ * kBins, 0.0);
    std::vector<size_t> hn(F_ * kBins, 0);
    for (size_t i = b; i < e; ++i) {
      const size_t r = idx[i];
      const uint8_t* xb = bins_ + r * F_;
      const double gi = g_[r];
      for (size_t f = 0; f < F_; ++f) {
        hg[f * kBins + xb[f]] += gi;
        hn[f * kBins + xb[f]] += 1;
      }
    }
    const double parent = G * G / (double(N) + p_.lambda);
    double best = 0.0;
    int best_f = -1, best_t = -1;
    for (size_t f = 0; f < F_; ++f) {
      double GL = 0.0;
      size_t NL = 0;
      for (int bin = 0; bin < kBins - 1; ++bin) {
        GL += hg[f * kBins + size_t(bin)];
        NL += hn[f * kBins + size_t(bin)];
        const size_t NR = N - NL;
        if (NL < size_t(p_.min_leaf)) continue;
        if (NR < size_t(p_.min_leaf)) break;
        const double GR = G - GL;
        const double gain = GL * GL / (double(NL) + p_.lambda) + GR * GR / (double(NR) + p_.lambda) - parent;
        if (gain > best + 1e-12) {
          best = gain;
          best_f = int(f);
          best_t = bin;
        }
      }
    }
    if (best_f < 0) {
      t.nodes[size_t(id)].value = leaf;
      return id;
    }
    // Stable partition (deterministic on every standard library).
    size_t m = b, k = 0;
    for (size_t i = b; i < e; ++i) {
      const size_t r = idx[i];
      if (bins_[r * F_ + size_t(best_f)] <= best_t)
        idx[m++] = r;
      else
        tmp_[k++] = r;
    }
    for (size_t i = 0; i < k; ++i) idx[m + i] = tmp_[i];
    t.nodes[size_t(id)].feat = best_f;
    t.nodes[size_t(id)].thr = best_t;
    const int L = node(t, idx, b, m, depth + 1);
    const int R = node(t, idx, m, e, depth + 1);
    t.nodes[size_t(id)].left = L;
    t.nodes[size_t(id)].right = R;
    return id;
  }

  const uint8_t* bins_;
  size_t F_;
  const double* g_;
  const GbdtParams& p_;
  std::vector<size_t> tmp_;
};

// Train on rows [tr0, tr1); stop early on the validation dates [vd0, vd1) (rows [vr0, vr1)).
inline GbdtModel gbdt_fit(const Panel& P, size_t tr0, size_t tr1, int vd0, int vd1, const GbdtParams& prm, Rng& rng) {
  const size_t F = size_t(P.F), ntr = tr1 - tr0;
  const size_t vr0 = P.date_start[size_t(vd0)], vr1 = P.date_start[size_t(vd1)], nval = vr1 - vr0;
  const uint8_t* btr = P.bins.data() + tr0 * F;
  GbdtModel model;
  double base = 0.0;
  for (size_t i = 0; i < ntr; ++i) base += P.y[tr0 + i];
  base /= double(ntr);
  model.base = base;
  std::vector<double> Ftr(ntr, base), Fval(nval, base), grad(ntr);
  std::vector<size_t> sub;
  sub.reserve(ntr);
  std::vector<Tree> trees;
  double best_ic = -std::numeric_limits<double>::infinity();
  size_t best_n = 0;
  for (int t = 0; t < prm.max_trees; ++t) {
    for (size_t i = 0; i < ntr; ++i) grad[i] = double(P.y[tr0 + i]) - Ftr[i];
    sub.clear();
    for (size_t i = 0; i < ntr; ++i)
      if (rng.uniform() < prm.subsample) sub.push_back(i);
    TreeBuilder builder(btr, P.F, grad.data(), prm);
    trees.push_back(builder.build(sub));
    const Tree& tree = trees.back();
    for (size_t i = 0; i < ntr; ++i) Ftr[i] += tree.predict(btr + i * F);
    for (size_t i = 0; i < nval; ++i) Fval[i] += tree.predict(P.bins.data() + (vr0 + i) * F);
    if ((t + 1) % prm.eval_every == 0) {
      const double ic = mean_ic(P, vd0, vd1, Fval.data());
      if (ic > best_ic + 1e-9) {
        best_ic = ic;
        best_n = size_t(t + 1);
      } else if (size_t(t + 1) - best_n >= size_t(prm.patience)) {
        break;
      }
    }
  }
  trees.resize(best_n);
  model.trees = std::move(trees);
  model.val_ic = best_ic;
  return model;
}

inline void gbdt_predict(const Panel& P, const GbdtModel& m, size_t r0, size_t r1, double* out) {
  const size_t F = size_t(P.F);
  for (size_t r = r0; r < r1; ++r) {
    double s = m.base;
    for (const Tree& t : m.trees) s += t.predict(P.bins.data() + r * F);
    out[r - r0] = s;
  }
}

}  // namespace pq
