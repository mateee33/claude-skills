"""Run every revision through suspension, structure, swingarm, joint checks and mass; write results/summary.json."""
from __future__ import annotations
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import designs, run_suspension as RSu, run_structure as RSt, swingarm_fe as SW, local_checks as LC
import benchmarks as B, loads as Ld
from cases import CASES, ULT

ROOT = os.path.join(os.path.dirname(__file__), "..", "results")


def main(h_ft=6.0, h_sw=4.0):
    summary = dict(revisions={}, mesh=dict(front_triangle_h=h_ft, swingarm_h=h_sw))
    for name in designs.REVISIONS:
        t0 = time.time()
        d = getattr(designs, name)()
        od = os.path.join(ROOT, d["name"]); os.makedirs(od, exist_ok=True)
        res, g, sw = RSu.run(d, od)
        st, m = RSt.solve_cases(getattr(designs, name)(), h_ft, verbose=False)
        json.dump(st, open(os.path.join(od, "structure_h%.1f.json" % h_ft), "w"), indent=1, default=float)
        np.savez(os.path.join(od, "_front_triangle_mesh.npz"), V=m.V, F=m.F, zone=np.array(m.zone, dtype=str))
        so, ms = SW.run(getattr(designs, name)(), h_sw, verbose=False)
        json.dump(so, open(os.path.join(od, "swingarm_h%.1f.json" % h_sw), "w"), indent=1, default=float)
        np.savez(os.path.join(od, "_swingarm_mesh.npz"), V=ms.V, F=ms.F, zone=np.array(ms.zone, dtype=str))
        mx = LC.interface_maxima(st, so)
        if d.get("rev6"):
            cad = json.load(open(os.path.join(od, "clearance_3d.json")))["info"]["masses_kg"]
            rows = LC.checks_v6(mx, getattr(designs, name)())
            items, total = LC.mass_budget_v6(st["mass_total"], so["mass_total"], cad)
        else:
            rows = LC.checks(mx, d.get("shock_mount", "bonded"))
            items, total = LC.mass_budget(st["mass_total"], so["mass_total"], d.get("shock_mount", "bonded"))
        ft = {k: c["governing"] for k, c in st["cases"].items()}
        sa = {k: c["governing"] for k, c in so["cases"].items()}
        worst_ft = max(ft.items(), key=lambda kv: kv[1]["fi"]); worst_sa = max(sa.items(), key=lambda kv: kv[1]["fi"])
        worst_joint = min(r["margin"] for r in rows if "comparison" not in r["item"])
        summary["revisions"][d["name"]] = dict(
            suspension=dict(lr_start=res["linkage"]["lr_start"], lr_end=res["linkage"]["lr_end"], progression=res["linkage"]["progression"],
                            travel=res["geometry"]["rear_travel"], setup=res["setup"], g1={k: bool(v) for k, v in res["g1"].items()},
                            kin=res["kinematics_at_sag"], clearances=res["clearances"], w_rear=res["rear_static_load_N"]),
            geometry=res["geometry"], hard_points=res["hard_points"],
            front_triangle={k: dict(zone=v["zone"], fi=v["fi"], ms=v["ms"], mode=v["mode"], at=v["at"]) for k, v in ft.items()},
            swingarm={k: dict(zone=v["zone"], fi=v["fi"], mode=v["mode"], at=v["at"]) for k, v in sa.items()},
            worst=dict(front_triangle=dict(case=worst_ft[0], **{k: worst_ft[1][k] for k in ("zone", "fi", "mode")}),
                       swingarm=dict(case=worst_sa[0], **{k: worst_sa[1][k] for k in ("zone", "fi", "mode")}), joint_margin=worst_joint),
            structure_pass=bool(worst_ft[1]["fi"] <= 1.0 and worst_sa[1]["fi"] <= 1.0 and worst_joint >= 0.0),
            interface_limit_forces=mx, joints=rows, mass_items=[(a, b, c) for a, b, c in items], frame_mass=total,
            laminate_mass=dict(front_triangle=st["mass_total"], swingarm=so["mass_total"], ft_zones=st["mass"], sa_zones=so["mass"]),
            swingarm_lateral_stiffness=so["lateral_stiffness_N_per_mm"],
            ht_lateral_deflection_LC3=st["cases"]["LC3"]["disp"]["HTL"][2],
            case_forces={k: dict(rear=c["info"]["f_rear"], front=c["info"]["f_front"], hands=c["info"]["f_hands"], bb=c["bb_reaction"],
                                 shock=c["info"]["shock"], link=c["info"]["link"], pivot=c["info"]["pivot"], rocker=c["info"]["rocker"],
                                 ht_upper=c["info"]["ht_upper"], ht_lower=c["info"]["ht_lower"],
                                 balance=float(np.linalg.norm(c["statics_vs_fe"][:3]))) for k, c in st["cases"].items()})
        r = summary["revisions"][d["name"]]
        print(f"{d['name']}: G1 {r['suspension']['g1']} | FT worst {worst_ft[0]} {worst_ft[1]['zone']} {worst_ft[1]['fi']:.2f} | SA worst {worst_sa[0]} {worst_sa[1]['fi']:.2f}"
              f" | joints min margin {worst_joint:+.2f} | mass {total:.2f} kg | pass {r['structure_pass']} | {time.time()-t0:.0f}s")
    # benchmarks: G1 (estimated curves) and G3 (geometry)
    bm = RSu.benchmark_g1()
    summary["benchmarks_g1"] = {k: {kk: (vv if not isinstance(vv, np.ndarray) else None) for kk, vv in v.items() if kk not in ("z", "f")} for k, v in bm.items()}
    d = getattr(designs, designs.FINAL)(); from geometry import frame_geometry; g = frame_geometry(d)
    summary["g3"] = dict(custom=Ld.g3_metric(d["head_angle"], d["fork_axle_to_crown"], d["fork_offset"], g["head_tube_len"]),
                         sender=Ld.g3_metric(B.SENDER["head_angle"], B.SENDER["fork_a2c"], B.SENDER["fork_offset"], B.SENDER["head_tube"]),
                         supreme=Ld.g3_metric(B.SUPREME["head_angle"], B.SUPREME["fork_a2c"], B.SUPREME["fork_offset"], B.SUPREME["head_tube"]),
                         supreme_612=Ld.g3_metric(B.SUPREME["head_angle"], 612.0, B.SUPREME["fork_offset"], B.SUPREME["head_tube"]))
    json.dump(summary, open(os.path.join(ROOT, "summary.json"), "w"), indent=1, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else (bool(o) if isinstance(o, np.bool_) else str(o)))
    return summary


if __name__ == "__main__":
    s = main()
    print("G3", {k: (round(v["moment_Nm"]), round(v["upper_bearing_kN"], 2)) for k, v in s["g3"].items()})
