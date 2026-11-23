"""Load cases (limit loads at the tyre contact patches) and conversion to front-triangle interface loads."""
from __future__ import annotations
import numpy as np
from kinematics import Linkage, interp_pose
import loads as Ld

ULT = 1.5   # ultimate = 1.5 x limit

# forces on the bike from the ground / rider, frame axes (x forward, y up, z left), newtons
# Each case fixes the hand load and all but one vertical wheel force; the remaining vertical wheel force ("solve")
# is found from the pitching-moment balance about the bottom bracket, so the rider's feet react a pure force there.
# Lateral loads are bounded by wheel side-collapse strength (about 1.5 kN, estimated).
CASES = [
    dict(key="LC1", name="Hard braking into a compression", zr=20.0, zf=140.0, solve="rear",
         rear=(-500.0, 0.0, 0.0), front=(-1500.0, 3000.0, 0.0), hands=(800.0, -1200.0, 0.0)),
    dict(key="LC2a", name="Bottom-out landing, rider centred", zr=200.0, zf=190.0, solve="front",
         rear=(0.0, 8300.0, 0.0), front=(0.0, 0.0, 0.0), hands=(0.0, -2000.0, 0.0)),
    dict(key="LC2b", name="Bottom-out landing, rider weight back", zr=200.0, zf=120.0, solve="front",
         rear=(0.0, 9200.0, 0.0), front=(0.0, 0.0, 0.0), hands=(0.0, 1000.0, 0.0)),
    dict(key="LC2c", name="Bottom-out landing, rider weight forward", zr=200.0, zf=195.0, solve="front",
         rear=(0.0, 9200.0, 0.0), front=(0.0, 0.0, 0.0), hands=(0.0, -3000.0, 0.0)),
    dict(key="LC2d", name="Front wheel cases a knuckle (8 kN, 45 deg rearward)", zr=100.0, zf=150.0, solve="rear",
         rear=(0.0, 0.0, 0.0), front=(-5660.0, 5660.0, 0.0), hands=(0.0, 0.0, 0.0)),
    dict(key="LC3", name="Sideways landing (1.5 kN side load at each tyre)", zr=180.0, zf=170.0, solve="front",
         rear=(0.0, 5500.0, 1500.0), front=(0.0, 0.0, 1500.0), hands=(0.0, 0.0, 0.0)),
    dict(key="LC4", name="Cornering compression (3 g, side load 0.35 of normal)", zr=120.0, zf=100.0, solve="front",
         rear=(0.0, 1710.0, 600.0), front=(0.0, 0.0, 400.0), hands=(0.0, 0.0, 0.0)),
]


def balance(d, g, sw, case):
    """Return rear, front, hand force vectors with the 'solve' wheel's vertical force set by moment balance about the BB."""
    from kinematics import interp_pose
    fr = np.array(case["rear"], float); ff = np.array(case["front"], float); fh = np.array(case["hands"], float)
    hand = np.array([d["reach"] - 20.0, d["stack"] + 110.0])
    q = interp_pose(sw, case["zr"])
    Cr = q["A"] + np.array([0.0, -d["rear_tyre_radius"]])
    Cf = g["front_axle"] - case["zf"] * g["steer_axis"] + np.array([0.0, -d["front_tyre_radius"]])
    cr = lambda r, f: r[0] * f[1] - r[1] * f[0]
    if case["solve"] == "front":
        m = cr(Cr, fr[:2]) + cr(hand, fh[:2]) + cr(Cf, np.array([ff[0], 0.0]))
        ff[1] = -m / Cf[0]
    else:
        m = cr(Cf, ff[:2]) + cr(hand, fh[:2]) + cr(Cr, np.array([fr[0], 0.0]))
        fr[1] = -m / Cr[0]
    return fr, ff, fh


