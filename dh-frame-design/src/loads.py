"""Design loads: landing simulation, load-case definitions and free-body interface forces.

Everything here is CALCULATED (statics) or SIMULATED (lumped landing model) from ESTIMATED parameters.
Frame coordinates: x forward, y up, z to the rider's left; N, mm.

Structural design mass (not the suspension set-up mass):
  rider 80 kg kitted  = 68 kg x 1.18 (allowance for body-mass change, extra protection, a second rider)
  bike 17 kg          -> system 97 kg
"""
from __future__ import annotations
import numpy as np
from scipy.integrate import solve_ivp
from kinematics import Linkage, interp_pose
from airspring import calibrated
import suspension as S

G = 9.81
M_RIDER_STRUCT = 80.0
M_BIKE = 17.0
M_UNSPRUNG = dict(rear=4.5, front=4.0)


# ------------------------------------------------------------------ measured anchor
def isbs_effective_stiffness():
    """Phillips, Kilgas & Jensen (ISBS 2015): flat drops 0.29/0.48/0.67 m, 76.6 kg riders, 130 mm bike.
    One linear effective spring reproduces all three measured totals; returns k (N/m) and the fit."""
    W = 884.8
    h = np.array([0.29, 0.48, 0.67]); F = np.array([5442., 6800., 7878.])
    k = np.mean(((F - W) ** 2 - W ** 2) / (2 * W * h))
    pred = W + np.sqrt(W ** 2 + 2 * k * W * h)
    return k, h, F, pred, W


def empirical_peak(weight, h, k_over_w=None):
    k, *_, W = isbs_effective_stiffness()
    kw = (k / W) if k_over_w is None else k_over_w
    return weight * (1 + np.sqrt(1 + 2 * kw * h))


# ------------------------------------------------------------------ landing simulation
def fork_spring(z, p_psi=130.0, travel=200.0, cr=3.0, area=830.0, l_neg=60.0, n=1.3):
    """ESTIMATED BoXXer air-spring force at the wheel (N). No manufacturer curve exists."""
    p = p_psi * 0.00689476 + 0.101325
    lc = travel * cr / (cr - 1)
    z = np.clip(z, 0, travel * 0.999)
    f = p * area * ((1 - z / lc) ** (-n) - (1 + z / l_neg) ** (-n))
    return f + 900.0 * np.clip(z - (travel - 8), 0, None)


def landing(wheel, efh, sw=None, p_shock=229.0, tokens=2, mass_share=0.6, rider=M_RIDER_STRUCT,
            k_leg=30e3, c_leg=1800.0, k_tyre=200e3, tyre_stroke=0.050, k_rim=1.5e6,
            c_hs=220.0, f_knee=600.0, c_hbo=900.0, p_fork=140.0, fork_cr=3.0, leg_stroke=0.45):
    """Three-mass vertical landing model for one wheel.

    rider share -> legs (spring + damper) -> sprung bike share -> suspension (air spring, damper,
    hydraulic bottom-out, bumper) -> unsprung mass -> tyre (linear, then rim strike) -> ground.
    efh = equivalent flat-drop height (m): the height that gives the velocity component normal to the landing.
    Returns peak wheel (ground) force, peak suspension force at the wheel, peak travel, peak leg force.
    """
    m_r = mass_share * rider
    m_s = mass_share * (M_BIKE - M_UNSPRUNG["rear"] - M_UNSPRUNG["front"])
    m_u = M_UNSPRUNG[wheel]
    kl, cl = mass_share * k_leg, mass_share * c_leg
    travel = 0.200
    if wheel == "rear":
        spring = calibrated(tokens)
        zt, st, lr = sw["travel"] / 1000.0, sw["stroke"], sw["lr"]
        def f_spring(z):
            zz = np.clip(z, 0, travel)
            return spring.force(np.interp(zz, zt, st), p_shock, 1.3) / np.interp(zz, zt, lr) + 2.0e6 * max(z - travel, 0.0)
    else:
        def f_spring(z):
            return float(fork_spring(1000 * min(max(z, 0), travel), p_fork, 200.0, fork_cr)) + 2.0e6 * max(z - travel, 0.0)

    def f_damp(z, v):
        if v <= 0:
            return 2500.0 * v                       # rebound (not relevant for the peak)
        f = min(1200.0 * v, f_knee) + c_hs * v
        if z > 0.8 * travel:                        # hydraulic bottom-out in the last 20 % of travel
            f += c_hbo * v * (z - 0.8 * travel) / (0.2 * travel)
        return f

    def f_tyre(d):
        if d <= 0:
            return 0.0
        return k_tyre * min(d, tyre_stroke) + k_rim * max(d - tyre_stroke, 0.0)

    v0 = np.sqrt(2 * G * efh)

    def rhs(t, y):
        xr, xs, xu, vr, vs, vu = y                 # positions measured downward from first ground contact
        leg = kl * (xr - xs) + cl * (vr - vs)
        if (xr - xs) > leg_stroke:
            leg += 3.0e5 * (xr - xs - leg_stroke)   # rider's body meets the bike
        leg = max(leg, 0.0)
        z = xs - xu
        fs = f_spring(z) + f_damp(z, vs - vu)
        ft = f_tyre(xu)
        return [vr, vs, vu, G - leg / m_r, G + (leg - fs) / m_s, G + (fs - ft) / m_u]

    sol = solve_ivp(rhs, [0, 0.6], [0, 0, 0, v0, v0, v0], max_step=2e-4, rtol=1e-6, atol=1e-8)
    xr, xs, xu, vr, vs, vu = sol.y
    z = xs - xu
    ft = np.array([f_tyre(d) for d in xu])
    fs = np.array([f_spring(a) + f_damp(a, b) for a, b in zip(z, vs - vu)])
    leg = np.maximum(kl * (xr - xs) + cl * (vr - vs), 0)
    i = int(np.argmax(ft))
    return dict(peak_ground=float(ft.max()), peak_susp=float(fs.max()), peak_travel=float(z.max() * 1000),
                peak_leg=float(leg.max()), tyre_defl=float(xu.max() * 1000), t_peak=float(sol.t[i]),
                weight=(m_r + m_s + m_u) * G, leg_stroke_used=float((xr - xs).max() * 1000))


