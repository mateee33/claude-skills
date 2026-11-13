// Loading the weekly feature panel written by the Rust `prep` stage.
#pragma once

#include <cmath>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include "common.hpp"

namespace pq {

constexpr int kBins = 32;  // histogram bins for the tree model

struct Panel {
  std::vector<std::string> feature_names;
  int F = 0;
  size_t n = 0;
  std::vector<float> X;        // n*F, row-major; each feature is a weekly rank in [-sqrt3, sqrt3]
  std::vector<uint8_t> bins;   // n*F, X quantised into kBins equal-width rank buckets
  std::vector<float> y;        // training target: weekly rank of the forward return
  std::vector<float> fwd;      // the forward return itself (passed through to the backtest)
  std::vector<float> vol;      // 63-day daily volatility (for position sizing in the backtest)
  std::vector<int> date_of_row;
  std::vector<std::string> dates;   // unique rebalance dates, ascending
  std::vector<int> year_of_date;
  std::vector<size_t> date_start;   // rows of date d are [date_start[d], date_start[d+1])
  std::vector<std::string> ticker, sector;
  int horizon = 5, lag = 1, step = 5;

  int find_feature(const std::string& name) const {
    for (int i = 0; i < F; ++i)
      if (feature_names[size_t(i)] == name) return i;
    return -1;
  }
};

inline float parse_float(const std::string& s, size_t line, const char* what) {
  char* end = nullptr;
  float v = std::strtof(s.c_str(), &end);
  if (end == s.c_str() || !std::isfinite(v))
    die("panel line " + std::to_string(line) + ": bad " + what + " '" + s + "'");
  return v;
}

inline Panel load_panel(const std::string& path) {
  Panel P;
  std::ifstream in(path, std::ios::binary);
  if (!in) die("cannot open " + path);
  std::stringstream buf;
  buf << in.rdbuf();
  const std::string text = buf.str();

  // Settings written by prep (holding period etc.); defaults match prep's defaults.
  {
    std::ifstream meta(path + ".meta");
    std::string line;
    while (std::getline(meta, line)) {
      auto kv = split(trim(line), '=');
      if (kv.size() != 2) continue;
      if (kv[0] == "horizon") P.horizon = std::atoi(kv[1].c_str());
      if (kv[0] == "lag") P.lag = std::atoi(kv[1].c_str());
      if (kv[0] == "step") P.step = std::atoi(kv[1].c_str());
    }
    if (P.horizon <= 0 || P.lag <= 0 || P.step <= 0) die("bad horizon/lag/step in " + path + ".meta");
  }

  size_t pos = 0, line_no = 0;
  auto next_line = [&](std::string& out) -> bool {
    while (pos < text.size()) {
      size_t e = text.find('\n', pos);
      if (e == std::string::npos) e = text.size();
      out.assign(text, pos, e - pos);
      pos = e + 1;
      ++line_no;
      if (!out.empty() && out.back() == '\r') out.pop_back();
      if (!out.empty() && out[0] != '#') return true;
    }
    return false;
  };

  std::string line;
  if (!next_line(line)) die(path + " is empty");
  auto header = split(line, ',');
  auto idx = [&](const std::string& name) -> size_t {
    for (size_t i = 0; i < header.size(); ++i)
      if (trim(header[i]) == name) return i;
    die(path + ": missing column '" + name + "'");
  };
  const size_t c_date = idx("date"), c_ticker = idx("ticker"), c_sector = idx("sector");
  const size_t c_vol = idx("vol"), c_fwd = idx("fwd_ret"), c_target = idx("target");
  if (!(c_sector < c_vol)) die(path + ": expected feature columns between 'sector' and 'vol'");
  for (size_t i = c_sector + 1; i < c_vol; ++i) P.feature_names.push_back(trim(header[i]));
  P.F = int(P.feature_names.size());
  if (P.F == 0) die(path + ": no feature columns");

  std::vector<float> feats(size_t(P.F));
  while (next_line(line)) {
    auto f = split(line, ',');
    if (f.size() != header.size())
      die("panel line " + std::to_string(line_no) + ": expected " + std::to_string(header.size()) + " fields");
    const std::string& d = f[c_date];
    if (P.dates.empty() || P.dates.back() != d) {
      if (!P.dates.empty() && d < P.dates.back()) die("panel must be sorted by date (line " + std::to_string(line_no) + ")");
      P.dates.push_back(d);
      P.year_of_date.push_back(std::atoi(d.substr(0, 4).c_str()));
      P.date_start.push_back(P.n);
    }
    for (int k = 0; k < P.F; ++k) feats[size_t(k)] = parse_float(f[c_sector + 1 + size_t(k)], line_no, "feature");
    P.X.insert(P.X.end(), feats.begin(), feats.end());
    P.y.push_back(parse_float(f[c_target], line_no, "target"));
    P.fwd.push_back(parse_float(f[c_fwd], line_no, "fwd_ret"));
    P.vol.push_back(parse_float(f[c_vol], line_no, "vol"));
    P.date_of_row.push_back(int(P.dates.size()) - 1);
    P.ticker.push_back(f[c_ticker]);
    P.sector.push_back(f[c_sector]);
    ++P.n;
  }
  P.date_start.push_back(P.n);
  if (P.n == 0) die(path + " has no data rows");

  // Ranks map to [-sqrt3, sqrt3]; equal-width buckets on that scale are equal-frequency buckets.
  P.bins.resize(P.X.size());
  const double s12 = std::sqrt(12.0);
  for (size_t i = 0; i < P.X.size(); ++i) {
    int b = int((double(P.X[i]) / s12 + 0.5) * kBins);
    P.bins[i] = uint8_t(b < 0 ? 0 : (b >= kBins ? kBins - 1 : b));
  }
  return P;
}

// Mean over dates [d0, d1) of the cross-sectional correlation between `pred` and the rank
// target. `pred[i]` belongs to row date_start[d0] + i. This is the validation score.
inline double mean_ic(const Panel& P, int d0, int d1, const double* pred) {
  const size_t base = P.date_start[size_t(d0)];
  double sum = 0.0;
  int count = 0;
  for (int d = d0; d < d1; ++d) {
    const size_t a = P.date_start[size_t(d)], b = P.date_start[size_t(d) + 1];
    const size_t n = b - a;
    if (n < 3) continue;
    double mp = 0, my = 0;
    for (size_t r = a; r < b; ++r) {
      mp += pred[r - base];
      my += P.y[r];
    }
    mp /= double(n);
    my /= double(n);
    double sxy = 0, sxx = 0, syy = 0;
    for (size_t r = a; r < b; ++r) {
      const double u = pred[r - base] - mp, v = double(P.y[r]) - my;
      sxy += u * v;
      sxx += u * u;
      syy += v * v;
    }
    if (sxx > 0 && syy > 0) {
      sum += sxy / std::sqrt(sxx * syy);
      ++count;
    }
  }
  return count ? sum / count : 0.0;
}

}  // namespace pq