def fork_3d(d, g, zf, fc, fh, hand):
    ax = np.array([g["steer_axis"][0], g["steer_axis"][1], 0.0]); n3 = np.array([g["steer_normal"][0], g["steer_normal"][1], 0.0])
    z3 = np.array([0.0, 0.0, 1.0])
    T = np.array([g["HT_top"][0], g["HT_top"][1], 0.0]); B = np.array([g["HT_bot"][0], g["HT_bot"][1], 0.0])
    axle = np.array([g["front_axle"][0], g["front_axle"][1], 0.0]) - zf * ax
    C = axle + np.array([0.0, -d["front_tyre_radius"], 0.0])
    fc, fh, hand = np.asarray(fc, float), np.asarray(fh, float), np.asarray(hand, float)
    cols = [n3, z3, n3, z3, ax]                       # force directions of unknowns Ru_n, Ru_z, Rl_n, Rl_z, N
    arms = [T - B, T - B, B - B, B - B, B - B]
    A = np.zeros((5, 5)); b = np.zeros(5)
    Fext = fc + fh
    Mext = np.cross(C - B, fc) + np.cross(hand - B, fh)
    for j, (dirj, armj) in enumerate(zip(cols, arms)):
        mj = np.cross(armj, dirj)
        A[:, j] = [dirj @ n3, dirj @ z3, dirj @ ax, mj @ z3, mj @ n3]
    b[:] = [-(Fext @ n3), -(Fext @ z3), -(Fext @ ax), -(Mext @ z3), -(Mext @ n3)]
    x = np.linalg.solve(A, b)
    RT = x[0] * n3 + x[1] * z3; RB = x[2] * n3 + x[3] * z3 + x[4] * ax
    steer_torque = float((Mext + np.cross(T - B, RT)) @ ax)
    return dict(HTU=-RT, HTL=-RB, contact=C, steer_torque_Nmm=steer_torque, radial_upper=float(np.linalg.norm(RT)),
                radial_lower=float(np.linalg.norm(x[2] * n3 + x[3] * z3)), axial=float(x[4]))


def interface_loads(d, g, sw, case):
    """Loads on the front-triangle masters (6-vectors) for a case, plus bookkeeping for the balance check."""
    P = np.array([*d["pts"]["P"], 0.0])
    fr, ff, fh = balance(d, g, sw, case)
    hand = np.array([d["reach"] - 20.0, d["stack"] + 110.0, 0.0])
    rb = Ld.rear_free_body(d, sw, case["zr"], fr[:2])
    Cr = np.array([rb["contact"][0], rb["contact"][1], 0.0])
    fk = fork_3d(d, g, case["zf"], ff, fh, hand)
    L = {}
    L["HTU"] = np.concatenate([fk["HTU"], np.zeros(3)])
    L["HTL"] = np.concatenate([fk["HTL"], np.zeros(3)])
    fz = np.array([0.0, 0.0, fr[2]])
    L["PIV"] = np.concatenate([np.array([rb["P"][0], rb["P"][1], 0.0]) + fz, np.cross(Cr - P, fz)])
    L["ROCK"] = np.array([rb["R"][0], rb["R"][1], 0, 0, 0, 0.0])
    L["SHK"] = np.array([rb["M"][0], rb["M"][1], 0, 0, 0, 0.0])
    # independent whole-system statics: what the BB support must provide
    Fext = fr + ff + fh
    Mext = np.cross(Cr, fr) + np.cross(fk["contact"], ff) + np.cross(hand, fh) - fk["steer_torque_Nmm"] * np.array([g["steer_axis"][0], g["steer_axis"][1], 0.0])
    expect = np.concatenate([-Fext, -Mext])
    info = dict(link=rb["link"], shock=rb["shock"], pivot=float(np.linalg.norm(L["PIV"][:3])), rocker=float(np.linalg.norm(rb["R"])),
                ht_upper=fk["radial_upper"], ht_lower=fk["radial_lower"], ht_axial=fk["axial"], steer_torque=fk["steer_torque_Nmm"],
                contact_rear=Cr, contact_front=fk["contact"], f_rear=fr, f_front=ff, f_hands=fh)
    return L, expect, info
