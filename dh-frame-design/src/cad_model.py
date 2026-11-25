"""3-D solid model of the frame assembly (build123d / OpenCascade), built from the same primitive definitions the
shell models use, plus machined parts and component envelopes. Exports STEP and runs the 3-D clearance checks.

Frame coordinates: origin BB centre, x forward, y up, z to the rider's left, millimetres, top-out unless a pose is given.
Carbon parts are modelled as the OUTER MOULD LINE (solid); wall thickness comes from the ply book, not from this model.
"""
from __future__ import annotations
import os, sys, json, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from build123d import (Vector, Plane, Pos, Rot, Axis, Ellipse, Circle, Rectangle, Polygon, Cylinder, Box, Solid, Compound, Part, Location,
                       extrude, revolve, make_hull, fillet, new_edges, export_step, Align, Mode)
import frame_fe as FE, swingarm_fe as SW
import suspension as S
from geometry import frame_geometry
from kinematics import Linkage, interp_pose

# ---- interface dimensions (see sources/interfaces.md for where each comes from)
IF = dict(
    bb_bore=42.0, bb_width=83.0, ht_bore=55.9, seat_bore=31.6, seat_insertion=107.0,
    pivot_axle=20.0, pivot_sleeve=26.0, pivot_bush_od=23.0, rocker_axle=17.0, rocker_bush_od=19.0,
    link_pin=12.0, link_bush_od=14.0, shock_pin=12.7, shock_bolt=8.0, shock_eye_width=22.0, shock_hw_width=30.0, axle=12.0,
    iscg_bcd=73.0, iscg_first_deg=50.0,                          # ISCG 05: three M6 holes, first one 50 deg below the BB -> rear-axle line
    chainline=56.5, chain_half_width=4.1, chain_half_height=4.4,
    # SRAM X01 DH DUB crank arm inside face minus 1.5 mm for boots: (radius from BB axis, distance from centre plane)
    crank_profile=[(25.0, 63.2), (35.0, 65.8), (65.0, 72.8), (85.0, 75.3), (105.0, 76.3), (130.0, 76.8), (190.0, 76.8)], crank_outer=104.0,
    ring_radius={30: 64.3, 32: 68.3, 34: 72.3},                  # SRAM XX DH chainring outer radius
    rotor_d=220.0, rotor_z=62.5,                                 # largest rotor allowed; rotor plane estimated
    cog_z={10: -70.0, 24: -47.0}, cog_extra=4.5,                 # cog planes estimated (not published)
    # BoXXer: stanchion plane 6 mm ahead of the steerer for the 44 mm offset (from part codes); spacing and crown outline ESTIMATED
    fork=dict(stanchion_cc=160.0, stanchion_fwd=6.0, stanchion_d=38.0, crown_th=38.0, crown_depth=72.0, crown_gap=141.9, lower_d=50.0, bumper_d=58.0),
    # Vivid Air C1 fit drawing: can 58, sleeve 48.25 from 19.25, reservoir outer edge 63 from the axis, from -11.39 to 98.21
    shock=dict(can_d=58.0, sleeve_d=48.25, sleeve_start=19.25, sleeve_len=22.0, can_len=150.0, body_d=38.0,
               head_d=50.0, head_start=12.0, head_len=40.0, res_d=40.0, res_edge=63.0, res_from=-11.39, res_to=98.21),
)


def V3(p, z=0.0):
    if isinstance(p, Vector):
        return p
    return Vector(float(p[0]), float(p[1]), float(p[2]) if len(p) > 2 else z)


def _pair(v):
    return (float(v[0]), float(v[1])) if np.ndim(v) > 0 else (float(v), float(v))


def tube(a, b, hd, hw):
    """Elliptical tube from a to b (2-D points in the centre plane, or 3-D points); hd = in-plane half-depth, hw = half-width."""
    a3, b3 = V3(a), V3(b)
    t = (b3 - a3).normalized()
    n = Vector(-t.Y, t.X, 0).normalized()
    (hda, hdb), (hwa, hwb) = _pair(hd), _pair(hw)
    wa = (Plane(origin=a3, x_dir=n, z_dir=t) * Ellipse(hda, hwa)).faces()[0].outer_wire()
    wb = (Plane(origin=b3, x_dir=n, z_dir=t) * Ellipse(hdb, hwb)).faces()[0].outer_wire()
    return Solid.make_loft([wa, wb])


