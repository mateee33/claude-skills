"""Estimated air-spring model for the RockShox Vivid Ultimate DH (air), 250 x 75.

RockShox publishes no force curve or chamber dimensions, so this is a two-chamber
ideal-gas model with ESTIMATED dimensions, scaled by one factor so that it reproduces
a frame-specific pressure chart (Commencal Supreme DH V5.2 Team Replica: 80 kg rider,
264 psi, 2 tokens, sag 22.5 % of shock stroke). See sources/fork_and_shock.md.

  F(x) = P_pos(x) A_bore - P_neg(x) (A_bore - A_body) - P_atm A_body + F_ifp   [absolute pressures]

x = shock stroke from full extension (mm). Polytropic exponent n: 1.0 for slow (sag,
"static" curves), 1.3 for fast landings. Every output of this module is ESTIMATED.
"""
from __future__ import annotations
import numpy as np

PSI = 0.00689476          # MPa per psi
P_ATM = 0.101325          # MPa

BASE = dict(
    d_bore=42.0,          # mm, air piston bore (estimated; outer can is 58 mm, shaft-end step 48.25 mm)
    d_body=28.0,          # mm, damper body through the seal head (estimated)
    v_pos_2tok=180.0e3,   # mm^3, positive volume at full extension with 2 tokens (estimated)
    v_token=4.0e3,        # mm^3 per Bottomless Token (estimated)
    v_neg_eq=23.0e3,      # mm^3, negative volume at the equalisation port (estimated; chosen with x_eq for ~zero top-out force)
    x_eq=12.0,            # mm, stroke at which chambers equalise (estimated)
    f_ifp=120.0,          # N, reservoir gas force on the damper shaft (estimated; 8.3 bar charge)
    stroke=75.0,
    k_scale=1.0,          # calibration factor on areas and volumes (shape preserving)
    bumper_start=70.0,    # mm, bottom-out bumper engagement (estimated)
    bumper_rate=600.0,    # N/mm, bumper stiffness (estimated)
)

MAX_PRESSURE_PSI = {0: 330, 1: 330, 2: 330, 3: 300, 4: 300}   # RockShox service manual, 67.5-75 mm strokes


class AirSpring:
    def __init__(self, tokens=2, **over):
        self.q = dict(BASE); self.q.update(over)
        self.tokens = tokens

    def areas(self):
        q = self.q
        ab = q["k_scale"] * np.pi / 4 * q["d_bore"] ** 2
        ad = q["k_scale"] * np.pi / 4 * q["d_body"] ** 2
        return ab, ad

    def volumes(self):
        q = self.q
        vp0 = q["k_scale"] * (q["v_pos_2tok"] + (2 - self.tokens) * q["v_token"])
        return vp0, q["k_scale"] * q["v_neg_eq"]

    def compression_ratio(self):
        ab, _ = self.areas(); vp0, _ = self.volumes()
        return vp0 / (vp0 - ab * self.q["stroke"])

    def force(self, x, p_gauge_psi, n=1.0, bumper=True):
        """Spring force (N) at stroke x (mm) for a pump pressure set at full extension."""
        q = self.q
        x = np.asarray(x, float)
        ab, ad = self.areas(); an = ab - ad
        vp0, vneq = self.volumes()
        p0 = p_gauge_psi * PSI + P_ATM
        ppos = p0 * (vp0 / (vp0 - ab * x)) ** n
        peq = p0 * (vp0 / (vp0 - ab * q["x_eq"])) ** n
        vneg = np.maximum(vneq + an * (x - q["x_eq"]), 0.2 * vneq)
        pneg = peq * (vneq / vneg) ** n
        f = ppos * ab - pneg * an - P_ATM * ad + q["f_ifp"]
        if bumper:
            f = f + q["bumper_rate"] * np.clip(x - q["bumper_start"], 0, None)
        return f

    def pressure_for(self, x_sag, f_target, n=1.0):
        """Pump pressure (psi) that gives force f_target at stroke x_sag."""
        lo, hi = 20.0, 600.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if self.force(x_sag, mid, n) < f_target:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)


def calibrated(tokens=2, **over):
    """Air spring scaled to the Commencal anchor (computed once, cached)."""
    k = _anchor_scale()
    return AirSpring(tokens=tokens, k_scale=k, **over)


_K = None


def _anchor_scale():
    """Scale factor so that 264 psi / 2 tokens gives the anchor force at 16.9 mm stroke.

    Anchor force: 80 kg rider on a Supreme DH V5 size L (wheelbase 1311, rear centre 454),
    same mass-distribution assumptions as designs.py, leverage 3.23 at sag (third-party estimate).
    """
    global _K
    if _K is not None:
        return _K
    g = 9.81
    fc = 1311 - 454
    w_rear = g * (80 * (fc - 30) / 1311 + 9.5 * (fc - 200) / 1311)      # N at the wheel
    f_anchor = w_rear * 3.23                                             # N at the shock
    x_sag, p = 0.225 * 75, 264.0
    lo, hi = 0.3, 3.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if AirSpring(tokens=2, k_scale=mid).force(x_sag, p) < f_anchor:
            lo = mid
        else:
            hi = mid
    _K = 0.5 * (lo + hi)
    return _K


if __name__ == "__main__":
    k = _anchor_scale()
    s = calibrated(2)
    ab, ad = s.areas()
    print("scale k = %.3f  -> effective bore %.1f mm, body %.1f mm" % (k, np.sqrt(4 * ab / np.pi), np.sqrt(4 * ad / np.pi)))
    for tok in range(5):
        s = calibrated(tok)
        print("tokens", tok, "compression ratio %.2f" % s.compression_ratio(),
              "F(0,17,37.5,56,75 mm) at 200 psi slow:", np.round(s.force([0, 17, 37.5, 56, 75], 200.0, bumper=False)))
    # cross-check with RockShox rule of thumb: psi = rider weight in lb -> about 30 % sag on a generic 2.85 bike
    s = calibrated(0)
    f = s.force(22.5, 176.0)
    print("rule-of-thumb check: 80 kg, 176 psi, 0 tokens, 30%% stroke: shock force %.0f N -> supports %.0f N at the wheel on LR 2.85 (need ~545 N)" % (f, f / 2.85))
