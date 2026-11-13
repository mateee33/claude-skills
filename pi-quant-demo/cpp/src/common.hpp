// Shared utilities for the C++ model engine. C++17, standard library only.
#pragma once

#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

namespace pq {

// xoshiro256** seeded through splitmix64 (the same generator the Rust stages use).
class Rng {
 public:
  explicit Rng(uint64_t seed) {
    uint64_t x = seed;
    for (auto& v : s_) v = splitmix64(x);
  }
  uint64_t next() {
    const uint64_t result = rotl(s_[1] * 5, 7) * 9;
    const uint64_t t = s_[1] << 17;
    s_[2] ^= s_[0];
    s_[3] ^= s_[1];
    s_[1] ^= s_[2];
    s_[0] ^= s_[3];
    s_[2] ^= t;
    s_[3] = rotl(s_[3], 45);
    return result;
  }
  // Uniform on [0, 1) with 53 random bits.
  double uniform() { return double(next() >> 11) * (1.0 / 9007199254740992.0); }
  // Approximately N(0,1): sum of 12 uniforms minus 6. Additions only, so the same seed gives
  // the same numbers on x86 and ARM (std::normal_distribution differs between libraries).
  double normal() {
    double s = 0.0;
    for (int i = 0; i < 12; ++i) s += uniform();
    return s - 6.0;
  }
  // Integer in [0, n).
  size_t below(size_t n) {
    size_t k = size_t(uniform() * double(n));
    return k < n ? k : n - 1;
  }

  static uint64_t mix(uint64_t a, uint64_t b, uint64_t c) {
    uint64_t x = a ^ (b * 0x9E3779B97F4A7C15ULL) ^ (c * 0xD1B54A32D192ED03ULL);
    return splitmix64(x);
  }

 private:
  static uint64_t rotl(uint64_t x, int k) { return (x << k) | (x >> (64 - k)); }
  static uint64_t splitmix64(uint64_t& x) {
    x += 0x9E3779B97F4A7C15ULL;
    uint64_t z = x;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
  }
  uint64_t s_[4];
};

class Timer {
 public:
  Timer() : t0_(std::chrono::steady_clock::now()) {}
  double seconds() const {
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0_).count();
  }

 private:
  std::chrono::steady_clock::time_point t0_;
};

[[noreturn]] inline void die(const std::string& msg) {
  std::fprintf(stderr, "error: %s\n", msg.c_str());
  std::exit(1);
}

inline std::vector<std::string> split(const std::string& s, char sep) {
  std::vector<std::string> out;
  size_t start = 0;
  for (;;) {
    size_t p = s.find(sep, start);
    if (p == std::string::npos) {
      out.push_back(s.substr(start));
      return out;
    }
    out.push_back(s.substr(start, p - start));
    start = p + 1;
  }
}

inline std::string trim(const std::string& s) {
  size_t a = 0, b = s.size();
  while (a < b && (s[a] == ' ' || s[a] == '\t' || s[a] == '\r' || s[a] == '\n')) ++a;
  while (b > a && (s[b - 1] == ' ' || s[b - 1] == '\t' || s[b - 1] == '\r' || s[b - 1] == '\n')) --b;
  return s.substr(a, b - a);
}

}  // namespace pq
