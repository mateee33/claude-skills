"""Synthesis of the shock linkage for a target leverage curve (global search + least squares)."""
from __future__ import annotations
import numpy as np
from scipy.optimize import least_squares
from kinematics import Linkage

KEYS = ["S", "L", "R", "K", "M"]


def unpack(x):
    return {k: np.array(x[2 * i:2 * i + 2], float) for i, k in enumerate(KEYS)}


def ang(u, v):
    c = np.sum(u * v, axis=-1) / (np.linalg.norm(u, axis=-1) * np.linalg.norm(v, axis=-1))
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


def residuals(x, P, A, spec, pack):
    pts = dict(P=P, A=A, **unpack(x))
    lk = Linkage(pts, spec["stroke"])
    sw = lk.sweep(n=61, ncoarse=600)
    travel = spec["travel"]
    zs = np.linspace(0, travel, 21)
    tgt = np.interp(zs, spec["lr_z"], spec["lr_v"])
    r = []
    if sw["ok"]:
        lr = np.interp(zs, sw["travel"], sw["lr"])
        r += list((lr - tgt) / 0.01)                               # 0.01 LR = 1 unit
        r.append((sw["travel"][-1] - travel) / 0.2)               # 0.2 mm
    else:
        short = spec["stroke"] - sw["stroke"][-1]
        r += [30.0 + short] * 21
        r.append(100.0)
    r.append((lk.e2e - spec["e2e"]) / 0.05)                        # 0.05 mm
    p = lk.p
    m0, m1 = pack["mast"]
    t = (m1 - m0) / np.linalg.norm(m1 - m0)
    dR = t[0] * (p["R"] - m0)[1] - t[1] * (p["R"] - m0)[0]         # signed distance to mast axis
    r.append(max(abs(dR) - pack["mast_tol"], 0) / 0.5)
    dt0, dt1 = pack["down_tube"]
    td = (dt1 - dt0) / np.linalg.norm(dt1 - dt0)
    hM = td[0] * (p["M"] - dt0)[1] - td[1] * (p["M"] - dt0)[0]     # height above down-tube axis
    r.append((max(pack["M_height"][0] - hM, 0) + max(hM - pack["M_height"][1], 0)) / pack.get("keepout_w", 0.5))
    a1 = ang(sw["S"] - sw["L"], p["R"] - sw["L"])                  # link / rocker transmission angle
    a2 = ang(p["M"] - sw["K"], p["R"] - sw["K"])                   # shock / rocker transmission angle
    lo1, hi1, lo2, hi2 = pack["trans"]
    worst = (np.clip(lo1 - a1, 0, None) + np.clip(a1 - hi1, 0, None)
             + np.clip(lo2 - a2, 0, None) + np.clip(a2 - hi2, 0, None)).max()
    r.append(worst / 1.0)
    r.append(max(pack["min_link"] - lk.link_len, 0) / 0.5)
    r.append(max(pack["min_arm"] - lk.rock_K, 0) / 0.5)
    r.append(max(pack["min_arm"] - lk.rock_L, 0) / 0.5)
    r.append(max(lk.rock_K - pack["max_arm"], 0) / 0.5)
    r.append(max(lk.rock_L - pack["max_arm"], 0) / 0.5)
    # keep-out circles for the shock axis (pivot housing etc.) and the seat-mast front face, through travel
    viol = 0.0
    M = p["M"]
    for c, rad in pack.get("keepout", []):
        c = np.asarray(c, float)
        ab = sw["K"] - M
        t = np.clip(np.sum((c - M) * ab, axis=1) / np.sum(ab * ab, axis=1), 0, 1)
        dist = np.linalg.norm(c - (M + t[:, None] * ab), axis=1)
        viol = max(viol, float(np.clip(rad - dist, 0, None).max()))
    r.append(viol / pack.get("keepout_w", 0.5))
    if "max_link" in pack:
        r.append(max(lk.link_len - pack["max_link"], 0) / 0.5)
    return np.array(r)


