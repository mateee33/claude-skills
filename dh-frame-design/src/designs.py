"""Design definitions (one dictionary per revision). Units mm / degrees / kg, frame coordinates (see geometry.py)."""
from __future__ import annotations
import copy
import numpy as np

COMPONENTS = dict(
    fork="RockShox BoXXer Ultimate D2, 27.5 in, 200 mm, DebonAir+, 44 mm offset, Tall upper crown",
    shock="RockShox Vivid Ultimate DH D1 (air), 250 x 75 mm, standard eyelets, 30 x 8 mm hardware",
    tyres="27.5 x 2.5 in (ETRTO 63-584) DH casing, front and rear",
)

BASE = dict(
    # ---- fit and geometry targets
    head_angle=63.0,
    reach=475.0,
    stack=632.5,
    bb_height=345.0,
    rear_centre=440.0,             # axle to BB, straight line, top-out
    # ---- components (manufacturer documentation in sources/fork_and_shock.md)
    front_tyre_radius=356.0,       # 27.5 x 2.5, estimated nominal (tyres vary about +/-4 mm)
    rear_tyre_radius=356.0,
    tyre_width=64.0,
    fork_axle_to_crown=586.0,      # RockShox 2027 front suspension specifications, 27.5 in, 200 mm
    fork_offset=44.0,
    fork_travel=200.0,
    lower_headset_stack=4.0,       # ZS56 lower cup + crown race, estimated
    upper_headset_stack=9.0,       # ZS56 upper cup + cover, estimated
    shock_e2e=250.0,
    shock_stroke=75.0,
    rear_travel=200.0,
    # ---- drivetrain used for anti-squat / chain growth
    chainring=32, cog=17,
    idler=dict(teeth=14, centre=(-54.0, 92.0)),
    # ---- structure reference lines (side view, top-out)
    seat_mast=((-18.0, 70.0), (-82.0, 400.0)),   # axis, bottom -> top
    seat_mast_depth=48.0,
    down_tube_end=(20.0, -25.0),                 # axis point at the BB end
    down_tube_depth=82.0,
    top_tube_end=(-68.0, 352.0),                 # axis point at the seat-mast junction
    top_tube_depth=56.0,
)


def v1():
    d = copy.deepcopy(BASE)
    d["name"] = "V1"
    d["lr_target"] = dict(z=[0.0, 200.0], v=[3.10, 2.30])   # linear leverage target, 25.8 % progression
    # hard points at top-out (fit_linkage.py result, rounded to 0.1 mm)
    d["pts"] = dict(P=(-25.0, 120.0),     # main pivot (on the seat-mast axis)
                    S=(-185.0, 192.2),    # push-link eye on the swingarm
                    L=(-139.6, 308.9),    # push-link eye on the rocker
                    R=(-55.5, 286.0),     # rocker pivot on the seat mast
                    K=(5.0, 333.0),       # shock eye on the rocker
                    M=(40.8, 85.6))       # shock eye on the front triangle
    d["tokens"] = 2
    d["sag_frac"] = 0.25
    return d


def with_axle(d):
    """Add the rear-axle top-out position (from rear-centre length and BB height) to the hard points."""
    from geometry import frame_geometry
    g = frame_geometry(d)
    d["pts"]["A"] = tuple(float(v) for v in g["rear_axle"])
    return d, g


def v2():
    """V2: leverage curve steepened (3.08-2.30 -> 3.48-2.17) to raise mid-stroke support and pressure at 25 % sag."""
    d = v1()
    d["name"] = "V2"
    d["lr_target"] = dict(z=[0.0, 50.0, 100.0, 150.0, 200.0], v=[3.40, 3.20, 2.60, 2.30, 2.22])
    d["pts"] = dict(P=(-25.0, 120.0), S=(-190.0, 211.8), L=(-125.4, 325.0), R=(-49.7, 278.0), K=(0.0, 323.9), M=(38.9, 77.0))
    return d


def _sym(half):
    return half + half[::-1]


def v3():
    """V3: V2 kinematics; laminate reinforced after the first structural run (head-tube junction, head tube, tube walls)."""
    F, U = "F", "U"
    d = v2()
    d["name"] = "V3"
    d["htj_len"] = 140.0          # length of the head-tube junction reinforcement measured from the steering axis
    import frame_fe as FE
    L = FE.base_layups()
    L["ht_junction"] = _sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 0),
                             (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 0)])
    L["head_tube"] = _sym([(F, 45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 90),
                           (U, 45), (U, -45), (U, 0), (U, 90), (U, 0)])
    L["top_tube"] = _sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 0), (U, 90)])
    L["down_tube"] = _sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 90)])
    L["seat_mast"] = _sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0)])
    d["layups"] = L
    return d


def v4():
    """V4: V3 plus a laterally stronger swingarm (wider lower spar and upright, thicker spar laminate, knee build-up)."""
    F, U = "F", "U"
    d = v3()
    d["name"] = "V4"
    d["swingarm"] = dict(lower_hw=15.0, upright_hw=13.0, knee_patch=55.0)
    import swingarm_fe as SW
    L = SW.sw_layups()
    L["spar"] = _sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 90)])
    L["knee"] = _sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 90)])
    L["web"] = _sym([(F, 45), (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 90)])
    d["sw_layups"] = L
    return d


def v5():
    """V5: V4 plus a redesigned shock mount: flanged bushes bearing on 8 mm lug walls instead of bond-carried inserts."""
    d = v4()
    d["name"] = "V5"
    d["shock_mount"] = "tophat"
    return d


