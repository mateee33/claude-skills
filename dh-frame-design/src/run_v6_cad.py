"""Build the V6 solid assembly, export STEP, run the 3-D clearance study and render views."""
from __future__ import annotations
import os, sys, json, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from build123d import Compound, export_step, Color
import designs, cad_model as C, frame_fe as FE
from geometry import frame_geometry

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "cad", "V6"); os.makedirs(os.path.join(OUT, "parts"), exist_ok=True)
RES = os.path.join(ROOT, "results", "V6"); os.makedirs(RES, exist_ok=True)

COL = dict(front_triangle=(0.16, 0.18, 0.22), swingarm=(0.20, 0.22, 0.27), rocker=(0.75, 0.33, 0.10), links=(0.75, 0.33, 0.10),
           shock_fitting=(0.75, 0.33, 0.10), main_axle=(0.55, 0.57, 0.6), rocker_axle=(0.55, 0.57, 0.6), idler=(0.55, 0.57, 0.6),
           idler_stub=(0.55, 0.57, 0.6), bb_sleeve=(0.75, 0.33, 0.10), idler_carrier=(0.75, 0.33, 0.10), shock=(0.05, 0.37, 0.65), rear_wheel=(0.6, 0.62, 0.65), front_wheel=(0.6, 0.62, 0.65),
           fork_upper=(0.35, 0.37, 0.4), fork_lower=(0.35, 0.37, 0.4), steerer=(0.35, 0.37, 0.4), chainring=(0.45, 0.47, 0.5),
           rotor=(0.45, 0.47, 0.5), cassette=(0.45, 0.47, 0.5), chain_10T=(0.8, 0.6, 0.1), chain_24T=(0.8, 0.6, 0.1), crank_sweep=(0.85, 0.87, 0.9))
FRAME_PARTS = ["front_triangle", "swingarm", "rocker", "links", "shock_fitting", "main_axle", "rocker_axle", "idler", "idler_stub",
               "bb_sleeve", "idler_carrier"]
PART_NO = dict(front_triangle="FT-001_front_triangle_OML", swingarm="SA-001_swingarm_OML", rocker="RK-001_rocker", links="LK-001_push_links",
               shock_fitting="SM-001_shock_mount_fitting", main_axle="AX-001_main_pivot_axle", rocker_axle="AX-002_rocker_axle",
               idler="ID-001_idler_sprocket", idler_stub="ID-002_idler_stub", bb_sleeve="BB-001_bb_sleeve_iscg", idler_carrier="ID-003_idler_carrier")


def assembly_compound(parts, names, label):
    kids = []
    for n in names:
        s = parts[n]
        s.label = PART_NO.get(n, "ENV_" + n)
        s.color = Color(*COL.get(n, (0.6, 0.6, 0.6)))
        kids.append(s)
    return Compound(children=kids, label=label)


def render(parts, names, path, title, views=None, lim=None, zoom=1.0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(16, 7.2), dpi=110)
    views = views or [(0, -90, "from the drive side"), (22, -62, "three-quarter view")]
    light = np.array([0.3, 0.5, -0.8]); light /= np.linalg.norm(light)
    tess = {}
    for n in names:
        V, F, _ = C.safe_tessellate(parts[n], 1.0, 0.5)
        tess[n] = (V, F)
    for i, (el, az, cap) in enumerate(views):
        ax = fig.add_subplot(1, len(views), i + 1, projection="3d")
        for n in names:
            V, F = tess[n]
            tri = V[F][:, :, [0, 2, 1]]                      # plot x, z (depth), y (up)
            nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
            sh = 0.45 + 0.55 * np.abs(nrm @ light[[0, 2, 1]])
            base = np.array(COL.get(n, (0.6, 0.6, 0.6)))
            alpha = 0.18 if n in ("crank_sweep",) else (0.5 if n in ("rear_wheel", "front_wheel") else 1.0)
            fc = np.clip(base[None, :] * sh[:, None] + 0.12, 0, 1)
            pc = Poly3DCollection(tri, facecolors=np.concatenate([fc, np.full((len(fc), 1), alpha)], 1), edgecolors="none")
            ax.add_collection3d(pc)
        ax.set_xlim(-800, 1200); ax.set_ylim(-500, 500); ax.set_zlim(-400, 800)
        if lim is not None:
            (x0, x1), (z0, z1), (y0, y1) = lim
            ax.set_xlim(x0, x1); ax.set_ylim(z0, z1); ax.set_zlim(y0, y1)
            ax.set_box_aspect((x1 - x0, z1 - z0, y1 - y0), zoom=zoom); ax.view_init(elev=el, azim=az); ax.set_axis_off()
        else:
            ax.set_box_aspect((2000, 1000, 1200), zoom=1.3); ax.view_init(elev=el, azim=az); ax.set_axis_off()
        ax.set_title(cap, fontsize=10, y=0.92)
    fig.suptitle(title, fontsize=11, x=0.02, ha="left")
    fig.subplots_adjust(left=0, right=1, top=0.96, bottom=0, wspace=0)
    fig.savefig(path); plt.close(fig)


