# pi-quant-demo — build the C++ model engine and the Rust pipeline tools into ./bin
#
#   make            build everything (needs g++ and cargo)
#   make test       Rust unit tests
#   make clean      remove build outputs (keeps downloaded data)
#
# Cross-compiling from a PC for a Pi (optional, see README):
#   make CXX=aarch64-linux-gnu-g++ RUST_TARGET=aarch64-unknown-linux-gnu BIN_DIR=bin-aarch64

CXX         ?= g++
# -ffp-contract=off stops the compiler fusing a*b+c into one instruction on ARM but not on x86,
# which keeps results identical across machines.
CXXFLAGS    ?= -std=c++17 -O3 -pthread -ffp-contract=off -Wall -Wextra
CARGO       ?= cargo
BIN_DIR     ?= bin
RUST_TARGET ?=

ifeq ($(RUST_TARGET),)
  RUST_OUT   := rust/target/release
  CARGO_ARGS :=
else
  RUST_OUT   := rust/target/$(RUST_TARGET)/release
  CARGO_ARGS := --target $(RUST_TARGET)
endif

RUST_BINS := fetch synth prep backtest
CPP_SRC   := cpp/src/train.cpp $(wildcard cpp/src/*.hpp)

.PHONY: all cpp rust test clean

all: cpp rust

cpp: $(BIN_DIR)/train

$(BIN_DIR)/train: $(CPP_SRC)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CXXFLAGS) -o $@ cpp/src/train.cpp

rust:
	cd rust && $(CARGO) build --release $(CARGO_ARGS)
	@mkdir -p $(BIN_DIR)
	@for b in $(RUST_BINS); do cp $(RUST_OUT)/$$b $(BIN_DIR)/; done
	@echo "Built: $(BIN_DIR)/train $(addprefix $(BIN_DIR)/,$(RUST_BINS))"

test:
	cd rust && $(CARGO) test --release

clean:
	rm -rf bin bin-* rust/target
