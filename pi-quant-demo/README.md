# pi-quant-demo

A small, complete version of how a quantitative fund tests a stock-prediction model, written in
**C++ and Rust** and sized to run on a **Raspberry Pi**. It downloads real US stock prices, builds
features, trains three models (ridge regression, gradient-boosted trees and a neural network),
tests them walk-forward year by year, turns the forecasts into a long/short portfolio, charges
trading costs, and then checks whether the result beats pure luck.

No third-party libraries in either language. Everything — the CSV and JSON parsers, the neural
network, the tree booster, the backtester — is in this folder and readable.

> This is an educational demo, not a trading system and not investment advice. The results below
> include the parts that don't work, because that is most of what real quant research finds.

## Quick start on a Raspberry Pi

Needs a C++17 compiler and Rust 1.63 or newer; peak memory is about 100 MB, so any Pi from the 3
or Zero 2 W up should do. I verified 64-bit and 32-bit ARM builds under emulation, not on a physical
Pi — see "How I checked it".

```bash
# 1. Tools: a C++ compiler, make, curl, git, and Rust
sudo apt update
sudo apt install -y build-essential curl git cargo   # Bookworm's packaged Rust (1.63) is new enough

# 2. Get this folder (sparse checkout: only pi-quant-demo/, not the whole repository)
git clone --depth 1 --filter=blob:none --sparse --branch <branch> <repository-url> repo
cd repo && git sparse-checkout set pi-quant-demo && cd pi-quant-demo

# 3. Build, check the build, run on real data
make                 # builds bin/train (C++) and bin/fetch, synth, prep, backtest (Rust)
./run.sh verify      # offline self-test; should print PASS twice
./run.sh real        # ~3 minutes downloading from Yahoo Finance, then trains and reports
```

The report is printed and saved to `data/real/results/report.txt`.

On a Pi 3 or Zero 2 W, use lighter models: `TRAIN_ARGS="--quick" ./run.sh real`.

## The six steps, and where each one lives

