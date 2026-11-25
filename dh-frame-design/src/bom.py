"""Bill of materials for V6. One list feeds both the frame-mass figure in results/summary.json and mfg/BOM_V6.csv."""
from __future__ import annotations
import numpy as np

HEADER = ["item", "part no.", "description", "qty", "material", "process", "mass each g", "mass basis", "CAD file / standard", "status"]


def rows(ft_laminate_kg, sa_laminate_kg, cl):
    """cl = part masses in kg from the solid model (results/V6/clearance_3d.json, info.masses_kg).
    Mass basis: 'model' = shell-model laminate or solid-model volume x density; 'estimate' = judgement."""
    g = lambda k: round(1000 * cl[k])
    tube = lambda do, di, L, rho: round(np.pi / 4 * (do ** 2 - di ** 2) * L * rho * 1e-3)
    AL, TI = "7075-T6, hard anodised", "Ti-6Al-4V (grade 5), annealed"
    rows = [HEADER,
        [1, "FT-001", "Front triangle (head tube, top tube, down tube, seat mast, BB and pivot bosses)", 1, "Toray T700G/2510 UD + T700S/2510 plain weave prepreg",
         "bladder-moulded in a two-part female tool, oven cure; see ply book", round(1080 * ft_laminate_kg), "model + 8 % overlaps",
         "cad/V6/parts/FT-001_front_triangle_OML.step (tool surface)", "analysed; tool surface needs production surfacing"],
        [2, "SA-001", "Swingarm, asymmetric (wide non-drive pivot eye)", 1, "same prepregs", "bladder-moulded, oven cure; see ply book",
         round(1080 * sa_laminate_kg), "model + 8 % overlaps", "cad/V6/parts/SA-001_swingarm_OML.step (tool surface)",
         "analysed; drive-side pivot lug needs solid-element analysis or test"],
        [3, "BB-001", "Bottom-bracket sleeve, 83 mm, BSA thread 1.37 in x 24 TPI, with integral ISCG 05 tabs", 1, AL, "CNC; bonded in with a glass isolation ply",
         g("bb_sleeve"), "model", "cad/V6/parts/BB-001_bb_sleeve_iscg.step; SRAM DUB BSA 83; ISCG 05", "modelled; tab face offset to be confirmed against the chain guide"],
        [4, "FT-INS-02", "Main pivot sleeve, 26 OD x 20 H7 bore x 58", 1, AL, "CNC; bonded in", tube(26, 20, 58, 2.81), "calculated", "bore shown in FT-001", "sized, not drawn"],
        [5, "FT-INS-03", "Rocker bush sleeve, 24 OD x 19 H7 bore x 62", 1, AL, "CNC; bonded in", tube(24, 19, 62, 2.81), "calculated", "bore shown in FT-001", "sized, not drawn"],
        [6, "SM-001", "Shock-mount fitting (air-can end of the shock), 30 mm between ears, M8", 1, AL, "CNC; bonded and bolted (2 x M6) into its pocket",
         g("shock_fitting"), "model", "cad/V6/parts/SM-001_shock_mount_fitting.step; RockShox 8 x 30 hardware", "modelled; bolt inserts not drawn"],
        [7, "SA-INS-01", "Dropout inserts, 157 mm spacing, drive side to the SRAM UDH specification", 2, AL, "CNC; co-moulded and bonded", 38, "estimate",
         "SRAM drawing 90-7518-190-000 Rev H", "not drawn; must be checked against SRAM's STEP clearance model"],
        [8, "SA-INS-02", "Pivot bush sleeves, 27 OD x 23 H7 bore (15.5 long drive side, 31 long non-drive side)", 2, AL, "CNC; bonded in",
         round((tube(27, 23, 15.5, 2.81) + tube(27, 23, 31, 2.81)) / 2), "calculated (average)", "bores shown in SA-001", "sized, not drawn"],
        [9, "SA-INS-03", "Rear brake post-mount bosses, 2 x M6, 74.2 mm spacing", 2, AL, "CNC; bonded and wrapped", 9, "estimate",
         "SRAM frame-fit specification (post mount, 200 mm rotor)", "OPEN: position and caliper clearance not designed"],
        [10, "RK-001", "Rocker plates, left and right", 2, AL, "CNC from plate", round(g("rocker") / 2), "model (not pocketed)", "cad/V6/parts/RK-001_rocker.step",
         "modelled; pocketing and fatigue check outstanding"],
        [11, "LK-001", "Push link, 16 x 11 section, about 130 mm between eyes", 2, AL, "CNC", round(g("links") / 2), "model", "cad/V6/parts/LK-001_push_links.step", "modelled"],
        [12, "AX-001", "Main pivot axle, 20 OD x 14 bore x 113.5 (longer on the non-drive side)", 1, TI, "turned and ground, f7 on the bush seats", g("main_axle"), "model",
         "cad/V6/parts/AX-001_main_pivot_axle.step", "modelled; end bolts not drawn"],
        [13, "AX-002", "Rocker axle, 17 OD x 11 bore x 90, clamps the two rocker plates", 1, TI, "turned and ground, f7", g("rocker_axle"), "model",
         "cad/V6/parts/AX-002_rocker_axle.step", "modelled; end bolts not drawn"],
        [14, "PIN-12", "Link pins, 12 f7", 4, TI, "turned and ground", 16, "estimate", "bores shown in SA-001, RK-001, LK-001", "sized, not drawn"],
        [15, "ID-001", "Idler sprocket, 14 teeth, narrow-wide, with sealed bearing", 1, "7075-T6 or steel", "purchased or CNC", g("idler") + 15, "model + bearing estimate",
         "cad/V6/parts/ID-001_idler_sprocket.step", "envelope only; bearing not selected"],
        [16, "ID-002", "Idler stub, 16 mm shoulder, M12 into the carrier", 1, TI, "turned", g("idler_stub"), "model", "cad/V6/parts/ID-002_idler_stub.step", "modelled"],
        [17, "ID-003", "Idler carrier plate, 8 mm, on the three ISCG 05 tabs", 1, AL, "CNC from plate", g("idler_carrier"), "model (not pocketed)",
         "cad/V6/parts/ID-003_idler_carrier.step", "modelled; outline indicative, lower chain guide not designed"],
        [18, "BUSH", "GGB DU plain bushes: 2 x 1720DU, 1 x 2015DU, 1 x 2030DU, 4 x 1210DU", 1, "steel-backed PTFE (GGB DU)", "purchased; pressed in, not reamed", 60, "estimate (set)",
         "GGB DU designer's handbook", "sizes exist in the catalogue; life not assessed"],
        [19, "HW", "Bolts and washers: 2 x M8 shock bolts, 3 x M6 ISCG bolts, 2 x M6 fitting bolts, axle end bolts, thrust washers", 1, "class 12.9 steel / Ti", "purchased", 120, "estimate (set)", "", ""],
        [20, "PROT", "Down-tube guard, spar and chain protection, fork bump-stop pads, paint", 1, "moulded rubber / PU film / paint", "bonded on", 250, "estimate (set)", "", "not designed"],
        ["-", "(bought-in, not frame mass)", "RockShox 8 x 30 shock hardware x 2; Cane Creek Forty ZS56/ZS56 headset (or +/-5 mm reach cups); SRAM DUB BSA 83 BB; SRAM UDH; "
         "12 x 157 rear axle; 31.6 mm seat post and clamp", "", "", "", "", "", "see sources/interfaces.md", ""]]
    return rows


def frame_mass_items(ft_laminate_kg, sa_laminate_kg, cl):
    """(description, kg, basis) per BOM line that counts toward frame mass, and the total in kg."""
    items = [("%s %s" % (r[1], r[2]) + (" (x%d)" % r[3] if r[3] != 1 else ""), r[3] * r[6] / 1000.0, r[7])
             for r in rows(ft_laminate_kg, sa_laminate_kg, cl)[1:] if isinstance(r[0], int)]
    return items, float(sum(v for _, v, _ in items))
