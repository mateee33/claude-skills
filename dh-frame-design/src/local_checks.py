"""Hand calculations for joints, pins, bearings and bonded inserts (CALCULATED from the interface loads).

Inputs are the largest LIMIT interface forces over all load cases; checks are made at ULTIMATE (x1.5) unless noted.
Material values: sources/standards_loads_materials.md. Items marked (unverified) use typical values that were not
re-checked against a datasheet in this session.
"""
from __future__ import annotations
import numpy as np

ULT = 1.5
TI = dict(yield_=880.0, ult=950.0, shear=550.0, fatigue=510.0)          # Ti-6Al-4V annealed
AL = dict(yield_=503.0, ult=572.0, shear=331.0, fatigue=159.0)          # 7075-T6
STEEL_PIN_YIELD = 1000.0                                                 # hardened alloy-steel pin, (unverified) nominal
DU_STATIC, DU_DYNAMIC = 250.0, 140.0                                     # GGB DU plain bearing, N/mm2
BOND_RT, BOND_HOT = 28.9, 20.7                                           # Loctite EA 9394 lap shear, MPa (25 C / 82 C)
BOND_ALLOW = 0.25 * BOND_HOT                                             # average shear allowed at ultimate (peak/average and fatigue cover), ESTIMATED
CARBON_BEARING_ALLOW = 250.0                                             # MPa, pin-bearing design value for clamped quasi-isotropic laminate, ESTIMATED


def tube_z(do, di):
    return np.pi * (do ** 4 - di ** 4) / (32 * do)