def surface_deviation(d, g):
    """How far the blended analysis surface is from the CAD outer mould line (mm)."""
    from scipy.spatial import cKDTree
    ft_oml, _ = C.front_triangle(d, g, bores=False)
    V, F, _ = C.safe_tessellate(ft_oml, 0.15, 0.2)
    rng = np.random.default_rng(0)
    area = 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    idx = rng.choice(len(F), 400000, p=area / area.sum())
    r1, r2 = rng.random(len(idx)), rng.random(len(idx)); m = r1 + r2 > 1; r1[m], r2[m] = 1 - r1[m], 1 - r2[m]
    pts = V[F[idx, 0]] + r1[:, None] * (V[F[idx, 1]] - V[F[idx, 0]]) + r2[:, None] * (V[F[idx, 2]] - V[F[idx, 0]])
    Vm, Fm, _ = FE.build_mesh(d, g, 6.0, inset="none")           # the blended tool surface (the analysis mesh sits half a laminate inside it)
    dist, _ = cKDTree(pts).query(Vm)
    return dict(nodes=int(len(Vm)), median=float(np.median(dist)), p90=float(np.percentile(dist, 90)), p99=float(np.percentile(dist, 99)), max=float(dist.max()),
                within_1mm=float((dist < 1.0).mean()), within_3mm=float((dist < 3.0).mean()))


if __name__ == "__main__":
    t0 = time.time()
    d = designs.v6(); asm = C.Assembly(d)
    travel = asm.sw["travel"][-1]
    info = dict(fillets_modelled=asm.ft_info["fillets"], volumes_cm3={}, masses_kg={})
    dens = dict(rocker=2.81e-6, links=2.81e-6, shock_fitting=2.81e-6, main_axle=4.43e-6, rocker_axle=4.43e-6, idler_stub=4.43e-6, idler=2.81e-6,
                bb_sleeve=2.81e-6, idler_carrier=2.81e-6)
    poses = [("topout", 0.0, 0.0), ("sag", 0.25 * travel, 35.0), ("bottomout", travel, 195.0)]
    for name, z, fz in poses:
        parts, q = asm.pose(z, fork_travel=fz)
        if name == "topout":
            for n in FRAME_PARTS:
                export_step(parts[n], os.path.join(OUT, "parts", PART_NO[n] + ".step"))
                info["volumes_cm3"][n] = float(parts[n].volume / 1e3)
                if n in dens:
                    info["masses_kg"][n] = float(parts[n].volume * dens[n])
            render(parts, FRAME_PARTS + ["shock", "rear_wheel", "front_wheel", "fork_upper", "fork_lower", "chainring", "rotor", "cassette", "chain_24T"],
                   os.path.join(ROOT, "results", "figures", "assembly_V6.png"), "V6 solid assembly at top-out (component envelopes in grey and blue)")
            render(parts, FRAME_PARTS + ["shock", "chainring", "chain_24T", "chain_10T"],
                   os.path.join(ROOT, "results", "figures", "assembly_V6_detail.png"),
                   "V6 frame parts around the pivot, linkage and idler (shock envelope in blue, chain in the 10- and 24-tooth cogs in yellow)",
                   views=[(8, -75, "drive side"), (8, 105, "non-drive side"), (62, -90, "from above")],
                   lim=((-230.0, 110.0), (-110.0, 110.0), (-60.0, 370.0)), zoom=1.35)
        names = FRAME_PARTS + ["shock", "rear_wheel", "rotor", "cassette", "chainring", "chain_10T", "chain_24T", "crank_sweep",
                               "fork_upper", "fork_lower", "front_wheel", "steerer"]
        export_step(assembly_compound(parts, names, "DH_FRAME_V6_" + name), os.path.join(OUT, f"assembly_{name}.step"))
        print("exported", name, "%.0fs" % (time.time() - t0), flush=True)
    if "--render-only" in sys.argv:              # STEP files and pictures only; keep the existing clearance results
        sys.exit(0)
    info["surface_deviation_mm"] = surface_deviation(d, asm.g)
    print("deviation", info["surface_deviation_mm"], flush=True)
    out = C.clearance_study(asm, travels=(0, 25, 50, 75, 100, 125, 150, 175, 200), verbose=False)
    out["info"] = info
    json.dump(out, open(os.path.join(RES, "clearance_3d.json"), "w"), indent=1)
    print("--- minimum over travel (mm)")
    for k, v in sorted(out["travel_min"].items(), key=lambda kv: kv[1]["min"]):
        print("  %-34s %6.1f at %s mm" % (k, v["min"], v["at"]))
    print("--- static"); [print("  %-34s %6.1f" % (k, v)) for k, v in sorted(out["static"].items(), key=lambda kv: kv[1])]
    print("--- steering"); [print("  %-28s" % k, {a: round(b, 1) for a, b in v.items()}) for k, v in out["steering"].items()]
    print("masses", {k: round(v, 3) for k, v in info["masses_kg"].items()}, "total %.0fs" % (time.time() - t0))
