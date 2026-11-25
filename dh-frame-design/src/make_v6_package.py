"""Manufacturing data for V6: ply book, zone areas, bill of materials. Numbers come from the models, not from hand entry."""
from __future__ import annotations
import os, sys, json, csv
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import designs, laminate as lam, frame_fe as FE, swingarm_fe as SW
from geometry import frame_geometry

ROOT = os.path.join(os.path.dirname(__file__), "..")
MFG = os.path.join(ROOT, "mfg"); os.makedirs(MFG, exist_ok=True)
MAT = dict(U="Toray T700G/2510 UD tape, 150 g/m2, 0.152 mm cured", F="Toray T700S-12K/2510 plain weave, 190 g/m2, 0.218 mm cured")
ZONE_DESC = dict(
    down_tube="Down tube, between the head-tube junction and the BB core", top_tube="Top tube, between the head-tube junction and the seat-mast junction",
    seat_mast="Seat mast, between the rocker boss and the BB core", head_tube="Head tube barrel",
    ht_junction="Top- and down-tube walls within 140 mm of the steering axis", core="Seat-mast / top-tube junction and lower mast",
    boss="BB shell, main-pivot boss, rocker boss, shock-fitting seat (local build-up)",
    mast_pad="Seat-mast walls within 44 mm of the rocker pivot (pad around the rocker boss)",
    spar="Swingarm lower and upper spars and upright", knee="Lower spar and strut within 50 mm of the yoke junction",
    node="Pivot eyes, link lugs, dropouts", strut="Yoke-to-eye struts", yoke="Full-width yoke box", web="(not used in V6)")


def zone_areas(m, layups):
    V, F = m.V, m.F
    area = 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    return {z: float(area[m.zone == z].sum()) for z in layups}


def bom(ft_kg, sa_kg):
    import bom as B
    cl = json.load(open(os.path.join(ROOT, "results", "V6", "clearance_3d.json")))["info"]["masses_kg"]
    rows = B.rows(ft_kg, sa_kg, cl)
    csv.writer(open(os.path.join(MFG, "BOM_V6.csv"), "w", newline="")).writerows(rows)
    print("BOM items", len(rows) - 2, "| frame mass per the G2 definition %.3f kg" % B.frame_mass_items(ft_kg, sa_kg, cl)[1])


def main():
    d = designs.v6(); g = frame_geometry(d); d["pts"]["A"] = tuple(float(v) for v in g["rear_axle"])
    mf = FE.build_model(d, g, 6.0)
    ms = SW.build(d, g, 4.0)
    parts = [("FT-001 front triangle", mf.layups, zone_areas(mf, mf.layups)), ("SA-001 swingarm", ms.layups, zone_areas(ms, ms.layups))]
    rows = [["part", "zone", "zone description", "ply no. (1 = bladder side)", "material", "orientation (deg, 0 = along the member axis; fabric laid at +/-45)",
             "cured ply thickness mm", "cumulative thickness mm"]]
    summary = [["part", "zone", "plies", "thickness mm", "surface area cm2", "laminate mass g", "UD plies at 0", "UD plies at +/-45", "UD plies at 90", "fabric plies"]]
    totals = {}
    for pname, layups, areas in parts:
        for z, stack in layups.items():
            if areas.get(z, 0) <= 0:
                continue
            t = 0.0
            for i, (mk, ang) in enumerate(stack, 1):
                t += lam.MATS[mk]["t"]
                rows.append([pname, z, ZONE_DESC.get(z, ""), i, MAT[mk], "+/-45" if mk == "F" else f"{ang:+.0f}", f"{lam.MATS[mk]['t']:.3f}", f"{t:.3f}"])
            mass = areas[z] * lam.areal_mass(stack) * 1000
            n0 = sum(1 for mk, a in stack if mk == "U" and a == 0); n45 = sum(1 for mk, a in stack if mk == "U" and abs(a) == 45)
            n90 = sum(1 for mk, a in stack if mk == "U" and a == 90); nf = sum(1 for mk, a in stack if mk == "F")
            summary.append([pname, z, len(stack), f"{lam.thickness(stack):.2f}", f"{areas[z]/100:.0f}", f"{mass:.0f}", n0, n45, n90, nf])
            totals[pname] = totals.get(pname, 0.0) + mass
    csv.writer(open(os.path.join(MFG, "ply_book_V6.csv"), "w", newline="")).writerows(rows)
    csv.writer(open(os.path.join(MFG, "laminate_zones_V6.csv"), "w", newline="")).writerows(summary)
    bom(totals["FT-001 front triangle"] / 1000, totals["SA-001 swingarm"] / 1000)
    print("ply book rows", len(rows) - 1, "| laminate mass g", {k: round(v) for k, v in totals.items()})
    for r in summary:
        print("  ", r)


if __name__ == "__main__":
    main()