def checks(loads, shock_mount="bonded"):
    """loads: dict with limit forces in N: shock, link (total, two links), pivot, pivot_bearing, rocker, ht_upper, ht_lower,
    dropout, feet, idler."""
    rows = []
    def add(item, demand, capacity, unit, note, kind="calculated"):
        rows.append(dict(item=item, demand=float(demand), capacity=float(capacity), unit=unit,
                         margin=float(capacity / demand - 1), note=note, kind=kind))
    Fs = loads["shock"] * ULT
    # 1 shock eye pin: 12.7 mm steel pin, 22 mm eyelet between clevis tabs 34 mm apart (centre to centre)
    m = Fs / 2 * (34 / 2 - 22 / 4)
    add("Shock eye pin bending (12.7 mm steel pin, both ends of the shock)", m / (np.pi * 12.7 ** 3 / 32), STEEL_PIN_YIELD, "MPa",
        "simply supported pin, load spread over the 22 mm eyelet; yield criterion; pin strength unverified")
    add("Shock eye pin double shear", Fs / (2 * np.pi * 12.7 ** 2 / 4), 0.58 * STEEL_PIN_YIELD, "MPa", "")
    add("Shock mount clevis tabs, bearing in 7075 inserts (2 x 8 mm)", Fs / (2 * 12.7 * 8), 1.5 * AL["yield_"], "MPa", "bearing yield taken as 1.5 x tensile yield")
    if shock_mount == "bonded":
        add("Shock mount inserts, bond shear to carbon lug (2 x 600 mm2 bonded bushes)", Fs / 1200.0, BOND_ALLOW, "MPa",
            "average adhesive shear if the bond is the load path", "estimated")
    else:
        add("Shock mount top-hat bushes bearing on carbon lug walls (2 x 20 mm OD x 8 mm wall)", Fs / (2 * 20 * 8), CARBON_BEARING_ALLOW, "MPa",
            "load carried in bearing; the bond only retains the bushes", "estimated")
    # 2 rocker pivot: 17 mm Ti axle fixed through the seat mast in a bonded sleeve; DU bushes 17 x 12 in each rocker plate
    Fr = loads["rocker"] * ULT
    add("Rocker pivot axle double shear (17 mm Ti-6Al-4V, 11 mm bore)", Fr / (2 * np.pi * (17 ** 2 - 11 ** 2) / 4), TI["shear"], "MPa", "")
    add("Rocker pivot plain bearings, pressure at ultimate (2 x 17 x 12 mm)", Fr / (2 * 17 * 12), DU_STATIC, "MPa", "static rating")
    add("Rocker pivot plain bearings, pressure at limit", loads["rocker"] / (2 * 17 * 12), DU_DYNAMIC, "MPa", "dynamic rating")
    add("Rocker pivot sleeve bearing on carbon seat mast (22 mm sleeve x 56 mm)", Fr / (22 * 56), CARBON_BEARING_ALLOW, "MPa", "", "estimated")
    # 3 push links: two 7075 links 12 x 16 mm, 130 mm eye to eye, DU bushes 12 x 10 at each eye
    Fl = loads["link"] * ULT / 2
    add("Push link column buckling (each, 7075, 12 x 16 mm, 130 mm)", Fl, np.pi ** 2 * 71700 * (16 * 12 ** 3 / 12) / 130 ** 2, "N", "Euler, pinned ends")
    add("Push link compressive stress", Fl / (12 * 16), AL["yield_"], "MPa", "")
    add("Push link eye plain bearings at limit (12 x 10 mm)", loads["link"] / 2 / (12 * 10), DU_DYNAMIC, "MPa", "dynamic rating")
    # 4 main pivot: 20 mm Ti axle (14 mm bore) clamped in the frame, plain bearings 20 x 16 in each swingarm arm
    Fb = loads["pivot_bearing"] * ULT
    add("Main pivot axle bending (20/14 mm Ti-6Al-4V, 10 mm overhang)", Fb * 10 / tube_z(20, 14), TI["yield_"], "MPa", "")
    add("Main pivot plain bearing pressure at limit (20 x 16 mm each side)", loads["pivot_bearing"] / (20 * 16), DU_DYNAMIC, "MPa", "dynamic rating")
    add("Main pivot: same load on a 6004 ball bearing (for comparison)", loads["pivot_bearing"], 5000.0, "N",
        "static rating C0 of an SKF 6004; negative margin is why plain bearings are specified")
    add("Main pivot sleeve bearing on carbon (26 mm sleeve x 56 mm)", loads["pivot"] * ULT / (26 * 56), CARBON_BEARING_ALLOW, "MPa", "", "estimated")
    # 5 head tube bearing seats (ZS56 cups, 12 mm insertion)
    add("Lower headset cup bearing on carbon head tube (56 x 12 mm)", loads["ht_lower"] * ULT / (56 * 12), CARBON_BEARING_ALLOW, "MPa", "", "estimated")
    add("Upper headset cup bearing on carbon head tube (56 x 12 mm)", loads["ht_upper"] * ULT / (56 * 12), CARBON_BEARING_ALLOW, "MPa", "", "estimated")
    # 6 bottom bracket shell (7075 threaded sleeve, 46 mm OD x 83 mm, bonded and co-moulded)
    add("BB shell bearing pressure on carbon (46 x 83 mm)", loads["feet"] * ULT / (46 * 83), CARBON_BEARING_ALLOW, "MPa", "", "estimated")
    # 7 dropouts: 7075 inserts, 12 mm axle, 10 mm wall; bond area 3600 mm2 each, also trapped
    Fd = loads["dropout"] * ULT
    add("Dropout insert, axle bearing (12 x 10 mm)", Fd / (12 * 10), 1.5 * AL["yield_"], "MPa", "")
    add("Dropout insert bond shear (3600 mm2 each)", Fd / 3600.0, BOND_ALLOW, "MPa", "average shear; insert is also wrapped by the spar laminate", "estimated")
    # 8 idler stub: 16 mm Ti stub, 20 mm overhang, chain resultant from a 2.0 kN pedal force
    Fi = loads["idler"] * ULT
    add("Idler stub bending (16 mm Ti-6Al-4V, 20 mm overhang)", Fi * 20 / (np.pi * 16 ** 3 / 32), TI["yield_"], "MPa", "sprint load, 2.0 kN on one pedal")
    return rows


def interface_maxima(struct, sw):
    """Largest limit interface forces over all cases from the front-triangle and swingarm results."""
    cs = struct["cases"]
    g = lambda k: max(c["info"][k] for c in cs.values())
    piv_b = 0.0
    for key, c in cs.items():
        f = np.array(c["interface"]["PIV"])
        inplane = np.hypot(f[0], f[1]) / 2
        couple = np.hypot(f[3], f[4]) / 76.0            # bearing centres 76 mm apart
        piv_b = max(piv_b, inplane + couple + abs(f[2]) / 2)
    drop = 0.0
    for key, c in sw["cases"].items():
        fr = np.array(c["f_rear"])
        drop = max(drop, np.hypot(fr[0], fr[1]) / 2 + abs(fr[2]) * 356.0 / 172.0)
    feet = max(np.linalg.norm(c["bb_reaction"][:3]) for c in cs.values())
    chain = 2000.0 * 165.0 / (12.7 / (2 * np.sin(np.pi / 32)))
    return dict(shock=g("shock"), link=g("link"), pivot=g("pivot"), pivot_bearing=piv_b, rocker=g("rocker"),
                ht_upper=g("ht_upper"), ht_lower=g("ht_lower"), dropout=drop, feet=feet, idler=2 * chain * np.sin(np.radians(50)),
                chain_tension=chain)


