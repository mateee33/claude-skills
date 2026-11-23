"""Suspension behaviour: wheel-force curve, sag/pressure, anti-rise, anti-squat, chain growth.

Assumptions that are the same for every bike analysed (stated once here):
  rider mass 68 kg (kitted) with centre of mass 30 mm ahead of and 780 mm above the BB (attack position, estimated)
  whole-bike mass 17.0 kg with centre of mass 150 mm ahead of and 100 mm above the BB (estimated)
  sprung bike mass 9.5 kg at 200 mm ahead of the BB (estimated)
  front fork at 35 mm of travel (17.5 %) while rear travel is swept
  gear for anti-squat and chain growth: 34-tooth chainring, 17-tooth cog, 16-tooth idler (12.7 mm pitch)
"""
from __future__ import annotations
import numpy as np
from kinematics import Linkage, interp_pose
from airspring import calibrated, MAX_PRESSURE_PSI

G = 9.81
RIDER = dict(mass=68.0, x=30.0, y=780.0)
BIKE = dict(mass=17.0, x=150.0, y=100.0)
SPRUNG_BIKE = dict(mass=9.5, x=200.0)
FRONT_SAG = 35.0
PITCH = 12.7


def sprocket_radius(teeth):
    return PITCH / (2 * np.sin(np.pi / teeth))


def rear_static_load(front_centre, wheelbase, rider_mass=RIDER["mass"]):
    """Rear-wheel sprung load (N) used for sag: static moment balance on level ground."""
    return G * (rider_mass * (front_centre - RIDER["x"]) / wheelbase
                + SPRUNG_BIKE["mass"] * (front_centre - SPRUNG_BIKE["x"]) / wheelbase)


def com():
    m = RIDER["mass"] + BIKE["mass"]
    return np.array([(RIDER["mass"] * RIDER["x"] + BIKE["mass"] * BIKE["x"]) / m,
                     (RIDER["mass"] * RIDER["y"] + BIKE["mass"] * BIKE["y"]) / m])


def tangent_normal(c1, r1, c2, r2):
    """Unit normal n of the 'upper' common tangent of two circles: both tangent points are c_i + r_i n."""
    d = c2 - c1; L = np.linalg.norm(d)
    dh = d / L; dp = np.array([-dh[1], dh[0]])
    if dp[1] < 0:
        dp = -dp
    a = (r1 - r2) / L
    return a * dh + np.sqrt(1 - a * a) * dp


def ground(A, F, rr, rf):
    """Ground line under both tyres. Returns forward unit u, up unit n, contact points."""
    d = F - A; L = np.linalg.norm(d)
    dh = d / L; dp = np.array([-dh[1], dh[0]])
    a = (rf - rr) / L
    n = a * dh + np.sqrt(1 - a * a) * dp
    u = np.array([n[1], -n[0]])
    return u, n, A - rr * n, F - rf * n


def force_curve(sw, spring, p_psi, n=1.0):
    """Wheel force (N) vs wheel travel from the shock spring force and the leverage ratio."""
    return spring.force(sw["stroke"], p_psi, n) / sw["lr"]


def setup(sw, w_rear, sag_frac, tokens, travel=None):
    """Pressure for a given sag (fraction of wheel travel) and the resulting curve metrics."""
    travel = travel or sw["travel"][-1]
    spring = calibrated(tokens)
    z_sag = sag_frac * travel
    x_sag = float(np.interp(z_sag, sw["travel"], sw["stroke"]))
    lr_sag = float(np.interp(z_sag, sw["travel"], sw["lr"]))
    p = spring.pressure_for(x_sag, w_rear * lr_sag)
    f = force_curve(sw, spring, p, 1.0)
    f_fast = force_curve(sw, spring, p, 1.3)
    z = sw["travel"]
    E = np.trapezoid(f, z) / 1000.0
    return dict(tokens=tokens, pressure_psi=p, pressure_bar=p * 0.0689476,
                pressure_frac=p / MAX_PRESSURE_PSI[tokens], x_sag=x_sag, z=z, f=f, f_fast=f_fast,
                mid_ratio=float(np.interp(0.6 * travel, z, f)) / w_rear,
                end_ratio=float(f[-1]) / w_rear, end_ratio_fast=float(f_fast[-1]) / w_rear,
                energy_J=E, drop_height=E / w_rear,
                f_shock_end=float(spring.force(sw["stroke"][-1], p, 1.0)),
                wheel_rate_sag=float(np.interp(z_sag, z, np.gradient(f, z))))


def g1_score(s):
    """Checks a-d of goal G1 (targets fixed in 01_rider_benchmarks_criteria.md)."""
    return dict(a_mid=(2.3 <= s["mid_ratio"] <= 2.8), b_end=(s["end_ratio"] >= 6.5),
                c_energy=(s["drop_height"] >= 0.50), d_pressure=(s["pressure_frac"] <= 0.75))


def kinematic_table(d, g, sw, nz=41):
    """Anti-rise, anti-squat and chain growth vs rear travel for the single-pivot layout."""
    P = np.asarray(d["pts"]["P"], float)
    rr, rf = d["rear_tyre_radius"], d["front_tyre_radius"]
    F = g["front_axle"] - FRONT_SAG * g["steer_axis"]
    cm = com()
    rc, rcr = sprocket_radius(d["cog"]), sprocket_radius(d["chainring"])
    idler = d.get("idler")
    if idler is not None:
        c2, r2 = np.asarray(idler["centre"], float), sprocket_radius(idler["teeth"])
    else:
        c2, r2 = np.zeros(2), rcr
    zs = np.linspace(0, sw["travel"][-1], nz)
    rows = []
    L0 = None
    for z in zs:
        q = interp_pose(sw, z)
        A = q["A"]
        u, n, Cr, Cf = ground(A, F, rr, rf)
        wb = np.dot(Cf - Cr, u)
        h = np.dot(cm - Cr, n)
        # anti-rise: brake caliper on the swingarm, instant centre = main pivot
        ar = (np.dot(P - Cr, n) / np.dot(P - Cr, u)) * wb / h
        # anti-squat by moments about the main pivot (unit thrust)
        nt = tangent_normal(A, rc, c2, r2)
        Q = A + rc * nt
        t = (c2 + r2 * nt) - Q; lt = np.linalg.norm(t); t = t / lt
        cross = lambda a, b: a[0] * b[1] - a[1] * b[0]
        m_thrust = cross(Cr - P, u)
        m_chain = (rr / rc) * cross(Q - P, t)
        m_transfer = (h / wb) * cross(Cr - P, n)
        asq = (m_thrust + m_chain) / (-m_transfer)
        # chain growth of the upper run (rear wheel locked to the swingarm)
        an = np.arctan2(nt[1], nt[0])
        Lc = lt + r2 * an + rc * (q["theta"] - an)
        if L0 is None:
            L0 = Lc
        growth = Lc - L0
        rows.append(dict(z=z, anti_rise=100 * ar, anti_squat=100 * asq, chain_growth=growth,
                         kickback_deg=np.degrees(growth / rcr), wheelbase=wb, com_height=h,
                         rear_centre=np.hypot(*A), axle_dx=q["axle_dx"]))
    return rows