def zcyl(c, r, z0, z1):
    return Pos(float(c[0]), float(c[1]), 0.5 * (z0 + z1)) * Cylinder(r, abs(z1 - z0))


def axis_cyl(p0, direction, r, length):
    return Solid.make_cylinder(r, length, Plane(origin=V3(p0), z_dir=Vector(*direction)))


def fuse(parts):
    s = parts[0]
    for p in parts[1:]:
        s = s + p
    return s


def hull_plate(circles, z0, z1):
    """Plate whose outline is the convex hull of circles [(centre2d, radius), ...], between z0 and z1."""
    sk = None
    for c, r in circles:
        f = Pos(float(c[0]), float(c[1]), 0) * Circle(r)
        sk = f if sk is None else sk + f
    hull = make_hull(sk.edges())
    return Pos(0, 0, min(z0, z1)) * extrude(hull, abs(z1 - z0))


def mirror_z(shape):
    return shape.mirror(Plane.XY)


# ------------------------------------------------------------------ carbon parts
def front_triangle(d, g, bores=True, try_fillet=True):
    prim, cuts = FE.primitives(d, g)
    ax = Vector(g["steer_axis"][0], g["steer_axis"][1], 0)
    T, B = V3(g["HT_top"]), V3(g["HT_bot"])
    solids = {}
    for name, p in prim.items():
        if p["kind"] == "tube":
            solids[name] = tube(p["a"], p["b"], p["hd"], p["hw"])
        else:
            solids[name] = zcyl(p["c"], p["r"], -p["hz"], p["hz"])
    order = ["head_tube", "down_tube", "top_tube", "seat_mast", "core", "bb", "pivot", "rocker", "shock"]
    radii = dict(down_tube=10.0, top_tube=8.0, seat_mast=8.0, core=6.0, bb=5.0, pivot=3.0, rocker=3.0, shock=3.0)
    body = solids[order[0]]
    filleted = {}
    for name in order[1:]:
        comb = body + solids[name]
        done = False
        if try_fillet:
            ne = new_edges(body, solids[name], combined=comb)
            for r in (radii[name], radii[name] * 0.6):
                try:
                    f = fillet(ne, r)
                    if f.is_valid and len(f.solids()) == 1:
                        f.tessellate(0.5, 0.5)
                        comb, done, filleted[name] = f, True, r
                        break
                except Exception:
                    pass
        if not done:
            filleted[name] = 0.0
        body = comb
    # trim the extended ends
    body = body - axis_cyl(T, (-ax.X, -ax.Y, 0), 48, 60) - axis_cyl(B, (ax.X, ax.Y, 0), 48, 60)
    hz = IF["bb_width"] / 2
    body = body - zcyl((0, 0), 34, hz, hz + 20) - zcyl((0, 0), 34, -hz - 20, -hz)
    P_, R_, M_ = (np.asarray(d["pts"][k], float) for k in ("P", "R", "M"))
    body = body - zcyl(P_, 22, 29, 50) - zcyl(P_, 22, -50, -29) - zcyl(R_, 19, 31, 50) - zcyl(R_, 19, -50, -31)
    info = dict(fillets=filleted)
    if bores:
        L = float(g["head_tube_len"])
        body = body - axis_cyl(T - ax * 5, (ax.X, ax.Y, 0), IF["ht_bore"] / 2, L + 10)
        body = body - zcyl((0, 0), IF["bb_bore"] / 2, -60, 60) - zcyl(P_, IF["pivot_sleeve"] / 2, -40, 40) - zcyl(R_, IF["rocker_bush_od"] / 2 + 2.5, -40, 40)
        # seat for the bolted and bonded aluminium shock-mount fitting (the carbon lug of the analysis model is replaced by it)
        body = body - shock_fitting(d, envelope=True) - bb_sleeve(d, envelope=True)
        m0, m1 = (np.asarray(v, float) for v in d["seat_mast"])
        tm = (m1 - m0) / np.linalg.norm(m1 - m0)
        body = body - axis_cyl(m1 + tm * 10, (-tm[0], -tm[1], 0), IF["seat_bore"] / 2, IF["seat_insertion"] + 10)
    return body, info