| Step | What happens | Code |
|---|---|---|
| 1. Define the target | Predict each stock's return over the next 5 trading days *relative to the other stocks*. The signal is computed at the close of day t; the trade happens at the close of day t+1 (never the same close); the stock is held to the close of t+6. | `rust/src/bin/prep.rs` |
| 2. Build features | 12 features from prices and volumes only: 1-day, 5-day and 1-month returns, 12-month momentum, 21/63-day volatility, abnormal volume, distance from the 52-week high, intraday range, where the close sits in the day's range (WorldQuant's published alpha #101), Amihud illiquidity, dollar volume. Each week every feature is converted to a cross-sectional rank. | `rust/src/bin/prep.rs` |
| 3. Train models | Ridge regression, gradient-boosted trees, a 2-layer neural network averaged over 3 seeds, and an ensemble of the three. A no-learning baseline (short-term reversal: bet against last week's move) for comparison. | `cpp/src/ridge.hpp`, `gbdt.hpp`, `mlp.hpp` |
| 4. Test honestly | Walk-forward by calendar year: train on everything before year Y-1, tune on year Y-1, predict year Y with the models frozen, then roll forward. A purge gap drops training weeks whose holding periods overlap the next block, so no future returns leak in. | `cpp/src/train.cpp` |
| 5. Turn forecasts into trades | Each week, within each sector: buy the top 20%, short the bottom 20%, size by inverse volatility, $1 long and $1 short per $1 of capital. Charge 5 bps per dollar traded and 0.5%/yr to borrow the shorts. | `rust/src/bin/backtest.rs` |
| 6. Retrain and monitor | Models are retrained from scratch every year. The report shows results year by year, and `ridge_coefs.csv` shows how the learned weights drift. | `train.cpp`, `backtest.rs` |

Plus one step real research needs and most demos skip: a **luck check**. The backtest re-runs the
exact same portfolio rules on 200 sets of *random* forecasts, so every model is compared with
what zero skill looks like on the same data.

```
Yahoo ──fetch──▶ data/real/raw/*.csv ──prep──▶ panel.csv ──train──▶ predictions.csv ──backtest──▶ results/
         (Rust)                         (Rust)              (C++)                       (Rust)
```

C++ runs the numeric engine and Rust handles parsing, network data, and accounting. That split is
a choice for this demo. It is not a claim about how any particular fund organises its code.

## Two self-tests: a market with an answer, and one without

`./run.sh synth` generates two fake markets from the **same random numbers**:

* **planted** — weak patterns are hidden in the returns: short-term reversal, which is much weaker
  after heavy volume (a non-linear interaction), and a small drift for stocks near their 52-week
  high. `truth.txt` documents them and estimates a ceiling: the best weekly IC (about 0.048)
  possible with perfect knowledge of the hidden formulas.
* **null** — identical noise, no patterns. Any "edge" found here is the pipeline fooling itself.

My results (`./run.sh verify` compares yours against these, digit for digit):

| | IC mean | IC t-stat | net return/yr | net Sharpe | beats random |
|---|---|---|---|---|---|
| planted: ridge | 0.0353 | 10.43 | +16.4% | 1.62 | 100% |
| planted: neural net | 0.0357 | 10.57 | +14.2% | 1.36 | 100% |
| planted: ensemble | 0.0359 | 10.60 | +15.3% | 1.48 | 100% |
| **null: ensemble** | **0.0026** | **0.78** | **−8.3%** | **−0.81** | **23.5%** |
| null: neural net | 0.0028 | 0.87 | −5.4% | −0.52 | 80.5% |

The pipeline finds most of what was planted (IC 0.036 against a ceiling of about 0.048). It finds
nothing where nothing exists, and it loses money there through trading costs, which is what should
happen.

## Results on real data

120 large US stocks (`universe.csv`), out-of-sample weekly from January 2005 to November 2026,
data downloaded on 2026-11-13. Your numbers will differ slightly because you will download more
recent data.

| model | IC mean | IC t | gross/yr | net/yr | net Sharpe | max drawdown | break-even cost |
|---|---|---|---|---|---|---|---|
| reversal (no learning) | 0.0121 | 2.01 | 6.5% | −2.2% | −0.20 | 72.5% | 4.0 bps |
| ridge | 0.0205 | 3.98 | 9.9% | 3.0% | 0.32 | 28.9% | 7.8 bps |
| gradient-boosted trees | 0.0186 | 3.99 | 7.1% | 0.3% | 0.03 | 42.9% | 5.6 bps |
| neural net | 0.0171 | 3.37 | 7.8% | 1.0% | 0.12 | 42.2% | 6.2 bps |
| ensemble | 0.0199 | 3.92 | 9.4% | 2.7% | 0.30 | 26.8% | 7.5 bps |
| 200 random forecasts (median) | −0.0003 | −0.11 | −0.3% | −9.1% | −1.42 | | |

What this says:

1. **There is a real but tiny signal.** IC is about 0.02, which is near the coin-flip end even by
   industry standards. Its t-statistic is about 4, and every learned model beat all 200 random
   portfolios before costs. The ridge weights point the same way as well-known effects (short-term
   reversal, 12-month momentum, an illiquidity premium); the 52-week-high feature gets the
   opposite sign to the published effect here.
2. **Trading costs take most of it.** The portfolio turns over about 250% of capital every week.
   The ensemble's 9.4% gross becomes 2.7% net. At 10 bps per dollar traded every model loses money
   (see the cost table in the report).
3. **The edge faded.** Ensemble net return was +9.1%/yr (Sharpe 0.98) in 2005–2010 and +0.2%/yr
   (Sharpe 0.02) in 2011–2026, while IC fell from 0.035 to 0.014. I chose that split *after* seeing
   the chart, so treat it as a description, not a test.
4. **The neural network did not beat linear regression here.** The differences between the models
   (IC 0.017–0.021) are within noise; the standard error of each mean IC is about 0.005. Non-linear
   models need the non-linearity to be large relative to the noise and the data to be plentiful;
   120 stocks over 20 years is not much data for weekly returns.
5. **Even these numbers are flattering** (see the next section).

## What this demo gets wrong, on purpose or by necessity

* **Survivorship bias.** The universe is today's large companies, so none of them went bankrupt in
  the sample. Real tests use the members of the index *as of each past date*, which needs paid data.
* **Simple costs.** A flat cost per dollar traded, no market impact, no slippage on volatile days,
  and drift between rebalances is ignored when measuring turnover. 5 bps and 0.5%/yr borrow are
  assumptions; the report shows other cost levels.
* **Sector labels.** These are my assignment of each company's current GICS sector, applied to the
  whole history. Companies get reclassified, and a few labels may be off.
* **Multiple testing.** Five models are compared on the same data, so the best one looks better
  than it would in live trading. Choosing settings after seeing results makes this worse, which is
  why I left the defaults alone after seeing the real-data results (see below).
* **Free data.** Yahoo's endpoint is unofficial and can change or stop. It adjusts for splits and
  dividends but not for spin-offs, which show up as fake crashes. `prep` lists every one-day move
  above 30% so you can check them. For this universe the largest ones match known events (Apple's
  profit warning on 2000-09-29, AIG in September 2008, the oil crash of March 2020) and none looked
  like a spin-off artifact.
* **Tiny scale.** 120 stocks and 12 price features, against the thousands of stocks and many data
  sources real funds use.

## How I checked it

* **No look-ahead.** An independent script recomputed 400 random forward returns from the raw files
  (buy at close t+1, sell at close t+6) and checked the rank transforms: no mismatches. The null
  market shows no edge (IC t-stats 0.6–1.3).
* **The luck check behaves as theory says.** Random forecasts' IC t-stats span −1.7 to +2.0
  (5th–95th percentile), close to a standard normal. One aside worth knowing: an earlier single
  random "placebo" draw reached t = −2.9 by pure chance. That was one draw in seven seeds tried;
  the other six were between −0.65 and +0.87. One lucky backtest proves very little.
* **Settings were chosen on a separate synthetic market** (seed 1001), never on real data or the
  seed shown above. Tree settings I tried differed by less than the noise, so I kept the defaults.
* **ARM.** Cross-compiled for 64-bit (aarch64) and 32-bit (armv7) ARM and ran the whole synthetic
  pipeline under QEMU emulation. The outputs were byte-for-byte identical to x86, including the
  neural network and tree predictions. **I have not run it on a physical Raspberry Pi**, so I have
  no Pi timings. On a 4-core x86 cloud VM, the real-data run took about 20 s after the download.
* **Toolchains.** Builds with no warnings on GCC 12 and 13, clang 18, Rust 1.63 and 1.97.
* **Memory and threads.** C++ engine runs clean under AddressSanitizer, UBSan and ThreadSanitizer,
  and gives identical predictions with 1 or 4 threads.

Identical results across CPUs come from three choices: an addition-only random number generator
(same on both sides), no math-library calls in training, and `-ffp-contract=off`, which stops the
compiler fusing `a*b+c` on ARM but not on x86. If `./run.sh verify` shows tiny differences on your
Pi, a different C math library version is the likely cause; large differences mean a bug — please
report them.

## Useful options

Every program prints its options with `--help`. Pass options through `run.sh` with environment
variables:

```bash
TRAIN_ARGS="--quick" ./run.sh real                       # 1 network, 10 epochs, 120 trees
BACKTEST_ARGS="--cost-bps 10 --quantile 0.1" ./run.sh real
BACKTEST_ARGS="--no-sector-neutral" ./run.sh pipeline data/real universe.csv   # re-run without re-downloading
FETCH_ARGS="--start 2010-01-01" ./run.sh real
SEED=3 ./run.sh synth                                    # another synthetic market
```

Outputs per dataset (`data/<name>/`): `panel.csv` (features + targets), `predictions.csv`
(out-of-sample forecasts of every model), `folds.csv` (what each yearly fold trained on and chose),
`ridge_coefs.csv`, and `results/` (`report.txt`, `summary.csv`, `yearly.csv`, `periods.csv`,
`equity.csv`, `random_trials.csv`).

## Using your own data

Put one CSV per stock in `data/<name>/raw/TICKER.csv` with the header
`date,open,high,low,close,adj_close,volume` (dates `YYYY-MM-DD`, ascending, split-adjusted prices,
`adj_close` also dividend-adjusted), write a `ticker,sector` universe file, then:

```bash
./run.sh pipeline data/<name> my_universe.csv
```

## Cross-compiling from a PC (optional)

```bash
sudo apt install g++-aarch64-linux-gnu && rustup target add aarch64-unknown-linux-gnu
CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_LINKER=aarch64-linux-gnu-gcc \
  make CXX=aarch64-linux-gnu-g++ RUST_TARGET=aarch64-unknown-linux-gnu BIN_DIR=bin-aarch64
# copy bin-aarch64/ to the Pi as bin/, or test locally with QEMU:
RUNNER="qemu-aarch64 -L /usr/aarch64-linux-gnu" BIN=bin-aarch64 ./run.sh verify
```

For 32-bit Raspberry Pi OS use `arm-linux-gnueabihf-g++` and `armv7-unknown-linux-gnueabihf`.

## Layout

```
pi-quant-demo/
├── Makefile          builds both languages into bin/
├── run.sh            runs the stages: synth | real | verify | pipeline
├── universe.csv      the 120 stocks and their sectors
├── reference/        expected synthetic results used by ./run.sh verify
├── rust/src/         fetch, synth, prep, backtest + shared code (CSV, JSON, dates, RNG, stats)
└── cpp/src/          train: ridge, gradient-boosted trees, neural network, walk-forward folds
```

## References for the ideas used

* Short-term reversal: Jegadeesh (1990), *Evidence of Predictable Behavior of Security Returns*; Lehmann (1990), *Fads, Martingales, and Market Efficiency*.
* Momentum: Jegadeesh & Titman (1993), *Returns to Buying Winners and Selling Losers*.
* Illiquidity: Amihud (2002), *Illiquidity and Stock Returns*.
* 52-week high: George & Hwang (2004), *The 52-Week High and Momentum Investing*.
* Alpha #101: Kakushadze (2016), *101 Formulaic Alphas*.
* Machine learning for returns: Gu, Kelly & Xiu (2020), *Empirical Asset Pricing via Machine Learning*.
* Purging overlapping labels and backtest overfitting: López de Prado (2018), *Advances in Financial Machine Learning*.
* AdamW: Loshchilov & Hutter (2019), *Decoupled Weight Decay Regularization*.
