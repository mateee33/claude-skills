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