def swingarm(d, g, bores=True):
    prim, ref = SW.sw_geometry(d, g)
    parts = []
    for p in prim:
        if p[0] == "tube":
            parts.append(tube(p[1], p[2], p[3], p[4]))
        elif p[0] == "zcyl":
            parts.append(zcyl(p[1], p[2], p[3], p[4]))
        else:
            lo, hi = p[1], p[2]
            parts.append(Pos(*(0.5 * (lo + hi))) * Box(*(hi - lo)))
    body = fuse(parts)
    if bores:
        A, P_, S_ = ref["A"], ref["P"], ref["S"]
        for sg in (1, -1):
            e, lg, dr = SW.side(ref["eye"], sg), SW.side(ref["lug"], sg), SW.side(ref["drop"], sg)
            body = body - zcyl(P_, IF["pivot_bush_od"] / 2, sg * (e[0] - 1), sg * (e[1] + 1))
            body = body - zcyl(S_, IF["link_pin"] / 2, sg * (lg[0] - 1), sg * (lg[1] + 1)) - zcyl(S_, ref["lug_r"] + 2.0, sg * 45.0, sg * 57.0)
            body = body - zcyl(A, IF["axle"] / 2, sg * (dr[0] - 1), sg * (dr[1] + 1))
    return body


# ------------------------------------------------------------------ machined parts (7075 / Ti)
def shock_fitting(d, envelope=False):
    """7075 clevis for the air-can end of the shock, seated in a pocket on the down tube / BB junction."""
    M_ = np.asarray(d["pts"]["M"], float)
    ear = hull_plate([(M_, 14.0), (M_ + np.array([-11.0, -24.0]), 9.0), (M_ + np.array([15.0, -21.0]), 9.0)], 15.0, 23.0)
    base = hull_plate([(M_ + np.array([-12.0, -27.0]), 7.0), (M_ + np.array([17.0, -24.0]), 7.0)], -23.0, 23.0)
    if envelope:
        return hull_plate([(M_, 16.0), (M_ + np.array([-12.0, -27.0]), 8.0), (M_ + np.array([17.0, -24.0]), 8.0)], -24.0, 24.0)
    body = ear + mirror_z(ear) + base
    return body - zcyl(M_, IF["shock_bolt"] / 2, -30, 30)        # M8 bolt through RockShox 8 x 30 mounting hardware


def rocker(d):
    """7075 rocker: two side plates clamped on a rotating 17 mm axle that turns in bushes housed in the seat mast.
    The front arms run high and step inward ahead of the mast so that the shock's damper head stays clear."""
    R_, K_, L_, S_, M_ = (np.asarray(d["pts"][k], float) for k in ("R", "K", "L", "S", "M"))
    t = (K_ - M_) / np.linalg.norm(K_ - M_)                        # shock axis, frame end -> rocker end
    e = np.array([-t[1], t[0]])
    if np.dot(e, R_ - K_) < 0:
        e = -e                                                    # perpendicular to the shock, toward the rocker pivot
    km = K_ + 30.0 * e + 8.0 * t
    u = (L_ - S_) / np.linalg.norm(L_ - S_)
    n = np.array([-u[1], u[0]])
    half = [hull_plate([(R_, 17), (km, 10)], 32, 40),              # hub to step, outside the mast
            hull_plate([(km, 9)], 15, 40),                         # step inward, ahead of the mast face and above the shock head
            hull_plate([(km, 9), (K_, 11)], 15, 23),               # shock-eye cheek
            hull_plate([(R_, 17), (L_, 13)], 39, 44.5),            # inner cheek of the link clevis
            hull_plate([(L_, 13)], 57.5, 63),                      # outer cheek
            hull_plate([(L_ + u * 16, 6.0), (L_ + u * 9 + n * 10, 5), (L_ + u * 9 - n * 10, 5)], 39, 63)]   # clevis bridge beyond the link eye
    h = fuse(half)
    h = h - zcyl(R_, IF["rocker_axle"] / 2, 25, 50) - zcyl(K_, 4.0, 10, 30) - zcyl(L_, IF["link_pin"] / 2, 30, 70)
    return h + mirror_z(h)