def fit(P, A, bounds, spec, pack, seed=1, nrand=6000, npolish=6, x0=None, sigma=None):
    rng = np.random.default_rng(seed)
    lo = np.array([b[0] for b in bounds], float); hi = np.array([b[1] for b in bounds], float)
    cands = []
    if x0 is not None:
        x0 = np.clip(np.asarray(x0, float), lo + 1e-6, hi - 1e-6)
        cands.append((0.5 * np.sum(residuals(x0, P, A, spec, pack) ** 2), x0))
    if x0 is not None and sigma:
        X = np.clip(x0 + sigma * rng.standard_normal((nrand, len(lo))), lo + 1e-6, hi - 1e-6)
    else:
        X = lo + (hi - lo) * rng.random((nrand, len(lo)))
    for x in X:
        # make the shock the right length cheaply: slide K along R->K direction is not exact, so just score
        c = 0.5 * np.sum(residuals(x, P, A, spec, pack) ** 2)
        cands.append((c, x))
    cands.sort(key=lambda t: t[0])
    best = None
    for c, x in cands[:npolish]:
        sol = least_squares(residuals, x, bounds=(lo, hi), x_scale=20.0, diff_step=1e-5,
                            args=(P, A, spec, pack), max_nfev=300)
        if best is None or sol.cost < best.cost:
            best = sol
    return best


def residuals_metric(x, P, A, spec, pack, w_rear):
    """Residuals that target the G1 metrics directly instead of a prescribed leverage curve."""
    import suspension as S
    base = residuals(x, P, A, dict(spec, lr_z=[0, spec["travel"]], lr_v=[3.0, 3.0]), pack)
    geo = base[21:]                                  # travel, e2e and packaging terms (drop the curve terms)
    pts = dict(P=P, A=A, **unpack(x))
    lk = Linkage(pts, spec["stroke"])
    sw = lk.sweep(n=121, ncoarse=600)
    if not sw["ok"]:
        return np.concatenate([np.full(8, 60.0), geo])
    st = S.setup(sw, w_rear, spec["sag"], spec["tokens"])
    lr = sw["lr"]
    r = [max(spec["mid_target"] - st["mid_ratio"], 0) / 0.005,
         max(st["pressure_frac"] - spec["p_frac_max"], 0) / 0.002,
         max(spec["p_frac_min"] - st["pressure_frac"], 0) / 0.002,
         max(lr[0] - spec["lr0_max"], 0) / 0.01,
         max(lr.max() - lr[0], 0) / 0.01,
         max(spec["lr_end_min"] - lr[-1], 0) / 0.01,
         float(np.clip(np.diff(lr), 0, None).sum()) / 0.01,          # monotone decreasing
         max(spec["end_min"] - st["end_ratio"], 0) / 0.02]
    return np.concatenate([np.array(r), geo])


def fit_metric(P, A, bounds, spec, pack, w_rear, x0, seed=1, nrand=3000, npolish=8, sigma=10.0):
    rng = np.random.default_rng(seed)
    lo = np.array([b[0] for b in bounds], float); hi = np.array([b[1] for b in bounds], float)
    x0 = np.clip(np.asarray(x0, float), lo + 1e-6, hi - 1e-6)
    X = np.vstack([x0, np.clip(x0 + sigma * rng.standard_normal((nrand, len(lo))), lo + 1e-6, hi - 1e-6)])
    costs = [0.5 * np.sum(residuals_metric(x, P, A, spec, pack, w_rear) ** 2) for x in X]
    order = np.argsort(costs)[:npolish]
    best = None
    for i in order:
        sol = least_squares(residuals_metric, X[i], bounds=(lo, hi), x_scale=20.0, diff_step=1e-5,
                            args=(P, A, spec, pack, w_rear), max_nfev=250)
        if best is None or sol.cost < best.cost:
            best = sol
    return best