def mass_budget(ft_laminate, sa_laminate, shock_mount="bonded"):
    """Frame mass per the G2 definition (kg). Laminate masses come from the shell models; the rest is ESTIMATED."""
    items = [
        ("Front triangle laminate (shell model area x areal mass)", ft_laminate, "calculated"),
        ("Front triangle overlaps, ply drops, resin fillets (+8 %)", 0.08 * ft_laminate, "estimated"),
        ("Front triangle inserts: BB sleeve, headset seats, pivot and rocker sleeves, shock and idler inserts", 0.290, "estimated"),
        ("Main pivot axle (Ti 20/14 x 110) and rocker axle (Ti 17/11 x 80)", 0.125, "calculated"),
        ("Swingarm laminate (shell model)", sa_laminate, "calculated"),
        ("Swingarm overlaps and fillets (+8 %)", 0.08 * sa_laminate, "estimated"),
        ("Swingarm inserts: dropouts, brake mount, pivot and link bushes", 0.175, "estimated"),
        ("Rocker (7075-T6 yoke) with bushes", 0.195, "estimated"),
        ("Push links (2 x 7075) with bushes", 0.160, "estimated"),
        ("Pins, bolts, idler sprocket and stub", 0.215, "estimated"),
        ("Frame protection (down-tube guard, spar and chain protection) and paint", 0.250, "estimated"),
    ]
    if shock_mount != "bonded":
        items.append(("Shock-mount lug wall build-up to 8 mm and top-hat bushes", 0.020, "estimated"))
    return items, float(sum(v for _, v, _ in items))


# ------------------------------------------------------------------ V6 hardware (matches the solid model in cad_model.py)
def idler_statics(d, tension):
    """Force on the idler and its moment about the BB axis from a chain tension, by statics of the two chain runs
    (chainring -> idler on the front side, idler -> cog over the top). Returns the worse of the 10- and 24-tooth cogs."""
    import suspension as S
    from geometry import frame_geometry
    A = np.asarray(frame_geometry(d)["rear_axle"], float)
    c2 = np.asarray(d["idler"]["centre"], float); r2 = S.sprocket_radius(d["idler"]["teeth"]); r1 = S.sprocket_radius(d["chainring"])
    D = np.linalg.norm(c2); ang = np.arctan2(c2[1], c2[0]) - np.arccos((r1 - r2) / D)
    n = np.array([np.cos(ang), np.sin(ang)])
    p_ring, p_id = r1 * n, c2 + r2 * n
    u1 = (p_ring - p_id) / np.linalg.norm(p_ring - p_id)
    out = None
    for teeth in (10, 24):
        rc = S.sprocket_radius(teeth); nt = S.tangent_normal(A, rc, c2, r2)
        q1, q2 = A + rc * nt, c2 + r2 * nt
        u2 = (q1 - q2) / np.linalg.norm(q1 - q2)
        F = tension * np.linalg.norm(u1 + u2)
        M = tension * abs(float(np.cross(p_id, u1) + np.cross(q2, u2)))
        bolt = F / 3 + M / (3 * 36.5)
        if out is None or bolt > out["bolt"]:
            out = dict(force=float(F), moment_Nmm=float(M), bolt=float(bolt), cog=teeth)
    return out


