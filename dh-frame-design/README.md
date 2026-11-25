# Custom carbon downhill frame study

A design study for a carbon downhill/freeride frame for one rider (185 cm, 68 kg in riding kit, Red Bull Rampage terrain),
benchmarked against the Canyon Sender CFR and the Commencal Supreme DH V5.

**This is a detailed design on paper, with numerical analysis. Nothing has been built or tested, and no qualified
composites engineer has reviewed it. It is not ready to ride.**

Start here:

1. [`DESIGN_V6.md`](DESIGN_V6.md) — the current revision: the frame as a 3-D assembly, what that changed, clearances, structure, open items.
2. [`REPORT.md`](REPORT.md) — the whole study from V1: rider and fit, benchmarks, suspension, loads, standards, revision log and scorecard.
   Its sections 3 to 5 describe V5, the last side-view revision.
3. [`01_rider_benchmarks_criteria.md`](01_rider_benchmarks_criteria.md) — rider inputs, benchmark configurations and the comparison rules, fixed before design.
4. [`cad/V6/`](cad/V6/) — STEP solids of every part, and of the assembly with fork, shock, wheels and drivetrain envelopes at top-out, sag and bottom-out.
   [`cad/`](cad/) also holds the hard-point tables and DXF side views.
5. [`mfg/`](mfg/) — ply book, laminate zones, bill of materials, interface and tolerance sheet, manufacturing notes.
6. [`sources/`](sources/) — every manufacturer chart, drawing, manual, standard and data sheet used, with URLs and what could not be found.
7. [`results/`](results/) — numbers behind every table (`summary.json`), per-revision outputs, figures.

Reproduce (Python 3.13; `pip install numpy scipy matplotlib pyfe3d composites scikit-image gpytoolbox ezdxf build123d`):

```
python3 src/run_v6_cad.py       # V6 solid model, STEP export, clearance study                (about 10 minutes)
python3 src/run_all.py          # all six revisions: suspension, shell models, joints, mass     (about 4 minutes)
python3 src/run_v6_checks.py    # V6 mesh-size and buckling checks                              (about 10 minutes)
python3 src/make_v6_package.py  # ply book, laminate zones, bill of materials
python3 src/make_figures.py     # figures and CAD exports
python3 src/make_v6_doc.py      # DESIGN_V6.md
python3 src/make_report.py      # REPORT.md from src/report_template.md and results/summary.json
```

`python3 src/run_v6_first_packaged.py` reproduces `results/V6/as_first_packaged.json`, the before/after of the analysis correction
described in `DESIGN_V6.md`, section 3 (about 5 minutes).

This folder is unrelated to the skills library it sits in. Its Python files are analysis scripts, not skill tools,
so the repository's counter check (`scripts/derive_counters.py --check`) will count them if this branch is ever merged.