def link(d, pose=None):
    S_, L_ = (np.asarray((pose or d["pts"])[k], float) for k in ("S", "L"))
    one = (hull_plate([(S_, 8), (L_, 8)], 45.5, 56.5) + zcyl(S_, 12, 45.5, 56.5) + zcyl(L_, 12, 45.5, 56.5)
           - zcyl(S_, IF["link_bush_od"] / 2, 40, 60) - zcyl(L_, IF["link_bush_od"] / 2, 40, 60))
    return one + mirror_z(one)


def iscg_holes(d):
    """ISCG 05 hole centres seen from the drive side (e*thirteen drawing): 73 mm bolt circle, first hole 50 deg below the
    line from the BB to the rear axle at full extension, the others 100 deg apart."""
    A_ = np.asarray(d["pts"]["A"], float)
    a0 = np.arctan2(A_[1], A_[0]) + np.radians(IF["iscg_first_deg"])
    return [0.5 * IF["iscg_bcd"] * np.array([np.cos(a0 + k * np.radians(100.0)), np.sin(a0 + k * np.radians(100.0))]) for k in range(3)]


def bb_sleeve(d, envelope=False):
    """BB-001: threaded 7075 bottom-bracket sleeve with the ISCG 05 tabs as an integral drive-side flange (bonded in)."""
    hz = IF["bb_width"] / 2
    flange = fuse([hull_plate([(np.zeros(2), 25.0), (h, 8.5)], -hz, -hz + 5.0) for h in iscg_holes(d)])
    body = zcyl((0, 0), IF["bb_bore"] / 2, -hz, hz) + flange
    if envelope:
        return flange
    body = body - zcyl((0, 0), 16.9, -hz - 1, hz + 1)            # 1.37 in x 24 TPI thread, minor diameter about 33.8 mm
    body = body - zcyl((0, 0), 19.0, -hz + 19.0, hz - 19.0)      # relieved between the two 19 mm thread lengths
    for h in iscg_holes(d):
        body = body - zcyl(h, 2.5, -hz - 1, -hz + 6.0)           # M6 tapping size
    return body


def idler_carrier(d):
    """ID-003: 8 mm 7075 plate on the three ISCG tabs carrying the idler stub, outboard of the BB shell face.
    Nothing can sit on the pivot axis outboard of the swingarm eye, because the chain passes there, so the idler is a
    cantilever on this plate: a triangular web between the front tab, the top tab and the idler keeps it stiff in its plane."""
    hz = IF["bb_width"] / 2
    c = np.asarray(d["idler"]["centre"], float)
    holes = iscg_holes(d)
    top = max(holes, key=lambda h: h[1]); front = max(holes, key=lambda h: h[0])
    z0, z1 = -hz - 8.0, -hz
    body = fuse([hull_plate([(holes[i], 8.5), (holes[(i + 1) % 3], 8.5)], z0, z1) for i in range(3)]
                + [hull_plate([(front, 8.5), (top, 11.0), (c, 14.0)], z0, z1)])
    body = body - zcyl((0, 0), 24.5, z0 - 1, z1 + 1)             # clearance for the BB cup
    for h in holes:
        body = body - zcyl(h, 3.3, z0 - 1, z1 + 1)
    return body - zcyl(c, 6.0, z0 - 1, z1 + 1)                   # idler stub seat (M12 thread)


def axles(d):
    P_, R_ = (np.asarray(d["pts"][k], float) for k in ("P", "R"))
    ez = d.get("swingarm", {}).get("eye_z", (31.0, 46.5))
    zr, zl = -(SW.side(ez, -1)[1] + 2.5), SW.side(ez, 1)[1] + 2.5
    main = zcyl(P_, IF["pivot_axle"] / 2, zr, zl) - zcyl(P_, 7.0, zr - 1, zl + 1)
    rock = zcyl(R_, IF["rocker_axle"] / 2, -45, 45) - zcyl(R_, 5.5, -46, 46)
    return main, rock


