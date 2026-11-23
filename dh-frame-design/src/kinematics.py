"""Planar rear-suspension kinematics for the DH frame study.

Layout: linkage-driven single pivot.
  swingarm (rigid): main pivot P, rear axle A, push-link eye S
  push link:        S -> L (fixed length)
  rocker (rigid):   frame pivot R, link eye L, shock eye K
  shock:            K -> M (M fixed to the front triangle)

Coordinates: millimetres, origin at bottom-bracket centre, +x toward the front
wheel, +y up, viewed from the drive side. All input points are given at
top-out (shock fully extended). Compression = clockwise swingarm rotation
(negative angle in this right-handed frame).

Definitions used everywhere in this study
  wheel travel z : vertical (frame +y) displacement of the rear axle from top-out
  leverage ratio : LR = dz / d(shock stroke)   (wheel travel per unit shock travel)
"""
from __future__ import annotations
import numpy as np


def rot(v, ang):
    """Rotate 2-vector(s) v by angle(s) ang (counter-clockwise positive)."""
    c, s = np.cos(ang), np.sin(ang)
    v = np.asarray(v, float)
    return np.stack([c * v[..., 0] - s * v[..., 1], s * v[..., 0] + c * v[..., 1]], axis=-1)


class Linkage:
    def __init__(self, pts: dict, stroke: float):
        self.p = {k: np.asarray(v, float) for k, v in pts.items()}
        self.stroke = float(stroke)
        p = self.p
        self.link_len = np.linalg.norm(p["L"] - p["S"])
        self.rock_L = np.linalg.norm(p["L"] - p["R"])
        self.rock_K = np.linalg.norm(p["K"] - p["R"])
        self.e2e = np.linalg.norm(p["K"] - p["M"])
        # assembly mode: which side of line R->S the link eye L sits at top-out
        e = (p["S"] - p["R"]); n = np.array([-e[1], e[0]])
        self.mode = 1.0 if np.dot(p["L"] - p["R"], n) >= 0 else -1.0

    def poses(self, theta):
        """Vectorised pose for swingarm angles theta (array, radians, <=0 compresses)."""
        p = self.p
        theta = np.atleast_1d(np.asarray(theta, float))
        A = p["P"] + rot(p["A"] - p["P"], theta)
        S = p["P"] + rot(p["S"] - p["P"], theta)
        v = S - p["R"]
        d = np.linalg.norm(v, axis=1)
        a = (self.rock_L**2 - self.link_len**2 + d**2) / (2 * d)
        h2 = self.rock_L**2 - a**2
        valid = h2 >= 0
        h = np.sqrt(np.where(valid, h2, 0.0))
        e = v / d[:, None]
        n = np.stack([-e[:, 1], e[:, 0]], axis=1)
        L = p["R"] + a[:, None] * e + self.mode * h[:, None] * n
        ang0 = np.arctan2(p["L"][1] - p["R"][1], p["L"][0] - p["R"][0])
        phi = np.unwrap(np.arctan2(L[:, 1] - p["R"][1], L[:, 0] - p["R"][0]) - ang0)
        K = p["R"] + rot(p["K"] - p["R"], phi)
        slen = np.linalg.norm(K - p["M"], axis=1)
        return dict(theta=theta, phi=phi, A=A, S=S, L=L, K=K, shock_len=slen, valid=valid)

    def sweep(self, n=401, theta_max=np.radians(45), ncoarse=1500):
        """Sweep from top-out until the full shock stroke is used.

        Returns arrays on a uniform shock-stroke grid. ok=False if the linkage
        locks, goes over-centre, or cannot reach full stroke.
        """
        th = -np.linspace(0, theta_max, ncoarse)
        q = self.poses(th)
        used = self.e2e - q["shock_len"]
        bad = (~q["valid"]) | (np.diff(used, prepend=-1e-9) <= 0)
        bad[0] = False
        first_bad = np.argmax(bad) if bad.any() else len(th)
        hit = np.argmax(used >= self.stroke) if (used >= self.stroke).any() else len(th)
        ok = hit < first_bad
        end = hit + 1 if ok else max(first_bad, 2)
        s_end = self.stroke if ok else used[end - 1]
        s = np.linspace(0, s_end, n)
        th_s = np.interp(s, used[:end], th[:end])
        q = self.poses(th_s)
        z = q["A"][:, 1] - self.p["A"][1]
        x = q["A"][:, 0] - self.p["A"][0]
        lr = np.gradient(z, s)
        q.update(ok=ok, stroke=s, travel=z, axle_dx=x, lr=lr)
        return q


def interp_pose(sw, z):
    """Linear interpolation of every pose array at wheel travel z (scalar)."""
    t = sw["travel"]
    out = {}
    for k in ("A", "S", "L", "K"):
        out[k] = np.array([np.interp(z, t, sw[k][:, 0]), np.interp(z, t, sw[k][:, 1])])
    for k in ("theta", "phi", "stroke", "lr", "shock_len", "axle_dx"):
        out[k] = float(np.interp(z, t, sw[k]))
    return out
