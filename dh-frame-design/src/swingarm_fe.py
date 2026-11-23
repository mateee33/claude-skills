"""Shell model of the carbon swingarm (idealised): two triangulated side frames, pivot yoke web, rigid axle.

Body coordinates = frame coordinates at top-out. Loads for a given wheel travel are rotated into body axes.
Supported at the main pivot (all six components); the push-link force from statics is applied at the link eyes, so
in-plane cases are self-balanced and the pivot's reaction moment about z is a balance check.
"""
from __future__ import annotations
import numpy as np
from geometry import frame_geometry
from kinematics import Linkage, interp_pose
from shellfe import mesh_from_sdf, ShellModel, boundary_nodes, buckling
import laminate as lam
import loads as Ld
from frame_fe import smin, sd_zcyl
from cases import CASES, ULT, balance

F_, U_ = "F", "U"
sym = lambda h: h + h[::-1]


def sw_layups():
    return {
        "spar": sym([(F_, 45), (U_, 0), (U_, 0), (U_, 45), (U_, -45), (U_, 0), (U_, 0), (U_, 90)]),
        "node": sym([(F_, 45), (U_, 0), (U_, 90), (U_, 45), (U_, -45), (U_, 0), (U_, 90), (U_, 45), (U_, -45), (U_, 0), (U_, 90)]),
        "web": sym([(F_, 45), (U_, 45), (U_, -45), (U_, 0), (U_, 90), (U_, 45), (U_, -45)]),
    }


def sd_tube3(P, a, b, hd, hw):
    a, b = np.asarray(a, float), np.asarray(b, float)
    t = (b - a); L = np.linalg.norm(t); t /= L
    n = np.array([-t[1], t[0], 0.0]); n /= np.linalg.norm(n)
    bv = np.cross(t, n)
    r = P - a
    s = r @ t; u = r @ n; w = r @ bv
    q = np.sqrt((u / hd) ** 2 + (w / hw) ** 2)
    return np.maximum((q - 1.0) * min(hd, hw), np.maximum(-s, s - L))


def sd_zcyl_off(P, c, r, z0, z1):
    d = np.hypot(P[:, 0] - c[0], P[:, 1] - c[1]) - r
    return np.maximum(d, np.maximum(z0 - P[:, 2], P[:, 2] - z1))


def sd_box(P, lo, hi):
    c = 0.5 * (np.asarray(lo) + np.asarray(hi)); h = 0.5 * (np.asarray(hi) - np.asarray(lo))
    q = np.abs(P - c) - h
    return np.linalg.norm(np.clip(q, 0, None), axis=1) + np.minimum(q.max(1), 0)


def sw_geometry(d, g):
    A = np.asarray(d["pts"]["A"], float); P = np.asarray(d["pts"]["P"], float); S = np.asarray(d["pts"]["S"], float)
    s = d.get("swingarm", {})
    zA, zP, zS = s.get("z_axle", 86.0), s.get("z_pivot", 38.0), s.get("z_link", 50.0)
    # knee point where the lower spar turns inward ahead of the tyre
    tA = (P - A) / np.linalg.norm(P - A)
    knee = A + tA * (np.linalg.norm(P - A) - 62.0)
    zK = s.get("z_knee", 52.0)
    prim = []
    for sgn in (1.0, -1.0):
        a3 = np.array([A[0], A[1], sgn * zA]); k3 = np.array([knee[0], knee[1], sgn * zK]); p3 = np.array([P[0], P[1], sgn * zP])
        s3 = np.array([S[0], S[1], sgn * zS])
        prim += [("tube", a3, k3, s.get("lower_hd", 18.0), s.get("lower_hw", 11.0), "spar"),
                 ("tube", k3, p3, s.get("lower_hd", 18.0), s.get("lower_hw", 11.0), "spar"),
                 ("tube", a3, s3, s.get("upper_hd", 15.0), s.get("upper_hw", 10.0), "spar"),
                 ("tube", s3, p3, s.get("upright_hd", 17.0), s.get("upright_hw", 11.0), "spar"),
                 ("zcyl", P, 24.0, min(sgn * 28.0, sgn * 48.0), max(sgn * 28.0, sgn * 48.0), "node"),
                 ("zcyl", S, 15.0, min(sgn * 40.0, sgn * 60.0), max(sgn * 40.0, sgn * 60.0), "node"),
                 ("zcyl", A, 19.0, min(sgn * 78.5, sgn * 96.0), max(sgn * 78.5, sgn * 96.0), "node")]
    # yoke web joining the two lower spars just behind the seat mast, below pivot height
    wc = P + np.array([-44.0, -22.0])
    prim.append(("box", np.array([wc[0] - 4.0, wc[1] - 26.0, -zK + 2.0]), np.array([wc[0] + 4.0, wc[1] + 26.0, zK - 2.0]), None, None, "web"))
    return prim, dict(A=A, P=P, S=S, zA=zA, zP=zP, zS=zS)


