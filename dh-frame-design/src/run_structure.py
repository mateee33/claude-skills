"""Front-triangle structural analysis for one revision: load cases, strain checks, balance and mesh checks."""
from __future__ import annotations
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from geometry import frame_geometry
from kinematics import Linkage
import frame_fe as FE
import laminate as lam
from cases import CASES, ULT, interface_loads

PATCH_R = 12.0   # mm, radius of the averaging patch used for hot-spot strain values (about 3-4 laminate thicknesses)


def solve_cases(d, h=6.5, layups=None, verbose=True, cases=CASES):
    layups = layups or d.get("layups")
    g = frame_geometry(d); d["pts"]["A"] = tuple(float(v) for v in g["rear_axle"])
    sw = Linkage(d["pts"], d["shock_stroke"]).sweep(n=401)
    t0 = time.time()
    m = FE.build_model(d, g, h, layups)
    # elements touching an interface ring or within 12 mm of it are excluded from the strain maxima
    slaves = np.concatenate([mm["slaves"] for mm in m.masters.values()])
    from scipy.spatial import cKDTree
    tree = cKDTree(m.V[slaves])
    cen = m.V[m.F].mean(1)
    dist, _ = tree.query(cen)
    valid = dist > 12.0
    area = 0.5 * np.linalg.norm(np.cross(m.V[m.F[:, 1]] - m.V[m.F[:, 0]], m.V[m.F[:, 2]] - m.V[m.F[:, 0]]), axis=1)
    out = dict(h=h, nodes=len(m.V), elements=len(m.F), build_s=time.time() - t0, cases={})
    for c in cases:
        L, expect, info = interface_loads(d, g, sw, c)
        u, reac, ur = m.solve(L)
        Rbb = m.reaction_at(reac, "BB")
        applied = np.zeros(6)
        for name, vec in L.items():
            x = m.masters[name]["x"]
            applied[:3] += vec[:3]; applied[3:] += vec[3:] + np.cross(x, vec[:3])
        fi, mode, e0, kp = FE.evaluate(m, u)
        fi_u = fi * ULT
        zres = {}
        for z in m.zone_names:
            sel = (m.zone == z) & valid
            if sel.any():
                i = np.where(sel)[0][np.argmax(fi_u[sel])]
                # hot-spot value: area-weighted mean over the elements of this zone within PATCH_R of the peak element
                near = sel & (np.linalg.norm(cen - cen[i], axis=1) < PATCH_R)
                patch = float(np.sum(fi_u[near] * area[near]) / np.sum(area[near]))
                zres[z] = dict(fi=patch, ms=float(1 / patch - 1), peak_element=float(fi_u[i]), mode=lam.MODE_NAMES[mode[i]],
                               at=[float(v) for v in cen[i]], p95=float(np.percentile(fi_u[sel], 95)))
        gov = max(zres.items(), key=lambda kv: kv[1]["fi"])
        out["cases"][c["key"]] = dict(name=c["name"], interface={k: [float(x) for x in v] for k, v in L.items()},
                                      info={k: (float(v) if np.isscalar(v) else [float(x) for x in v]) for k, v in info.items()},
                                      bb_reaction=[float(x) for x in Rbb], bb_expected=[float(x) for x in expect],
                                      fe_balance_residual=[float(x) for x in (applied + Rbb)],
                                      statics_vs_fe=[float(x) for x in (Rbb - expect)],
                                      zones=zres, governing=dict(zone=gov[0], **gov[1]),
                                      disp={k: [float(x) for x in m.master_disp(ur, k)] for k in m.masters},
                                      max_strain_ue=float(1e6 * np.abs(e0[valid]).max()))
        if verbose:
            r = out["cases"][c["key"]]
            print(f"{c['key']:5s} gov {gov[0]:11s} FI_ult {gov[1]['fi']:.2f} MS {gov[1]['ms']:+.2f} ({gov[1]['mode']}) at ({gov[1]['at'][0]:.0f},{gov[1]['at'][1]:.0f},{gov[1]['at'][2]:.0f})"
                  f" | shock {info['shock']/1e3:.1f} kN link {info['link']/1e3:.1f} pivot {r['info']['pivot']/1e3:.1f} rocker {r['info']['rocker']/1e3:.1f} HTu {info['ht_upper']/1e3:.1f} HTl {info['ht_lower']/1e3:.1f}"
                  f" | statics-FE |dF| {np.linalg.norm(r['statics_vs_fe'][:3]):.2e} N |dM| {np.linalg.norm(r['statics_vs_fe'][3:]):.2e} Nmm")
    out["mass"] = FE.mass_of(m)
    out["mass_total"] = float(sum(v["mass_kg"] for v in out["mass"].values()))
    return out, m


if __name__ == "__main__":
    import designs
    name = sys.argv[1] if len(sys.argv) > 1 else "v2"
    h = float(sys.argv[2]) if len(sys.argv) > 2 else 6.5
    d = getattr(designs, name)()
    out, m = solve_cases(d, h)
    od = os.path.join(os.path.dirname(__file__), "..", "results", d["name"]); os.makedirs(od, exist_ok=True)
    json.dump(out, open(os.path.join(od, "structure_h%.1f.json" % h), "w"), indent=1, default=float)
    print("nodes", out["nodes"], "elements", out["elements"], "laminate mass %.3f kg" % out["mass_total"])
    for z, v in out["mass"].items():
        print("  %-12s area %.4f m2  t %.2f mm  %.3f kg" % (z, v["area_mm2"] / 1e6, v["thickness"], v["mass_kg"]))
