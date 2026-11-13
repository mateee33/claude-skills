// train — steps 3, 4 and 6: fit models and test them walk-forward, one calendar year at a time.
//
// For each test year Y (the "fold"):
//   train on every week before year Y-1, minus a purge gap,
//   tune / early-stop on the weeks of year Y-1 (again minus a purge gap),
//   then predict every week of year Y with the models frozen.
// The purge gap drops the last weeks whose holding periods would overlap the next block — their
// returns were not yet known at the time, so using them would leak the future into training.
// Then roll forward one year and retrain from scratch (step 6).
//
// Models, all producing a score per stock per week (higher = expected to do better):
//   reversal  no learning: minus last week's return (a classic one-line rule, the baseline)
//   ridge     linear regression with an L2 penalty chosen on the validation year
//   gbdt      gradient-boosted trees (catches thresholds and interactions)
//   mlp       small neural network, average of several seeds
//   ensemble  average of the three learned models after standardising each one weekly
// (The zero-skill control — random forecasts — is run many times over in the backtest.)
//
// Build: g++ -std=c++17 -O3 -ffp-contract=off -pthread -o bin/train cpp/src/train.cpp

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#include "common.hpp"
#include "gbdt.hpp"
#include "mlp.hpp"
#include "panel.hpp"
#include "ridge.hpp"

using namespace pq;

static const char* kUsage =
    "train: walk-forward training and out-of-sample prediction (C++ model engine)\n"
    "\n"
    "USAGE:\n"
    "    train --panel data/real/panel.csv --out data/real/predictions.csv [options]\n"
    "\n"
    "OPTIONS:\n"
    "    --panel FILE          feature panel from `prep` (required)\n"
    "    --out FILE            out-of-sample predictions CSV (required)\n"
    "    --log-dir DIR         where folds.csv and ridge_coefs.csv go   [default: folder of --out]\n"
    "    --threads N           folds trained in parallel                [default: all cores]\n"
    "    --first-test-year Y   first year predicted                     [default: auto]\n"
    "    --min-train-years N   training years before the first test     [default: 3]\n"
    "    --seed N              random seed                              [default: 7]\n"
    "    --mlp-seeds N         networks averaged per fold               [default: 3]\n"
    "    --mlp-epochs N        maximum training epochs                  [default: 25]\n"
    "    --mlp-hidden A,B      hidden layer sizes                       [default: 24,12]\n"
    "    --gbdt-trees N        maximum trees                            [default: 300]\n"
    "    --gbdt-depth N        tree depth                               [default: 3]\n"
    "    --gbdt-min-leaf N     minimum rows per leaf                    [default: 300]\n"
    "    --quick               smaller settings for slow boards (1 net, 10 epochs, 120 trees)\n";

struct Options {
  std::string panel, out, log_dir;
  int threads = 0;
  int first_test_year = 0;
  int min_train_years = 3;
  uint64_t seed = 7;
  GbdtParams gbdt;
  MlpParams mlp;
  std::vector<double> alphas{0.001, 0.01, 0.1, 1.0, 10.0};
};