def v6():
    """V6: first revision defined and checked as a 3-D assembly against manufacturers' interface drawings (DESIGN_V6.md)."""
    F, U = "F", "U"
    d = v5()
    d["name"] = "V6"
    d["upper_headset_stack"] = 8.0                               # Cane Creek Forty ZS56 short cover
    d["idler"] = dict(teeth=14, centre=(30.0, 100.5))            # on a bolt-on carrier ahead of the pivot; chain line through the pivot
    d["rev6"] = True
    d["shell_inset"] = "half_thickness"      # solid model = tool (outer) surface; shell analysis runs on the laminate mid-plane
    d["dt_ht_offset"] = 62.0                                     # down tube joins the head tube higher so the fork's lower crown can swing under it
    # down tube tapers toward the head tube; narrower seat mast between the swingarm arms; head tube 70.8 mm outside
    # diameter so that a 7.4 mm wall remains around the 55.9 mm headset bore; rocker boss sized for its bush sleeve
    d["sections"] = dict(dt_hd=(41.0, 34.0), sm_hw=26.0, ht_r=35.4, rocker_r=17.5)
    import frame_fe as FE
    Lf = FE.base_layups()
    Lf.update(d.get("layups") or {})
    Lf["head_tube"] = _sym([(F, 45)] + [(U, 0), (U, 90), (U, 45), (U, -45)] * 5 + [(U, 0), (U, 90), (U, 0)])       # 48 plies, 7.43 mm
    d["layups"] = Lf
    A = (-439.86, 11.0); S = d["pts"]["S"]; P = d["pts"]["P"]
    ux, uy = (S[0] - A[0]), (S[1] - A[1]); un = (ux ** 2 + uy ** 2) ** 0.5
    U1 = (A[0] + 115.0 * ux / un, A[1] + 115.0 * uy / un)
    up = lambda f: (P[0] + f * (S[0] - P[0]), P[1] + f * (S[1] - P[1]))        # point on the pivot -> link-lug line
    # Swingarm stations: (x, y, |z|, half-depth, half-width) of the tool surface. L = non-drive side, R = drive side.
    # The drive side is boxed in between the seat mast (|z| < 26) and the chain (|z| > 51) around the pivot, so the
    # non-drive side is made wider there and carries more of the side load.
    d["swingarm"] = dict(
        layout="v6",
        lower_path=[(A[0], A[1] - 12.0, 89.5, 15.0, 10.5),       # leaves the dropout below the axle, outboard of the hub end
                    (-330.0, 20.0, 83.0, 17.0, 13.5),            # outboard of the 220 mm rotor / cassette
                    (-260.0, 34.0, 57.5, 18.0, 13.5),            # between spokes and crank arm, below the chain in every gear
                    (-80.0, 72.0, 54.0, 20.0, 15.5)],            # between tyre and crank arm, into the yoke
        upper_path=[(A[0], A[1], 89.5, 14.0, 10.5),
                    (U1[0], U1[1], 86.0, 14.5, 10.0),
                    (S[0], S[1], 51.0, 15.0, 11.0)],
        upright_path=dict(
            # drive side: narrow where the chain crosses it (pivot to 36 % of its length), wider above
            R=[(S[0], S[1], 51.0, 16.0, 10.0), (*up(0.58), 44.5, 18.0, 12.5), (*up(0.36), 38.75, 19.0, 7.5), (P[0], P[1], 38.75, 19.0, 7.5)],
            L=[(S[0], S[1], 51.0, 16.0, 10.0), (*up(0.45), 47.0, 18.0, 13.0), (P[0], P[1], 46.5, 18.0, 15.5)]),
        strut_path=dict(                                          # continues the lower spar line from the yoke to the pivot eye
            R=[(-80.0, 72.0, 52.0, 16.0, 14.0), (-62.0, 87.7, 42.0, 15.0, 9.0), (P[0], P[1], 38.75, 15.0, 7.5)],
            L=[(-80.0, 72.0, 54.0, 16.0, 15.5), (P[0], P[1], 46.5, 15.0, 15.5)]),
        yoke_box=(-80.0, -54.0, 56.0, 96.0, (-58.0, 68.0)),      # x0, x1, y0, y1, (z0, z1) of the cross-member ahead of the tyre
        eye_r=22.0, eye_z=dict(R=(31.0, 46.5), L=(31.0, 62.0)), lug_r=16.0, lug_z=(38.5, 63.5), drop_r=19.0, drop_z=(78.5, 100.0),
        knee_patches=[((-80.0, 68.0), 50.0)])
    import swingarm_fe as SW
    L = SW.sw_layups()
    L["spar"] = _sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 0), (U, 90), (U, 0), (U, 45), (U, -45)])                     # 22 plies, 3.48 mm
    L["strut"] = _sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 90)])                    # 22 plies
    L["node"] = _sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 0), (U, 90),
                      (U, 0), (U, 45), (U, -45), (U, 0)])                                                                                   # 32 plies, 5.00 mm
    L["knee"] = _sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 0), (U, 90),
                      (U, 45), (U, -45), (U, 0), (U, 0), (U, 45), (U, -45)])                                                                # 36 plies, 5.60 mm
    L["yoke"] = _sym([(F, 45), (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 90),
                      (U, 45), (U, -45), (U, 0), (U, 90)])                                                                                  # 34 plies, 5.30 mm
    d["sw_layups"] = L
    return d


REVISIONS = ["v1", "v2", "v3", "v4", "v5", "v6"]
FINAL = "v6"