def idler_assembly(d):
    c = np.asarray(d["idler"]["centre"], float)
    r = S.sprocket_radius(d["idler"]["teeth"])
    z = -IF["chainline"]
    sprocket = zcyl(c, r + 3.0, z - 1.1, z + 1.1) + zcyl(c, 13.0, z - 5, z + 5)
    stub = zcyl(c, 8.0, z - 6.5, -IF["bb_width"] / 2 - 8.0) + zcyl(c, 6.0, -IF["bb_width"] / 2 - 8.0, -IF["bb_width"] / 2)   # shoulder on the carrier, M12 into it
    return sprocket, stub


# ------------------------------------------------------------------ component envelopes
def crank_sweep():
    prof = IF["crank_profile"]
    pts = [(r, z) for r, z in prof] + [(prof[-1][0], IF["crank_outer"]), (prof[0][0], IF["crank_outer"])]
    face = Plane(origin=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0)) * Polygon(*pts, align=None)
    left = revolve(face, Axis.Z, 360)
    return left + mirror_z(left)


def chainring(d):
    r = IF["ring_radius"][d["chainring"]]
    return zcyl((0, 0), r + IF["chain_half_height"], -IF["chainline"] - IF["chain_half_width"], -IF["chainline"] + IF["chain_half_width"])


def chain_run(d, A):
    """Upper chain run from the idler to the cassette, for the 10- and 24-tooth cogs (each at its own lateral position)."""
    c2 = np.asarray(d["idler"]["centre"], float); r2 = S.sprocket_radius(d["idler"]["teeth"])
    hh, hw = IF["chain_half_height"], IF["chain_half_width"]
    solids = []
    for teeth in (10, 24):
        rc = S.sprocket_radius(teeth)
        nt = S.tangent_normal(np.asarray(A, float), rc, c2, r2)
        q1 = np.asarray(A, float) + rc * nt; q2 = c2 + r2 * nt
        t = (q2 - q1) / np.linalg.norm(q2 - q1); n = np.array([-t[1], t[0]])
        zr, zf = IF["cog_z"][teeth], -IF["chainline"]
        pr = Plane(origin=Vector(q1[0], q1[1], zr), x_dir=Vector(n[0], n[1], 0), z_dir=Vector(t[0], t[1], 0))
        pf = Plane(origin=Vector(q2[0], q2[1], zf), x_dir=Vector(n[0], n[1], 0), z_dir=Vector(t[0], t[1], 0))
        wr = (pr * Rectangle(2 * hh, 2 * hw)).faces()[0].outer_wire()
        wf = (pf * Rectangle(2 * hh, 2 * hw)).faces()[0].outer_wire()
        solids.append(Solid.make_loft([wr, wf]))
    return solids