static Options parse_args(int argc, char** argv) {
  Options o;
  auto need = [&](int& i) -> std::string {
    if (i + 1 >= argc) die(std::string("option ") + argv[i] + " needs a value\n\n" + kUsage);
    return argv[++i];
  };
  auto to_int = [&](const std::string& s, const char* name) {
    char* end = nullptr;
    long v = std::strtol(s.c_str(), &end, 10);
    if (end == s.c_str() || *end != '\0' || v < 0) die(std::string(name) + " expects a whole number, got '" + s + "'");
    return int(v);
  };
  bool quick = false;
  for (int i = 1; i < argc; ++i) {
    const std::string a = argv[i];
    if (a == "-h" || a == "--help") {
      std::printf("%s", kUsage);
      std::exit(0);
    } else if (a == "--panel") {
      o.panel = need(i);
    } else if (a == "--out") {
      o.out = need(i);
    } else if (a == "--log-dir") {
      o.log_dir = need(i);
    } else if (a == "--threads") {
      o.threads = to_int(need(i), "--threads");
    } else if (a == "--first-test-year") {
      o.first_test_year = to_int(need(i), "--first-test-year");
    } else if (a == "--min-train-years") {
      o.min_train_years = to_int(need(i), "--min-train-years");
    } else if (a == "--seed") {
      o.seed = uint64_t(to_int(need(i), "--seed"));
    } else if (a == "--mlp-seeds") {
      o.mlp.seeds = std::max(1, to_int(need(i), "--mlp-seeds"));
    } else if (a == "--mlp-epochs") {
      o.mlp.max_epochs = std::max(1, to_int(need(i), "--mlp-epochs"));
    } else if (a == "--mlp-hidden") {
      auto parts = split(need(i), ',');
      if (parts.size() != 2) die("--mlp-hidden expects two sizes, e.g. 24,12");
      o.mlp.h1 = std::max(1, to_int(parts[0], "--mlp-hidden"));
      o.mlp.h2 = std::max(1, to_int(parts[1], "--mlp-hidden"));
    } else if (a == "--gbdt-trees") {
      o.gbdt.max_trees = std::max(1, to_int(need(i), "--gbdt-trees"));
    } else if (a == "--gbdt-depth") {
      o.gbdt.depth = std::max(1, to_int(need(i), "--gbdt-depth"));
    } else if (a == "--gbdt-min-leaf") {
      o.gbdt.min_leaf = std::max(1, to_int(need(i), "--gbdt-min-leaf"));
    } else if (a == "--quick") {
      quick = true;
    } else {
      die("unknown option '" + a + "'\n\n" + kUsage);
    }
  }
  if (o.panel.empty() || o.out.empty()) die(std::string("--panel and --out are required\n\n") + kUsage);
  if (quick) {
    o.mlp.seeds = 1;
    o.mlp.max_epochs = 10;
    o.gbdt.max_trees = 120;
    o.gbdt.patience = 40;
  }
  if (o.log_dir.empty()) {
    const size_t p = o.out.find_last_of('/');
    o.log_dir = (p == std::string::npos) ? "." : o.out.substr(0, p);
  }
  return o;
}

struct Fold {
  int year = 0;
  int train_end = 0;              // train dates [0, train_end)
  int val_begin = 0, val_end = 0;  // validation dates
  int test_begin = 0, test_end = 0;
};

enum Model { REVERSAL, RIDGE, GBDT, MLP, ENSEMBLE, NMODELS };
static const char* kModelNames[NMODELS] = {"reversal", "ridge", "gbdt", "mlp", "ensemble"};

struct FoldResult {
  std::vector<double> pred[NMODELS];  // aligned to the test rows
  double ridge_alpha = 0, ridge_val = 0, gbdt_val = 0, mlp_val = 0;
  std::vector<double> ridge_w;
  size_t gbdt_trees = 0;
  std::vector<int> mlp_epochs;
  size_t n_train = 0, n_val = 0, n_test = 0;
  double seconds = 0;
};

// Standardise one model's scores within each date, so models on different scales can be averaged.
static void zscore_by_date(const Panel& P, const Fold& f, const std::vector<double>& in, std::vector<double>& out) {
  const size_t base = P.date_start[size_t(f.test_begin)];
  out.assign(in.size(), 0.0);
  for (int d = f.test_begin; d < f.test_end; ++d) {
    const size_t a = P.date_start[size_t(d)] - base, b = P.date_start[size_t(d) + 1] - base;
    double m = 0, s = 0;
    for (size_t i = a; i < b; ++i) m += in[i];
    m /= double(b - a);
    for (size_t i = a; i < b; ++i) s += (in[i] - m) * (in[i] - m);
    s = std::sqrt(s / double(b - a));
    for (size_t i = a; i < b; ++i) out[i] = s > 1e-12 ? (in[i] - m) / s : 0.0;
  }
}

