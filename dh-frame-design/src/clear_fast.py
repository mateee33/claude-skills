"""Fast clearance estimate for swingarm design iterations.

Everything the swingarm must miss (tyre, rotor, cassette, cranks, chainring, chain at two cogs, idler, front
triangle, shock, rocker, links) is sampled as surface points at several travel positions and expressed in the
swingarm's own frame. A candidate swingarm is then tested by evaluating its signed-distance function at those
points, which takes seconds. The estimate is a lower bound near blended junctions and for flat sections; the
final design is verified on the solid model (`run_v6_cad.py`).
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from geometry import frame_geometry
from kinematics import Linkage, interp_pose
import swingarm_fe as SW

TRAVELS = (0.0, 50.0, 100.0, 150.0, 200.0)


def _sample(shape, n, rng):
    import cad_model as C
    V, F, _ = C.safe_tessellate(shape, 0.4, 0.3)
    area = 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    idx = rng.choice(len(F), n, p=area / area.sum())
    r1, r2 = rng.random(n), rng.random(n); m = r1 + r2 > 1; r1[m], r2[m] = 1 - r1[m], 1 - r2[m]
    return V[F[idx, 0]] + r1[:, None] * (V[F[idx, 1]] - V[F[idx, 0]]) + r2[:, None] * (V[F[idx, 2]] - V[F[idx, 0]])


def obstacle_cloud(d, front_triangle=None, seed=0):
    """Points on everything the swingarm must clear, in the swingarm frame at top-out. Returns (points, labels, travel)."""
    import cad_model as C
    rng = np.random.default_rng(seed)
    g = frame_geometry(d); d["pts"]["A"] = tuple(float(v) for v in g["rear_axle"])
    sw = Linkage(d["pts"], d["shock_stroke"]).sweep(n=401)
    P = np.asarray(d["pts"]["P"], float); R = np.asarray(d["pts"]["R"], float); A0 = np.asarray(d["pts"]["A"], float)
    S0 = np.asarray(d["pts"]["S"], float)
    ft = front_triangle if front_triangle is not None else C.front_triangle(d, g, try_fillet=False)[0]
    static = dict(front_triangle=_sample(ft, 120000, rng), crank_sweep=_sample(C.crank_sweep(), 40000, rng),
                  chainring=_sample(C.chainring(d), 8000, rng))
    idl, stub = C.idler_assembly(d)
    static["idler"] = _sample(idl, 5000, rng); static["idler_stub"] = _sample(stub, 2000, rng)
    rk0 = C.rocker(d)
    pts, lab, trv = [], [], []
    fixed = dict(rear_wheel=C.wheel(A0, d["rear_tyre_radius"], d["tyre_width"]))
    fixed["rotor"], fixed["cassette"] = C.rear_extras(A0)
    for n, shp in fixed.items():
        p = _sample(shp, 30000, rng); pts.append(p); lab += [n] * len(p); trv += [-1.0] * len(p)
    for z in TRAVELS:
        q = interp_pose(sw, z)
        th = q["theta"]
        moving = dict(static)
        moving["shock"] = _sample(C.shock_body(q["K"], d["pts"]["M"]), 15000, rng)
        moving["rocker"] = _sample(C.rotz(rk0, R, q["phi"]), 12000, rng)
        moving["links"] = _sample(C.link(d, dict(S=q["S"], L=q["L"])), 6000, rng)
        ch = C.chain_run(d, q["A"])
        moving["chain_10T"] = _sample(ch[0], 6000, rng); moving["chain_24T"] = _sample(ch[1], 6000, rng)
        c, s = np.cos(-th), np.sin(-th)
        for n, p in moving.items():
            xy = p[:, :2] - P
            p2 = np.column_stack([P[0] + c * xy[:, 0] - s * xy[:, 1], P[1] + s * xy[:, 0] + c * xy[:, 1], p[:, 2]])
            # designed joints: ignore the neighbourhood of the joint axis
            if n == "front_triangle":
                p2 = p2[np.hypot(p2[:, 0] - P[0], p2[:, 1] - P[1]) > 30.0]
            if n == "links":
                p2 = p2[np.hypot(p2[:, 0] - S0[0], p2[:, 1] - S0[1]) > 24.0]
            pts.append(p2); lab += [n] * len(p2); trv += [z] * len(p2)
    return np.vstack(pts), np.array(lab), np.array(trv)


def clearances(d, cloud):
    """Minimum distance from each obstacle to the candidate swingarm (mm), with where and which member."""
    pts, lab, trv = cloud
    g = frame_geometry(d); d["pts"]["A"] = tuple(float(v) for v in g["rear_axle"])
    prim, ref = SW.sw_geometry(d, g)
    D = np.stack([SW.prim_sd(pts, p) for p in prim], 1)
    dmin = D.min(1); own = D.argmin(1)
    out = {}
    for n in np.unique(lab):
        sel = np.where(lab == n)[0]
        i = sel[np.argmin(dmin[sel])]
        p = prim[own[i]]
        desc = p[5] + (" tube %.0f,%.0f,%.0f" % tuple(p[1]) if p[0] == "tube" else " " + p[0])
        out[n] = dict(min=float(dmin[i]), travel=float(trv[i]), at=[float(v) for v in pts[i]], member=desc)
    return out


if __name__ == "__main__":
    import designs, time
    t0 = time.time()
    d = designs.v6()
    cloud = obstacle_cloud(d)
    np.savez_compressed(sys.argv[1], pts=cloud[0], lab=cloud[1], trv=cloud[2])
    print("cloud", cloud[0].shape, "%.0fs" % (time.time() - t0))
    for n, v in sorted(clearances(d, cloud).items(), key=lambda kv: kv[1]["min"]):
        print("  %-16s %6.1f mm at travel %4.0f  (%.0f, %.0f, %.0f)  %s" % (n, v["min"], v["travel"], *v["at"], v["member"]))