# ------------------------------------------------------------------ free bodies
def cross2(a, b):
    return a[0] * b[1] - a[1] * b[0]


def rear_free_body(d, sw, z, f_contact, contact_offset=None):
    """In-plane statics of swingarm + rocker at wheel travel z for a force at the rear tyre contact (N).

    Returns forces ON THE FRONT TRIANGLE at P, R, M, plus link and shock forces (compression positive)."""
    q = interp_pose(sw, z)
    P, R, M = (np.asarray(d["pts"][k], float) for k in ("P", "R", "M"))
    A, Sp, Lk, K = q["A"], q["S"], q["L"], q["K"]
    C = A + (np.array([0.0, -d["rear_tyre_radius"]]) if contact_offset is None else contact_offset)
    f = np.asarray(f_contact, float)
    ul = (Lk - Sp) / np.linalg.norm(Lk - Sp)                 # link axis S -> L
    # swingarm: moment about P of contact force + link reaction (link pushes swingarm along -ul with magnitude T) = 0
    T = cross2(C - P, f) / cross2(Sp - P, ul)                # link compression force (N)
    f_link_on_swingarm = -T * ul
    f_P_on_swingarm = -(f + f_link_on_swingarm)
    us = (M - K) / np.linalg.norm(M - K)                     # shock axis K -> M
    # rocker: link pushes rocker at L with +T ul ; shock pushes rocker at K with -Fs us (Fs = shock compression)
    Fs = cross2(Lk - R, T * ul) / cross2(K - R, us)
    f_R_on_rocker = -(T * ul - Fs * us)
    return dict(P=-f_P_on_swingarm, R=-f_R_on_rocker, M=Fs * us, link=T, shock=Fs, pose=q,
                contact=C, lr_check=float(f[1] and Fs / f[1]))


def fork_free_body(d, g, z_f, f_contact, f_hands, hand_pos):
    """In-plane statics of the fork assembly: returns forces ON THE HEAD TUBE at the upper and lower bearing."""
    ax, nrm = g["steer_axis"], g["steer_normal"]
    T, B = g["HT_top"], g["HT_bot"]
    Faxle = g["front_axle"] - z_f * ax
    C = Faxle + np.array([0.0, -d["front_tyre_radius"]])
    f = np.asarray(f_contact, float); h = np.asarray(f_hands, float)
    # unknowns: Ru, Rl (radial, along nrm) at T and B, N (axial along -ax, carried at the lower bearing)
    # forces ON THE FORK from the frame: Ru*nrm at T, Rl*nrm at B, N*(-ax) at B
    A_ = np.array([[nrm[0], nrm[0], -ax[0]], [nrm[1], nrm[1], -ax[1]],
                   [cross2(T - B, nrm), 0.0, 0.0]])
    b_ = -np.array([f[0] + h[0], f[1] + h[1], cross2(C - B, f) + cross2(np.asarray(hand_pos) - B, h)])
    Ru, Rl, N = np.linalg.solve(A_, b_)
    return dict(upper=-(Ru * nrm), lower=-(Rl * nrm - N * ax), Ru=Ru, Rl=Rl, N=N, contact=C)


def g3_metric(head_angle, a2c, offset, head_tube, lower_stack=4.0):
    """Goal G3: per 1 kN at the front axle normal to the ground: moment about the lower head-tube bearing (N m)
    and radial force on the upper head-tube bearing (kN). Geometry only."""
    ha = np.radians(head_angle)
    ax = np.array([np.cos(ha), -np.sin(ha)]); nrm = np.array([np.sin(ha), np.cos(ha)])
    B = np.zeros(2); T = B - head_tube * ax
    axle = B + (lower_stack + a2c) * ax + offset * nrm
    f = np.array([0.0, 1000.0])
    m = cross2(axle - B, f)                       # N mm
    ru = abs(m) / head_tube / 1000.0
    return dict(moment_Nm=abs(m) / 1000.0, upper_bearing_kN=ru, arm_mm=abs(m) / 1000.0)