def prim_sd(P, p):
    if p[0] == "tube":
        return sd_tube3(P, p[1], p[2], p[3], p[4])
    if p[0] == "zcyl":
        return sd_zcyl_off(P, p[1], p[2], p[3], p[4])
    return sd_box(P, p[1], p[2])


def build(d, g, h=5.0, layups=None):
    prim, ref = sw_geometry(d, g)
    def sdf(P):
        v = None
        for p in prim:
            dd = prim_sd(P, p)
            v = dd if v is None else smin(v, dd, 6.0)
        return v
    A, P_, S = ref["A"], ref["P"], ref["S"]

    def keep(V):
        xy = V[:, :2]; az = np.abs(V[:, 2])
        k = np.ones(len(V), bool)
        k &= ~((np.hypot(*(xy - P_).T) < 22.5) & ((az < 28.0 + 2.5) | (az > 48.0 - 2.5)))
        k &= ~((np.hypot(*(xy - S).T) < 13.5) & ((az < 40.0 + 2.5) | (az > 60.0 - 2.5)))
        k &= ~((np.hypot(*(xy - A).T) < 17.5) & ((az < 78.5 + 2.5) | (az > 96.0 - 2.5)))
        return k
    lo = np.array([A[0] - 30.0, min(A[1], P_[1]) - 60.0, -102.0]); hi = np.array([P_[0] + 34.0, S[1] + 30.0, 102.0])
    V, F = mesh_from_sdf(sdf, (lo, hi), h, clip=keep)
    cen = V[F].mean(1)
    D = np.stack([prim_sd(cen, p) for p in prim], 1)
    own = D.argmin(1)
    zone = np.array([prim[i][5] for i in own], dtype=object)
    xmat = np.zeros((len(F), 3))
    for i, p in enumerate(prim):
        m_ = own == i
        if p[0] == "tube":
            t = (p[2] - p[1]) / np.linalg.norm(p[2] - p[1]); xmat[m_] = t
        elif p[0] == "zcyl":
            xmat[m_] = [0, 0, 1.0]
        else:
            xmat[m_] = [0, 0, 1.0]
    # node reinforcement near the hard points
    tA = (P_ - A) / np.linalg.norm(P_ - A)
    knee = A + tA * (np.linalg.norm(P_ - A) - 62.0)
    layups = layups or d.get("sw_layups") or sw_layups()
    for pt, rad in ((P_, 46.0), (S, 34.0), (A, 40.0)):
        zone[(np.hypot(*(cen[:, :2] - pt).T) < rad) & (zone != "web")] = "node"
    kr = d.get("swingarm", {}).get("knee_patch", 0.0)
    if kr and "knee" in layups:                       # local build-up where the lower spar turns inward
        zone[(np.hypot(*(cen[:, :2] - knee).T) < kr) & (zone == "spar")] = "knee"
    order = list(layups.keys())
    m = ShellModel(V, F)
    m.set_properties([lam.shellprop(layups[z]) for z in order], np.array([order.index(z) for z in zone]), xmat)
    b = boundary_nodes(F); xy = V[:, :2]
    rings = dict(PIV=b[np.hypot(*(xy[b] - P_).T) < 28.0], LINK=b[np.hypot(*(xy[b] - S).T) < 18.0], AXLE=b[np.hypot(*(xy[b] - A).T) < 22.0])
    for name, c in (("PIV", P_), ("LINK", S), ("AXLE", A)):
        assert len(rings[name]) >= 12, (name, len(rings[name]))
        m.add_spider(name, rings[name], [c[0], c[1], 0.0])
    m.zone, m.zone_names, m.layups = zone, order, layups
    m.assemble(); m.factorize([("PIV", [0, 1, 2, 3, 4, 5])])
    return m


def case_loads(d, g, sw, case):
    """Loads on the swingarm masters in body axes for a load case (limit)."""
    fr, ff, fh = balance(d, g, sw, case)
    q = interp_pose(sw, case["zr"])
    P = np.asarray(d["pts"]["P"], float)
    th = q["theta"]                                    # swingarm rotation at this pose
    c, s = np.cos(-th), np.sin(-th)
    Rb = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])   # global -> body
    rb = Ld.rear_free_body(d, sw, case["zr"], fr[:2])
    ul = (q["L"] - q["S"]) / np.linalg.norm(q["L"] - q["S"])
    f_link = np.array([-rb["link"] * ul[0], -rb["link"] * ul[1], 0.0])        # on the swingarm at S
    f_axle = np.array([fr[0], fr[1], fr[2]])
    r_c = np.array([0.0, -d["rear_tyre_radius"], 0.0])                          # contact relative to axle (global)
    m_axle = np.cross(r_c, f_axle)
    L = dict(AXLE=np.concatenate([Rb @ f_axle, Rb @ m_axle]), LINK=np.concatenate([Rb @ f_link, np.zeros(3)]))
    return L, dict(link=rb["link"], f_rear=fr)