static FoldResult run_fold(const Panel& P, const Fold& f, const Options& o, int r5) {
  Timer timer;
  FoldResult res;
  const size_t tr0 = 0, tr1 = P.date_start[size_t(f.train_end)];
  const size_t vr0 = P.date_start[size_t(f.val_begin)], vr1 = P.date_start[size_t(f.val_end)];
  const size_t te0 = P.date_start[size_t(f.test_begin)], te1 = P.date_start[size_t(f.test_end)];
  res.n_train = tr1 - tr0;
  res.n_val = vr1 - vr0;
  res.n_test = te1 - te0;
  const size_t nt = te1 - te0;
  for (auto& p : res.pred) p.assign(nt, 0.0);
  const uint64_t fy = uint64_t(f.year);

  // Baseline: short-term reversal (no fitting at all).
  for (size_t i = 0; i < nt; ++i) res.pred[REVERSAL][i] = r5 >= 0 ? -double(P.X[(te0 + i) * size_t(P.F) + size_t(r5)]) : 0.0;

  // Ridge: pick the penalty with the best validation IC.
  {
    auto path = ridge_path(P, tr0, tr1, o.alphas);
    std::vector<double> pv(vr1 - vr0);
    double best = -1e9;
    size_t bi = 0;
    for (size_t k = 0; k < path.size(); ++k) {
      ridge_predict(P, path[k], vr0, vr1, pv.data());
      const double ic = mean_ic(P, f.val_begin, f.val_end, pv.data());
      if (ic > best + 1e-12) {
        best = ic;
        bi = k;
      }
    }
    ridge_predict(P, path[bi], te0, te1, res.pred[RIDGE].data());
    res.ridge_alpha = path[bi].alpha;
    res.ridge_val = best;
    res.ridge_w = path[bi].w;
  }

  // Gradient-boosted trees.
  {
    Rng rng(Rng::mix(o.seed, fy, 1));
    GbdtModel m = gbdt_fit(P, tr0, tr1, f.val_begin, f.val_end, o.gbdt, rng);
    gbdt_predict(P, m, te0, te1, res.pred[GBDT].data());
    res.gbdt_trees = m.trees.size();
    res.gbdt_val = m.val_ic;
  }

  // Neural network.
  {
    MlpModel m = mlp_fit(P, tr0, tr1, f.val_begin, f.val_end, o.mlp, Rng::mix(o.seed, fy, 2));
    mlp_predict(P, m, te0, te1, res.pred[MLP].data());
    res.mlp_epochs = m.epochs;
    res.mlp_val = m.val_ic;
  }

  // Ensemble of the learned models.
  {
    std::vector<double> z;
    for (int m : {RIDGE, GBDT, MLP}) {
      zscore_by_date(P, f, res.pred[m], z);
      for (size_t i = 0; i < nt; ++i) res.pred[ENSEMBLE][i] += z[i] / 3.0;
    }
  }
  res.seconds = timer.seconds();
  return res;
}

