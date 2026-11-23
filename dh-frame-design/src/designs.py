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


REVISIONS = ["v1", "v2", "v3", "v4", "v5"]
FINAL = "v5"