def run(d, h=5.0, verbose=True, layups=None):
    g = frame_geometry(d); d["pts"]["A"] = tuple(float(v) for v in g["rear_axle"])
    sw = Linkage(d["pts"], d["shock_stroke"]).sweep(n=401)
    m = build(d, g, h, layups)
    from scipy.spatial import cKDTree
    slaves = np.concatenate([mm["slaves"] for mm in m.masters.values()])
    cen = m.V[m.F].mean(1)
    dist, _ = cKDTree(m.V[slaves]).query(cen)
    valid = dist > 10.0
    area = 0.5 * np.linalg.norm(np.cross(m.V[m.F[:, 1]] - m.V[m.F[:, 0]], m.V[m.F[:, 2]] - m.V[m.F[:, 0]]), axis=1)
    out = dict(h=h, nodes=len(m.V), cases={})
    for case in CASES:
        L, info = case_loads(d, g, sw, case)
        u, reac, ur = m.solve(L)
        Rp = m.reaction_at(reac, "PIV")
        e0, kp = m.strains(u)
        fi = np.zeros(len(m.F)); mode = np.zeros(len(m.F), int)
        for z in m.zone_names:
            sel = np.where(m.zone == z)[0]
            r = lam.failure_indices(m.layups[z], e0[sel], kp[sel]); fi[sel] = r["fi"] * ULT; mode[sel] = r["mode"]
        zres = {}
        for z in m.zone_names:
            sel = (m.zone == z) & valid
            if not sel.any():
                continue
            i = np.where(sel)[0][np.argmax(fi[sel])]
            near = sel & (np.linalg.norm(cen - cen[i], axis=1) < 10.0)
            zres[z] = dict(fi=float(np.sum(fi[near] * area[near]) / np.sum(area[near])), peak_element=float(fi[i]),
                           mode=lam.MODE_NAMES[mode[i]], at=[float(v) for v in cen[i]])
        gov = max(zres.items(), key=lambda kv: kv[1]["fi"])
        dax = m.master_disp(ur, "AXLE")
        out["cases"][case["key"]] = dict(zones=zres, governing=dict(zone=gov[0], **gov[1]), pivot_reaction=[float(x) for x in Rp],
                                         axle_disp=[float(x) for x in dax], link=float(info["link"]), f_rear=[float(x) for x in info["f_rear"]])
        if verbose:
            print(f"{case['key']:5s} gov {gov[0]:5s} FI_ult {gov[1]['fi']:.2f} (peak el {gov[1]['peak_element']:.2f}) {gov[1]['mode'][:18]:18s} at ({gov[1]['at'][0]:.0f},{gov[1]['at'][1]:.0f},{gov[1]['at'][2]:.0f})"
                  f" | pivot reaction F ({Rp[0]:.0f},{Rp[1]:.0f},{Rp[2]:.0f}) N  Mz {Rp[5]/1e3:.2f} Nm | axle lateral defl {dax[2]:.2f} mm")
    mass = {}
    for z in m.zone_names:
        sel = m.zone == z
        mass[z] = float(area[sel].sum() * lam.areal_mass(m.layups[z]))
    out["mass"] = mass; out["mass_total"] = float(sum(mass.values()))
    # lateral stiffness at the axle: unit lateral force at the axle centre
    u, reac, ur = m.solve(dict(AXLE=[0, 0, 1000.0, 0, 0, 0]))
    out["lateral_stiffness_N_per_mm"] = float(1000.0 / m.master_disp(ur, "AXLE")[2])
    return out, m


if __name__ == "__main__":
    import sys, designs, json, os
    name = sys.argv[1] if len(sys.argv) > 1 else "v3"; h = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
    d = getattr(designs, name)()
    out, m = run(d, h)
    print("nodes", out["nodes"], "mass %.3f kg" % out["mass_total"], out["mass"], "lateral stiffness at axle %.0f N/mm" % out["lateral_stiffness_N_per_mm"])
    od = os.path.join(os.path.dirname(__file__), "..", "results", d["name"]); os.makedirs(od, exist_ok=True)
    json.dump(out, open(os.path.join(od, "swingarm_h%.1f.json" % h), "w"), indent=1, default=float)
    np.savez(os.path.join(od, "_swingarm_mesh.npz"), V=m.V, F=m.F)