int main(int argc, char** argv) {
  Options o = parse_args(argc, argv);
  Timer total;
  Panel P = load_panel(o.panel);
  const int r5 = P.find_feature("r5");
  if (r5 < 0) std::fprintf(stderr, "warning: no 'r5' feature; the reversal baseline will be flat\n");
  const int n_dates = int(P.dates.size());
  const int purge = (P.lag + P.horizon + P.step - 1) / P.step;  // rebalance dates until a target is known

  // ---- folds -------------------------------------------------------------------------------
  std::vector<Fold> folds;
  const int first_year = P.year_of_date.front(), last_year = P.year_of_date.back();
  const int start_year = o.first_test_year ? o.first_test_year : first_year + o.min_train_years + 1;
  auto first_date_of = [&](int y) {
    for (int d = 0; d < n_dates; ++d)
      if (P.year_of_date[size_t(d)] >= y) return d;
    return n_dates;
  };
  for (int y = start_year; y <= last_year; ++y) {
    Fold f;
    f.year = y;
    f.test_begin = first_date_of(y);
    f.test_end = first_date_of(y + 1);
    f.val_begin = first_date_of(y - 1);
    f.val_end = f.test_begin - purge + 1;
    f.train_end = f.val_begin - purge + 1;
    if (f.test_end <= f.test_begin || f.val_end <= f.val_begin || f.train_end < 20) continue;
    if (P.year_of_date[size_t(f.val_begin)] != y - 1) continue;  // no data in the validation year
    folds.push_back(f);
  }
  if (folds.empty()) die("not enough history for even one walk-forward fold (need ~" + std::to_string(o.min_train_years + 2) + " years)");

  unsigned hw = std::thread::hardware_concurrency();
  int threads = o.threads > 0 ? o.threads : int(hw ? hw : 1);
  threads = std::max(1, std::min(threads, int(folds.size())));
  std::printf("Panel: %zu rows, %d weekly dates (%s .. %s), %d features. Purge gap: %d dates.\n", P.n, n_dates,
              P.dates.front().c_str(), P.dates.back().c_str(), P.F, purge);
  std::printf("Walk-forward: %zu folds (test years %d..%d), %d thread%s. MLP %dx(%d,%d) x%d seeds, GBDT <=%d trees.\n",
              folds.size(), folds.front().year, folds.back().year, threads, threads == 1 ? "" : "s", P.F, o.mlp.h1,
              o.mlp.h2, o.mlp.seeds, o.gbdt.max_trees);
  std::fflush(stdout);

  // ---- run folds in parallel (largest training sets first for load balance) -----------------
  std::vector<FoldResult> results(folds.size());
  std::vector<size_t> order(folds.size());
  for (size_t i = 0; i < order.size(); ++i) order[i] = order.size() - 1 - i;
  std::atomic<size_t> next{0};
  std::mutex io;
  size_t done = 0;
  auto worker = [&]() {
    for (;;) {
      const size_t k = next.fetch_add(1);
      if (k >= order.size()) return;
      const size_t fi = order[k];
      results[fi] = run_fold(P, folds[fi], o, r5);
      std::lock_guard<std::mutex> lock(io);
      ++done;
      const FoldResult& r = results[fi];
      std::printf("  [%2zu/%zu] test %d: train %6zu rows, val %5zu, test %5zu | val IC ridge %+.4f  gbdt %+.4f (%zu trees)  mlp %+.4f | %.1fs\n",
                  done, folds.size(), folds[fi].year, r.n_train, r.n_val, r.n_test, r.ridge_val, r.gbdt_val,
                  r.gbdt_trees, r.mlp_val, r.seconds);
      std::fflush(stdout);
    }
  };
  std::vector<std::thread> pool;
  for (int t = 0; t < threads; ++t) pool.emplace_back(worker);
  for (auto& t : pool) t.join();

  // ---- write predictions (date order) and fold logs ----------------------------------------
  FILE* fp = std::fopen(o.out.c_str(), "wb");
  if (!fp) die("cannot write " + o.out);
  std::fprintf(fp, "date,ticker,sector,fwd_ret,vol");
  for (int m = 0; m < NMODELS; ++m) std::fprintf(fp, ",%s", kModelNames[m]);
  std::fprintf(fp, "\n");
  for (size_t fi = 0; fi < folds.size(); ++fi) {
    const size_t te0 = P.date_start[size_t(folds[fi].test_begin)];
    for (size_t i = 0; i < results[fi].n_test; ++i) {
      const size_t r = te0 + i;
      std::fprintf(fp, "%s,%s,%s,%.8g,%.8g", P.dates[size_t(P.date_of_row[r])].c_str(), P.ticker[r].c_str(),
                   P.sector[r].c_str(), double(P.fwd[r]), double(P.vol[r]));
      for (int m = 0; m < NMODELS; ++m) std::fprintf(fp, ",%.7g", results[fi].pred[m][i]);
      std::fprintf(fp, "\n");
    }
  }
  std::fclose(fp);

  const std::string folds_path = o.log_dir + "/folds.csv", coef_path = o.log_dir + "/ridge_coefs.csv";
  FILE* fl = std::fopen(folds_path.c_str(), "wb");
  FILE* fc = std::fopen(coef_path.c_str(), "wb");
  if (!fl || !fc) die("cannot write fold logs to " + o.log_dir);
  std::fprintf(fl, "test_year,train_rows,val_rows,test_rows,train_last_date,ridge_alpha,ridge_val_ic,gbdt_trees,gbdt_val_ic,mlp_epochs,mlp_val_ic,seconds\n");
  std::fprintf(fc, "test_year");
  for (const auto& n : P.feature_names) std::fprintf(fc, ",%s", n.c_str());
  std::fprintf(fc, "\n");
  for (size_t fi = 0; fi < folds.size(); ++fi) {
    const FoldResult& r = results[fi];
    std::string ep;
    for (size_t k = 0; k < r.mlp_epochs.size(); ++k) ep += (k ? "/" : "") + std::to_string(r.mlp_epochs[k]);
    std::fprintf(fl, "%d,%zu,%zu,%zu,%s,%g,%.5f,%zu,%.5f,%s,%.5f,%.2f\n", folds[fi].year, r.n_train, r.n_val, r.n_test,
                 P.dates[size_t(folds[fi].train_end - 1)].c_str(), r.ridge_alpha, r.ridge_val, r.gbdt_trees, r.gbdt_val,
                 ep.c_str(), r.mlp_val, r.seconds);
    std::fprintf(fc, "%d", folds[fi].year);
    for (double w : r.ridge_w) std::fprintf(fc, ",%.5f", w);
    std::fprintf(fc, "\n");
  }
  std::fclose(fl);
  std::fclose(fc);

  // Step 6 (monitoring): how stable is what the linear model learned?
  std::printf("\nRidge coefficients by training year (feature ranks -> return rank; + means 'higher is better'):\n%-9s", "test yr");
  for (const auto& n : P.feature_names) std::printf(" %8s", n.substr(0, 8).c_str());
  std::printf("\n");
  for (size_t fi = 0; fi < folds.size(); ++fi) {
    std::printf("%-9d", folds[fi].year);
    for (double w : results[fi].ridge_w) std::printf(" %+8.4f", w);
    std::printf("\n");
  }
  std::printf("\nWrote %s, %s, %s (%.1fs total)\n", o.out.c_str(), folds_path.c_str(), coef_path.c_str(), total.seconds());
  return 0;
}