def wheel(axle_c, radius, width, axis_dir=(0, 0, 1)):
    """Tyre and rim envelope as a body of revolution about the axle."""
    rs = radius - width / 2
    prof = Plane(origin=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    tyre = revolve(prof * (Pos(rs, 0) * Ellipse(width / 2, width / 2)), Axis.Z, 360)
    rim = revolve(prof * (Pos(rs - width / 2 - 12, 0) * Rectangle(26, 36)), Axis.Z, 360)
    w = tyre + rim
    return Pos(float(axle_c[0]), float(axle_c[1]), 0) * w


def rear_extras(A):
    rotor = zcyl(A, IF["rotor_d"] / 2, IF["rotor_z"] - 1.0, IF["rotor_z"] + 1.0)
    r10 = S.sprocket_radius(10) + IF["cog_extra"]; r24 = S.sprocket_radius(24) + IF["cog_extra"]
    z10, z24 = IF["cog_z"][10] - 3.0, IF["cog_z"][24] + 3.0
    cone = Solid.make_cone(r10, r24, z24 - z10, Plane(origin=Vector(float(A[0]), float(A[1]), z10), z_dir=Vector(0, 0, 1)))
    return rotor, cone


def shock_body(K, M):
    """Vivid air shock envelope (C1 fit drawing): sleeve and air can at the frame end (M); damper head and piggyback
    reservoir at the rocker end (K), reservoir pointing forward into the open front triangle."""
    q = IF["shock"]
    K, M = np.asarray(K, float), np.asarray(M, float)
    L = np.linalg.norm(K - M); t = (K - M) / L
    fwd = np.array([t[1], -t[0]])
    if fwd[0] < 0:
        fwd = -fwd
    dirv = (t[0], t[1], 0)
    ro = q["res_edge"] - q["res_d"] / 2
    w = IF["shock_eye_width"] / 2
    parts = [zcyl(M, 12.0, -w, w),
             axis_cyl(M + t * q["sleeve_start"], dirv, q["sleeve_d"] / 2, q["sleeve_len"]),
             axis_cyl(M + t * (q["sleeve_start"] + q["sleeve_len"]), dirv, q["can_d"] / 2, q["can_len"] - q["sleeve_start"] - q["sleeve_len"]),
             axis_cyl(M + t * q["can_len"], dirv, q["body_d"] / 2, max(L - q["can_len"] - q["head_start"] - q["head_len"], 1.0)),
             axis_cyl(K - t * (q["head_start"] + q["head_len"]), dirv, q["head_d"] / 2, q["head_len"]),
             zcyl(K, 13.0, -w, w),
             axis_cyl(K - t * q["res_to"] + fwd * ro, dirv, q["res_d"] / 2, q["res_to"] - q["res_from"]),
             hull_plate([(K - t * 28.0, 15.0), (K - t * 28.0 + fwd * ro, 15.0)], -17, 17)]
    return fuse(parts)


def fork(d, g, travel=0.0, steer_deg=0.0):
    """BoXXer envelope: crowns, upper tubes, lowers and front wheel. Steering about the steering axis."""
    q = IF["fork"]
    ax = np.array([g["steer_axis"][0], g["steer_axis"][1]]); nr = np.array([g["steer_normal"][0], g["steer_normal"][1]])
    C = np.asarray(g["crown_race"], float); T = np.asarray(g["HT_top"], float)
    axle = np.asarray(g["front_axle"], float) - travel * ax
    dirv = (ax[0], ax[1], 0)
    upper_parts, lower_parts = [], []
    top = C - ax * (q["crown_gap"] + q["crown_th"] * 0.5)
    for sg in (1, -1):
        base = top + nr * q["stanchion_fwd"]
        st = Solid.make_cylinder(q["stanchion_d"] / 2, q["crown_gap"] + 330.0, Plane(origin=Vector(base[0], base[1], sg * q["stanchion_cc"] / 2), z_dir=Vector(*dirv)))
        upper_parts.append(st)
        bump_c = C - ax * (q["crown_gap"] * 0.5) + nr * q["stanchion_fwd"]
        upper_parts.append(Solid.make_cylinder(q["bumper_d"] / 2, 30.0, Plane(origin=Vector(bump_c[0], bump_c[1], sg * q["stanchion_cc"] / 2), z_dir=Vector(*dirv))))
        lb = axle - nr * d["fork_offset"] + nr * q["stanchion_fwd"] - ax * 300.0
        lower_parts.append(Solid.make_cylinder(q["lower_d"] / 2, 330.0, Plane(origin=Vector(lb[0], lb[1], sg * q["stanchion_cc"] / 2), z_dir=Vector(*dirv))))
    crown_c = C + ax * (q["crown_th"] / 2 + 2.0) + nr * q["stanchion_fwd"] * 0.5
    pl = Plane(origin=Vector(crown_c[0], crown_c[1], 0), x_dir=Vector(nr[0], nr[1], 0), z_dir=Vector(*dirv))
    lower_crown = pl * Box(q["crown_depth"], q["stanchion_cc"] + 58.0, q["crown_th"])
    uc = C - ax * (q["crown_gap"] + 12.0) + nr * q["stanchion_fwd"] * 0.5
    pu = Plane(origin=Vector(uc[0], uc[1], 0), x_dir=Vector(nr[0], nr[1], 0), z_dir=Vector(*dirv))
    upper_crown = pu * Box(q["crown_depth"] - 6.0, q["stanchion_cc"] + 54.0, 24.0)
    steerer = Solid.make_cylinder(14.3, q["crown_gap"] + 40.0, Plane(origin=V3(C + ax * 5), z_dir=Vector(-ax[0], -ax[1], 0)))
    wh = wheel(axle, d["front_tyre_radius"], d["tyre_width"])
    grp = fuse(upper_parts + [lower_crown, upper_crown]) 
    low = fuse(lower_parts)
    if steer_deg:
        sa = Axis(V3(C), Vector(*dirv))
        grp, low, wh = grp.rotate(sa, steer_deg), low.rotate(sa, steer_deg), wh.rotate(sa, steer_deg)
    return dict(fork_upper=grp, fork_lower=low, front_wheel=wh, steerer=steerer)


# ------------------------------------------------------------------ assembly, poses, clearances
def rotz(shape, centre, ang_rad):
    return shape.rotate(Axis(Vector(float(centre[0]), float(centre[1]), 0), Vector(0, 0, 1)), float(np.degrees(ang_rad)))


class Assembly:
    def __init__(self, d):
        self.d = d
        self.g = frame_geometry(d); d["pts"]["A"] = tuple(float(v) for v in self.g["rear_axle"])
        self.sw = Linkage(d["pts"], d["shock_stroke"]).sweep(n=401)
        g = self.g
        self.ft, self.ft_info = front_triangle(d, g)
        self.sa0 = swingarm(d, g)
        self.rk0 = rocker(d)
        self.fitting = shock_fitting(d)
        self.main_axle, self.rocker_axle = axles(d)
        self.idler, self.idler_stub = idler_assembly(d)
        self.bb_sleeve, self.carrier = bb_sleeve(d), idler_carrier(d)
        self.crank = crank_sweep()
        self.ring = chainring(d)
        A0 = np.asarray(d["pts"]["A"], float)
        self.rwheel0 = wheel(A0, d["rear_tyre_radius"], d["tyre_width"])
        self.rotor0, self.cassette0 = rear_extras(A0)

    def pose(self, z, fork_travel=0.0, steer=0.0, with_fork=True):
        d, g = self.d, self.g
        q = interp_pose(self.sw, z)
        P_, R_ = np.asarray(d["pts"]["P"], float), np.asarray(d["pts"]["R"], float)
        th, ph = q["theta"], q["phi"]
        parts = dict(front_triangle=self.ft, swingarm=rotz(self.sa0, P_, th), rear_wheel=rotz(self.rwheel0, P_, th),
                     rotor=rotz(self.rotor0, P_, th), cassette=rotz(self.cassette0, P_, th), rocker=rotz(self.rk0, R_, ph),
                     links=link(d, dict(S=q["S"], L=q["L"])), shock=shock_body(q["K"], d["pts"]["M"]),
                     main_axle=self.main_axle, rocker_axle=self.rocker_axle, idler=self.idler, idler_stub=self.idler_stub,
                     shock_fitting=self.fitting, bb_sleeve=self.bb_sleeve, idler_carrier=self.carrier,
                     chainring=self.ring, crank_sweep=self.crank)
        ch = chain_run(d, q["A"])
        parts["chain_10T"], parts["chain_24T"] = ch[0], ch[1]
        if with_fork:
            parts.update(fork(d, g, fork_travel, steer))
        return parts, q


JOINTS = {   # pairs that meet at a designed joint: (joint point key, keep-out radius) -> clearance is measured outside it
    ("swingarm", "front_triangle"): ("P", 30.0), ("rocker", "front_triangle"): ("R", 26.0), ("links", "swingarm"): ("S", 24.0),
    ("links", "rocker"): ("L", 24.0), ("rocker", "shock"): ("K", 16.0), ("shock", "front_triangle"): ("M", 20.0),
    ("swingarm", "main_axle"): ("P", 14.0), ("idler_carrier", "front_triangle"): ("BB", 46.0),
}
TRAVEL_PAIRS = [("rear_wheel", "front_triangle"), ("swingarm", "front_triangle"), ("swingarm", "crank_sweep"), ("swingarm", "chainring"),
                ("swingarm", "idler"), ("swingarm", "chain_10T"), ("swingarm", "chain_24T"), ("swingarm", "shock"),
                ("rocker", "front_triangle"), ("rocker", "shock"), ("rocker", "rear_wheel"), ("links", "front_triangle"),
                ("links", "rear_wheel"), ("links", "crank_sweep"), ("links", "swingarm"), ("links", "rocker"), ("links", "shock"),
                ("shock", "front_triangle"), ("shock", "crank_sweep"), ("shock", "idler"), ("rocker", "crank_sweep"), ("swingarm", "idler_stub"),
                ("swingarm", "idler_carrier"), ("shock", "idler_carrier"), ("swingarm", "main_axle")]
STATIC_PAIRS = [("rear_wheel", "swingarm"), ("rotor", "swingarm"), ("cassette", "swingarm"), ("crank_sweep", "front_triangle"),
                ("crank_sweep", "idler"), ("chainring", "front_triangle"), ("idler", "front_triangle"),
                ("idler_carrier", "chainring"), ("idler_carrier", "crank_sweep"), ("idler_carrier", "front_triangle")]


def _dist(a, b, joint=None, q=None, d=None):
    """Minimum distance; at a designed joint the region within the keep-out radius of the joint axis is excluded."""
    if joint is not None:
        key, rad = joint
        c = np.zeros(2) if key == "BB" else np.asarray(q[key] if key in q else d["pts"][key], float)
        a = a - zcyl(c, rad, -120, 120)
    return float(a.distance_to(b))


def clearance_study(asm, travels=(0, 25, 50, 75, 100, 125, 150, 175, 200), verbose=True):
    d = asm.d
    out = dict(travel={}, static={}, steering={})
    for z in travels:
        parts, q = asm.pose(float(z), with_fork=False)
        row = {}
        for a, b in TRAVEL_PAIRS:
            j = JOINTS.get((a, b))
            row[f"{a} - {b}"] = _dist(parts[a], parts[b], j, q, d)
        out["travel"][str(z)] = row
        if verbose:
            print("travel", z, {k: round(v, 1) for k, v in row.items() if v < 8.0})
    parts, q = asm.pose(0.0, with_fork=False)
    for a, b in STATIC_PAIRS:
        out["static"][f"{a} - {b}"] = _dist(parts[a], parts[b], JOINTS.get((a, b)), q, d)
    for ft in (0.0, 200.0):
        for st in (0, 20, 40):
            f = fork(d, asm.g, ft, float(st))
            out["steering"][f"fork travel {ft:.0f}, steer {st}"] = dict(
                fork_upper=float(f["fork_upper"].distance_to(asm.ft)), fork_lower=float(f["fork_lower"].distance_to(asm.ft)),
                front_wheel=float(f["front_wheel"].distance_to(asm.ft)))
    # minima over travel
    keys = list(next(iter(out["travel"].values())).keys())
    out["travel_min"] = {k: dict(min=min(out["travel"][t][k] for t in out["travel"]), at=min(out["travel"], key=lambda t: out["travel"][t][k])) for k in keys}
    return out


def safe_tessellate(shape, tol=1.0, ang=0.5):
    """Triangulate a shape face by face; faces the mesher cannot triangulate are skipped instead of raising."""
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRep import BRep_Tool
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopAbs import TopAbs_REVERSED
    BRepMesh_IncrementalMesh(shape.wrapped, tol, False, ang, True)
    verts, tris, off, skipped = [], [], 0, 0
    for f in shape.faces():
        loc = TopLoc_Location()
        poly = BRep_Tool.Triangulation_s(f.wrapped, loc)
        if poly is None:
            skipped += 1
            continue
        trsf = loc.Transformation()
        n = poly.NbNodes()
        for i in range(1, n + 1):
            pnt = poly.Node(i).Transformed(trsf)
            verts.append((pnt.X(), pnt.Y(), pnt.Z()))
        rev = f.wrapped.Orientation() == TopAbs_REVERSED
        for i in range(1, poly.NbTriangles() + 1):
            a, b, c = poly.Triangle(i).Get()
            tris.append((off + a - 1, off + (c if rev else b) - 1, off + (b if rev else c) - 1))
        off += n
    return np.array(verts, float).reshape(-1, 3), np.array(tris, int).reshape(-1, 3), skipped
