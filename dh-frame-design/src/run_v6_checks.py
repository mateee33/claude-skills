"""V6 model checks: hot-spot index versus mesh size for both carbon parts, and linear buckling multipliers.

Writes results/V6/mesh_and_buckling.json. Run a single job with `python3 src/run_v6_checks.py ft 4.5` etc.; with no
argument every job runs in turn (slow)."""
from __future__ import annotations
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import designs, run_structure as RSt, swingarm_fe as SW, frame_fe as FE
from shellfe import buckling
from cases import CASES, ULT, interface_loads
from geometry import frame_geometry
from kinematics import Linkage

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "V6", "mesh_and_buckling.json")


def load():
    return json.load(open(OUT)) if os.path.exists(OUT) else dict(
        note="V6 hot-spot index at ultimate load (patch average) versus mesh size, and the lowest linear buckling load multipliers. "
             "Shell meshes on the laminate mid-plane.", front_triangle={}, swingarm={}, buckling_multiplier_on_ultimate={})


def save(rec):
    json.dump(rec, open(OUT, "w"), indent=1)


def ft(h):
    st, m = RSt.solve_cases(designs.v6(), h, verbose=False)
    return dict(nodes=st["nodes"], laminate_kg=st["mass_total"], **{k: round(c["governing"]["fi"], 3) for k, c in st["cases"].items()}), m


def sa(h):
    so, m = SW.run(designs.v6(), h, verbose=False)
    return dict(nodes=so["nodes"], laminate_kg=so["mass_total"], lateral_stiffness_N_per_mm=round(so["lateral_stiffness_N_per_mm"]),
                **{k: round(c["governing"]["fi"], 3) for k, c in so["cases"].items()}), m


def buckle_ft(h=6.0, keys=("LC2b", "LC2c", "LC2d", "LC3")):
    d = designs.v6(); g = frame_geometry(d); d["pts"]["A"] = tuple(float(v) for v in g["rear_axle"])
    sw = Linkage(d["pts"], d["shock_stroke"]).sweep(n=401)
    m = FE.build_model(d, g, h)
    out = {}
    for c in CASES:
        if c["key"] in keys:
            L, _, _ = interface_loads(d, g, sw, c)
            u, _, _ = m.solve(L)
            out[c["key"]] = round(float(buckling(m, u, 4)[0]) / ULT, 2)
    return out


def buckle_sa(h=4.0, keys=("LC2b", "LC3")):
    d = designs.v6(); g = frame_geometry(d); d["pts"]["A"] = tuple(float(v) for v in g["rear_axle"])
    sw = Linkage(d["pts"], d["shock_stroke"]).sweep(n=401)
    m = SW.build(d, g, h)
    out = {}
    for c in CASES:
        if c["key"] in keys:
            L, _ = SW.case_loads(d, g, sw, c)
            for tag, mir in ((c["key"], 1.0),) + (((c["key"] + "m", -1.0),) if c["key"] == "LC3" else ()):
                Lm = {k: np.asarray(v, float) * (np.array([1, 1, -1, -1, -1, 1.0]) if mir < 0 else 1.0) for k, v in L.items()}
                u, _, _ = m.solve(Lm)
                out[tag] = round(float(buckling(m, u, 4)[0]) / ULT, 2)
    return out


if __name__ == "__main__":
    jobs = [tuple(sys.argv[1:])] if len(sys.argv) > 1 else [("ft", "7.0"), ("ft", "6.0"), ("ft", "4.5"), ("sa", "5.0"), ("sa", "4.0"), ("sa", "3.3"),
                                                              ("buckle_ft",), ("buckle_sa",)]
    for job in jobs:
        t0 = time.time()
        if job[0] == "ft":
            res = ft(float(job[1]))[0]; rec = load(); rec["front_triangle"]["h=%s" % job[1]] = res
        elif job[0] == "sa":
            res = sa(float(job[1]))[0]; rec = load(); rec["swingarm"]["h=%s" % job[1]] = res
        elif job[0] == "buckle_ft":
            res = buckle_ft(); rec = load(); rec["buckling_multiplier_on_ultimate"]["front_triangle (h=6)"] = res
        else:
            res = buckle_sa(); rec = load(); rec["buckling_multiplier_on_ultimate"]["swingarm (h=4)"] = res
        save(rec)
        print(job, res, "%.0fs" % (time.time() - t0), flush=True)