def checks_v6(loads, d=None):
    """Joint and hardware checks for V6. Sizes are those of the solid model; bush sizes come from the GGB DU tables."""
    rows = []
    def add(item, demand, capacity, unit, note, kind="calculated"):
        rows.append(dict(item=item, demand=float(demand), capacity=float(capacity), unit=unit, margin=float(capacity / demand - 1), note=note, kind=kind))
    BOLT_129 = 1080.0                                                   # MPa, class 12.9 proof-level strength (nominal)
    # shock, both ends: RockShox 8 x 30 hardware (12.7 mm pin, M8 bolt through it) between two 8 mm ears 30 mm apart
    Fs = loads["shock"] * ULT
    m = Fs / 2 * (34 / 2 - 22 / 4)
    add("Shock hardware, bending (12.7 mm pin with the M8 bolt through it, treated as one solid steel section)", m / (np.pi * 12.7 ** 3 / 32),
        STEEL_PIN_YIELD, "MPa", "simply supported, load spread over a 22 mm eyelet (eyelet width estimated); pin and bolt strength unverified")
    add("Shock bolt M8, double shear", Fs / (2 * np.pi * 8.0 ** 2 / 4), 0.58 * BOLT_129, "MPa", "ignores the clamped pin, which shares the shear")
    add("SM-001 / RK-001 ears, M8 bolt bearing (7075, 2 x 8 mm)", Fs / (2 * 8.0 * 8.0), 1.5 * AL["yield_"], "MPa", "bearing yield taken as 1.5 x tensile yield")
    add("SM-001 ears, shear-out (2 ears x 2 planes x 8 x 10 mm)", Fs / (4 * 8 * 10.0), AL["shear"], "MPa", "")
    add("SM-001 seat, bearing on the carbon pocket floor (about 1500 mm2)", Fs * 0.99 / 1500.0, CARBON_BEARING_ALLOW, "MPa",
        "seat is square to the shock axis at mid travel", "estimated")
    add("SM-001 seat, shear on the pocket wall (46 x 6 mm) from the shock's +/-6 deg swing", Fs * np.sin(np.radians(6.5)) / (46 * 6.0),
        CARBON_BEARING_ALLOW, "MPa", "two M6 bolts and the bond act in addition", "estimated")
    # rocker: plates clamp a 17 mm Ti axle that turns in two GGB 1720DU bushes inside a sleeve bonded through the seat mast
    Fr = loads["rocker"] * ULT
    add("AX-002 rocker axle, bending at the plate clamp (17/11 mm Ti, 5 mm from the bush edge)", (Fr / 2) * 5.0 / tube_z(17, 11), TI["yield_"], "MPa",
        "axle turns in the mast; the plates clamp its ends")
    add("AX-002 rocker axle, shear", (Fr / 2) / (np.pi * (17 ** 2 - 11 ** 2) / 4), TI["shear"], "MPa", "")
    add("Rocker bushes 2 x GGB 1720DU, pressure at limit (17 x 40 mm)", loads["rocker"] / (17 * 40.0), DU_DYNAMIC, "MPa", "dynamic rating")
    add("Rocker bushes, pressure at ultimate", Fr / (17 * 40.0), DU_STATIC, "MPa", "static rating")
    add("Rocker bush sleeve bearing on the carbon mast boss (24 x 52 mm)", Fr / (24 * 52.0), CARBON_BEARING_ALLOW, "MPa", "", "estimated")
    # push links: two 7075 links 16 x 11 mm, 130 mm eye to eye, GGB 1210DU bush in each eye, 12 mm Ti pins
    Fl = loads["link"] * ULT / 2
    add("LK-001 push link, column buckling (7075, 16 x 11 mm, 130 mm)", Fl, np.pi ** 2 * 71700 * (16 * 11 ** 3 / 12) / 130 ** 2, "N", "Euler, pinned ends")
    add("LK-001 push link, compressive stress", Fl / (16 * 11.0), AL["yield_"], "MPa", "")
    add("Link bushes GGB 1210DU, pressure at limit (12 x 10 mm)", loads["link"] / 2 / (12 * 10.0), DU_DYNAMIC, "MPa", "dynamic rating")
    add("Link pins, double shear (12 mm Ti)", Fl / (2 * np.pi * 36.0), TI["shear"], "MPa", "")
    # main pivot: 20/14 mm Ti axle clamped in the frame sleeve; drive-side eye on one GGB 2015DU, non-drive eye on one 2030DU
    Fb = loads["pivot_bearing"] * ULT
    add("AX-001 main pivot axle, bending at the frame sleeve (20/14 mm Ti, drive-side arm 9.75 mm)", Fb * 9.75 / tube_z(20, 14), TI["yield_"], "MPa",
        "per-side force with the side-load couple taken on a 76 mm base (the eyes are 85 mm apart)")
    add("Main pivot drive-side bush GGB 2015DU, pressure at limit (20 x 15 mm)", loads["pivot_bearing"] / (20 * 15.0), DU_DYNAMIC, "MPa", "dynamic rating")
    add("Main pivot drive-side bush, pressure at ultimate", Fb / (20 * 15.0), DU_STATIC, "MPa", "static rating")
    add("Main pivot sleeve bearing on the carbon boss (26 x 58 mm)", loads["pivot"] * ULT / (26 * 58.0), CARBON_BEARING_ALLOW, "MPa", "", "estimated")
    add("Drive-side swingarm eye, bush housing bearing on carbon (27 mm sleeve x 15.5 mm)", Fb / (27 * 15.5), CARBON_BEARING_ALLOW, "MPa",
        "the lug is close to solid laminate here; shell results are indicative only", "estimated")
    # head tube: bearing cups seat directly in the carbon bore (S.H.I.S. ZS56, 11.5 mm cup insertion)
    add("Lower headset seat, bearing on carbon (55.9 x 11.5 mm)", loads["ht_lower"] * ULT / (55.9 * 11.5), CARBON_BEARING_ALLOW, "MPa", "", "estimated")
    add("Upper headset seat, bearing on carbon (55.9 x 11.5 mm)", loads["ht_upper"] * ULT / (55.9 * 11.5), CARBON_BEARING_ALLOW, "MPa", "", "estimated")
    add("BB-001 sleeve bearing on carbon (42 x 83 mm)", loads["feet"] * ULT / (42 * 83.0), CARBON_BEARING_ALLOW, "MPa", "", "estimated")
    Fd = loads["dropout"] * ULT
    add("Dropout insert, axle bearing (7075, 12.5 mm thick, 20 mm bore: SRAM UDH interface)", Fd / (20 * 12.5), 1.5 * AL["yield_"], "MPa", "")
    add("Dropout insert bond shear (3600 mm2 each, also wrapped by the spar laminate)", Fd / 3600.0, BOND_ALLOW, "MPa", "average shear", "estimated")
    # idler: 16 mm Ti stub cantilevered 11 mm from the mid-plane of the 8 mm carrier plate on the three ISCG tabs
    if d is not None:
        ist = idler_statics(d, loads["chain_tension"])
        Fi, bolt = ist["force"] * ULT, ist["bolt"] * ULT
        how = "statics of the two chain runs, %d-tooth cog; sprint load of 2.0 kN on one pedal" % ist["cog"]
    else:
        Fi = loads["idler"] * ULT; bolt = Fi / 3 + Fi * 105.0 / (3 * 36.5)
        how = "upper bound: whole idler force taken as tangential at 105 mm from the BB"
    add("ID-002 idler stub, bending at the carrier face (16 mm Ti, chain plane 7 mm from the face)", Fi * 7.0 / (np.pi * 16 ** 3 / 32), TI["yield_"], "MPa", how)
    add("ID-003 carrier plate, bending out of its plane (8 mm 7075, about 30 mm wide at the idler, 11 mm offset)", Fi * 11.0 / (30.0 * 8.0 ** 2 / 6),
        AL["yield_"], "MPa", "", "estimated")
    add("ID-003 ISCG bolts M6 class 12.9, shear (direct share plus the moment about the BB over a 73 mm bolt circle)", bolt, 0.58 * BOLT_129 * 20.1, "N",
        how + "; direct and moment shares added arithmetically", "estimated")
    add("BB-001 ISCG tabs, M6 bearing in 7075 (5 mm tab)", bolt / (6.0 * 5.0), 1.5 * AL["yield_"], "MPa", "same bolt force", "estimated")
    add("Rear brake post-mount bosses, M6 thread pull-out (12 mm engagement in a 7075 insert)", 4300.0 * ULT / 2,
        0.58 * AL["ult"] * np.pi * 5.0 * 12.0 * 0.5, "N", "caliper force for 1.2 kN at the tyre on a 220 mm rotor; mount position not yet modelled", "estimated")
    return rows


def mass_budget_v6(ft_laminate, sa_laminate, cad):
    """Frame mass per the G2 definition (kg), taken line by line from the bill of materials (bom.py)."""
    import bom
    return bom.frame_mass_items(ft_laminate, sa_laminate, cad)
