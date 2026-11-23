# Custom carbon downhill frame study

A design study for a carbon downhill/freeride frame for one rider (185 cm, 68 kg in riding kit, Red Bull Rampage terrain),
benchmarked against the Canyon Sender CFR and the Commencal Supreme DH V5.

**This is a paper design with numerical analysis. Nothing has been built or tested. It is not ready to ride.**

Start here:

1. [`REPORT.md`](REPORT.md) — the design, the analysis record, the revision log and the scorecard.
2. [`01_rider_benchmarks_criteria.md`](01_rider_benchmarks_criteria.md) — rider inputs, benchmark configurations and the comparison rules, fixed before design.
3. [`cad/`](cad/) — hard-point coordinate table, DXF side view, STL of the analysed surfaces.
4. [`sources/`](sources/) — every manufacturer chart, manual, standard and data sheet used, with URLs.
5. [`results/`](results/) — numbers behind every table (`summary.json`), per-revision outputs, figures.

Reproduce (Python 3.13; `pip install numpy scipy matplotlib pyfe3d composites scikit-image gpytoolbox ezdxf`):

```
python3 src/run_all.py        # all five revisions: suspension, shell models, joints, mass  (about 2 minutes)
python3 src/make_figures.py   # figures and CAD exports
python3 src/make_report.py    # regenerates the report tables from results/summary.json
```

This folder is unrelated to the skills library it sits in. Its Python files are analysis scripts, not skill tools,
so the repository's counter check (`scripts/derive_counters.py --check`) will count them if this branch is ever merged.
