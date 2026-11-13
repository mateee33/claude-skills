#!/usr/bin/env bash
# Run the pipeline end to end.
#
#   ./run.sh synth        offline self-test on two synthetic markets (planted signal vs none)
#   ./run.sh real         download real US stock data (Yahoo, needs internet) and run on it
#   ./run.sh verify       run the synthetic tests and compare with the reference results
#   ./run.sh pipeline DIR [UNIVERSE]   re-run prep/train/backtest on DIR/raw
#
# Extra options can be passed to each stage through environment variables, e.g.
#   TRAIN_ARGS="--quick" ./run.sh real          # lighter models for a Pi 3 / Zero 2
#   BACKTEST_ARGS="--cost-bps 10" ./run.sh real # harsher trading costs
#
# Testing an ARM build on a PC (optional): RUNNER="qemu-aarch64 -L /usr/aarch64-linux-gnu" BIN=bin-aarch64 ./run.sh synth
set -euo pipefail
cd "$(dirname "$0")"
BIN=${BIN:-./bin}
RUNNER=${RUNNER:-}  # optional command prefix, e.g. an emulator

for b in fetch synth prep train backtest; do
  if [[ ! -x "$BIN/$b" ]]; then
    echo "missing $BIN/$b — run 'make' first" >&2
    exit 1
  fi
done

pipeline() {
  local dir=$1 universe=${2:-}
  echo
  echo "=== [prep] features and targets: $dir ==="
  $RUNNER "$BIN/prep" --raw "$dir/raw" --out "$dir/panel.csv" ${universe:+--universe "$universe"} ${PREP_ARGS:-}
  echo
  echo "=== [train] walk-forward models (C++) ==="
  $RUNNER "$BIN/train" --panel "$dir/panel.csv" --out "$dir/predictions.csv" ${TRAIN_ARGS:-}
  echo
  echo "=== [backtest] portfolio after costs (Rust) ==="
  $RUNNER "$BIN/backtest" --pred "$dir/predictions.csv" --out "$dir/results" ${BACKTEST_ARGS:-}
}

case "${1:-}" in
  synth)
    seed=${SEED:-7}
    echo "=== [synth] market WITH planted patterns (seed $seed) ==="
    $RUNNER "$BIN/synth" --out data/synth-planted/raw --signal 1 --seed "$seed" ${SYNTH_ARGS:-}
    pipeline data/synth-planted data/synth-planted/universe.csv
    echo
    echo "=== [synth] same random numbers, NO patterns (the null test) ==="
    $RUNNER "$BIN/synth" --out data/synth-null/raw --signal 0 --seed "$seed" ${SYNTH_ARGS:-}
    pipeline data/synth-null data/synth-null/universe.csv
    echo
    echo "Done. Compare data/synth-planted/results/report.txt with data/synth-null/results/report.txt"
    ;;
  real)
    echo "=== [fetch] daily bars from Yahoo Finance ==="
    $RUNNER "$BIN/fetch" --universe universe.csv --out data/real/raw ${FETCH_ARGS:-}
    pipeline data/real universe.csv
    echo
    echo "Done. Report: data/real/results/report.txt"
    ;;
  verify)
    "$0" synth > data-verify.log 2>&1 || { echo "synthetic run failed, see data-verify.log" >&2; exit 1; }
    ok=1
    for d in synth-planted synth-null; do
      if cmp -s "data/$d/results/summary.csv" "reference/$d.summary.csv"; then
        echo "PASS  $d: results identical to the reference run"
      else
        ok=0
        echo "DIFF  $d: results differ from the reference run:"
        diff "reference/$d.summary.csv" "data/$d/results/summary.csv" || true
      fi
    done
    if [[ $ok == 1 ]]; then
      echo "Your build reproduces the reference numbers exactly."
    else
      echo "Tiny differences can come from a different C math library version; large ones mean something is wrong."
    fi
    ;;
  pipeline)
    [[ -n "${2:-}" ]] || { echo "usage: $0 pipeline DIR [UNIVERSE]" >&2; exit 2; }
    pipeline "$2" "${3:-}"
    ;;
  *)
    sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
    ;;
esac
