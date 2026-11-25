"""Writes DESIGN_V6.md. Every number in a table is read from a result file; the narrative is fixed text."""
from __future__ import annotations
import os, sys, json, csv
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import suspension as S, designs
import cad_model as C

ROOT = os.path.join(os.path.dirname(__file__), "..")
s = json.load(open(os.path.join(ROOT, "results", "summary.json")))
V6, V5 = s["revisions"]["V6"], s["revisions"]["V5"]
cl = json.load(open(os.path.join(ROOT, "results", "V6", "clearance_3d.json")))
mb = json.load(open(os.path.join(ROOT, "results", "V6", "mesh_and_buckling.json")))
bf = json.load(open(os.path.join(ROOT, "results", "V6", "as_first_packaged.json")))
bom = list(csv.reader(open(os.path.join(ROOT, "mfg", "BOM_V6.csv"))))
zones = list(csv.reader(open(os.path.join(ROOT, "mfg", "laminate_zones_V6.csv"))))
d = designs.v6()
names = {"LC1": "Hard braking into a compression", "LC2a": "Bottom-out landing, rider centred", "LC2b": "Bottom-out landing, weight back",
         "LC2c": "Bottom-out landing, weight forward", "LC2d": "Front wheel cases a knuckle", "LC3": "Sideways landing",
         "LC3m": "Sideways landing, from the other side", "LC4": "Cornering compression"}
o = []
w = o.append

# ------------------------------------------------------------------ numbers used in the text
ft_w, sa_w = V6["worst"]["front_triangle"], V6["worst"]["swingarm"]
ft_mesh = mb["front_triangle"]; sa_mesh = mb["swingarm"]
case_keys = [k for k in ft_mesh[next(iter(ft_mesh))] if k.startswith("LC")]
ft_hi = max(max(v[k] for k in case_keys) for v in ft_mesh.values())
sa_keys = [k for k in sa_mesh[next(iter(sa_mesh))] if k.startswith("LC")]
sa_hi = max(max(v[k] for k in sa_keys) for v in sa_mesh.values())
kin6, kin5 = V6["suspension"]["kin"], V5["suspension"]["kin"]
st6 = V6["suspension"]["setup"]
tooth_gap = float(np.hypot(*d["idler"]["centre"]) - C.IF["ring_radius"][d["chainring"]] - (S.sprocket_radius(d["idler"]["teeth"]) + 3.2))
tooth_gap34 = float(np.hypot(*d["idler"]["centre"]) - C.IF["ring_radius"][34] - (S.sprocket_radius(d["idler"]["teeth"]) + 3.2))
joint_min = min(V6["joints"], key=lambda j: j["margin"])
buck = mb["buckling_multiplier_on_ultimate"]
buck_min = min(min(v.values()) for v in buck.values())
dev = cl["info"]["surface_deviation_mm"]

w("# V6: the frame as a 3-D assembly\n")
w("**Status: a detailed design, still on paper.** V6 is the first revision that exists as solid parts in one assembly, checked for clashes "
  "through the whole suspension travel and steering range, analysed again on the changed geometry, and documented for a prototype shop. "
  "It has **not** been built, tested, or reviewed by a qualified composite-structures engineer. It is not safe to ride.\n")
w("Labels as in the main report: **measured**, **simulated**, **calculated**, **estimated**, **unknown**. Coordinates: origin at the BB centre, "
  "x forward, y up, z to the rider's left, millimetres, suspension extended.\n")

w("## 1. What changed in one paragraph\n")
w(f"The hard points, geometry and suspension curve are those of V5. Everything around them changed, because V5 had only been checked in side view. "
  f"Putting real component envelopes into a 3-D assembly showed ten clashes or impossibilities (section 2). Fixing them made the swingarm narrower "
  f"than the analysis had assumed, and checking that exposed an error in my own structural model (section 3). After a redesign the result is: "
  f"front-triangle worst strain index **{ft_w['fi']:.2f}** (up to {ft_hi:.2f} across mesh sizes), swingarm **{sa_w['fi']:.2f}**"
  + (f" (up to {sa_hi:.2f})" if sa_hi - sa_w['fi'] >= 0.01 else "") + ", "
  f"lowest joint margin **{joint_min['margin']:+.0%}**, no clash anywhere in the travel and steering sweep, and a frame mass of **{V6['frame_mass']:.2f} kg** "
  f"(V5: {V5['frame_mass']:.2f} kg). Against the three goals the picture is the same as for V5, except that the mass figure moved the wrong way (section 9).\n")
w("![V6 assembly](results/figures/assembly_V6.png)\n")
w("![V6 pivot, linkage and idler](results/figures/assembly_V6_detail.png)\n")

w("## 2. What the 3-D check found wrong with V5\n")
w("| # | Finding | Why V5 missed it | Change in V6 |")
w("|---|---|---|---|")
rows = [
    ("The bulge of the BB core sat where the shock's air can has to be", "side view only; the core was an analysis primitive",
     "bulge removed; the lower seat mast widens toward the BB instead (72 mm at the BB, 52 mm above the pivot)"),
    ("The down tube's underside hung below the bottom of the head tube, in the path of the fork's lower crown", "fork not modelled",
     "down tube meets the head tube 62 mm up from its lower end (was 38) and tapers from 82 to 68 mm deep"),
    ("The shock's reservoir does not fit at the frame end", "RockShox publish the reservoir envelope only in a fit drawing; V5 used a plain cylinder",
     "shock turned round: air can at the frame, damper head and reservoir at the rocker, reservoir facing forward into the open triangle"),
    ("Carbon tabs for the lower shock mount cannot be laid up in the space left", "no solid model",
     "7075 fitting SM-001 seated in a pocket in the down-tube junction, bolted (2 × M6) and bonded; the shock load goes into the pocket floor in bearing"),
    ("A rocker straddling the seat mast collides with the damper head", "no solid model",
     "two rocker plates run outside the mast and step inward ahead of it; they clamp a 17 mm axle that turns in two bushes inside the mast"),
    ("Swingarm spars passed through the brake rotor and cassette near the axle", "spars were drawn 86 mm out but 22–30 mm wide with no rotor or cassette",
     "spars leave the dropouts outboard of the hub ends and only come inboard ahead of the rotor"),
    ("The chain ran through the upper spar, the yoke and the upright", "chain not modelled",
     "lower spar kept below the chain in every gear; on the drive side the upright and pivot eye stay inboard of the chain where it crosses them"),
    ("The crank-arm envelope I had assumed was far too narrow", "placeholder instead of the manufacturer's drawing",
     "SRAM's frame-fit profile for X01 DH cranks; the swingarm stays at least 6 mm inside it"),
    ("The idler had nothing to stand on: the chain passes over the pivot axis, so nothing can be mounted there outboard of the swingarm eye",
     "idler drawn as a point", "idler on an 8 mm plate (ID-003) bolted to ISCG 05 tabs that are part of the BB sleeve (BB-001); idler centre moved to (30.0, 100.5)"),
    ("Crowns: the head tube and headset need 141.9 mm between the fork crowns", "not checked", "inside the BoXXer's Tall-crown range (126.8–147 mm); the Short crown does not fit"),
]
for i, r in enumerate(rows, 1):
    w(f"| {i} | {r[0]} | {r[1]} | {r[2]} |")
w("")

w("## 3. What checking the swingarm found wrong with my analysis\n")
w("Three errors, all mine, all found in this revision. They matter more than any clash.\n")
b0, b1 = bf["surface"], bf["midplane"]
w(f"1. **The shell model sat on the wrong surface.** In V1–V5 the shell elements were placed on the modelled surface and given the laminate's "
  f"thickness, half of it outside that surface. Once the solid model is the tool surface, the laminate lies wholly inside it, so the analysed "
  f"sections were too big by one wall thickness. For wide tubes that is a few percent. For the narrow swingarm members it is not: "
  f"the first packaged V6 swingarm scored {max(b0['swingarm'].values()):.2f} with the shell on the surface and "
  f"**{max(b1['swingarm'].values()):.2f}** with the shell on the true mid-plane (limit 1.00), and its lateral stiffness fell from "
  f"{b0['swingarm_lateral_stiffness']} to {b1['swingarm_lateral_stiffness']} N/mm. The head tube went from {b0['head_tube_zone_LC2d']:.2f} to "
  f"**{b1['head_tube_zone_LC2d']:.2f}**: with a 55.9 mm headset bore, the 66 mm tube I had analysed could not have had the wall I had given it (simulated).")
w("2. **The mid-plane was then placed too deep in flat sections**, because the distance function I used for elliptical tubes is exact only "
  "across the narrow direction. Replaced with a first-order-accurate one (mean error 0.1 mm against brute force).")
w("3. **A waypoint added to one spar broke the model.** Tube segments have square ends, so a bend in a spar leaves a notch. One such notch on the "
  "drive-side strut made the result three times worse than the same strut without the waypoint. I removed the waypoint. The remaining bends "
  "are gentle, but this is a weakness of how the geometry is built, and section 8 lists it.\n")
w("**What this means for V1–V5.** Their numbers describe parts whose outside is half a wall thickness larger than the surfaces in "
  "`cad/*_V5.stl`. They remain a fair record of the idealised study, but V5 is not a buildable design and its swingarm would not have fitted the bike.\n")
w("**The redesign that followed.**\n")
w("- Swingarm made **asymmetric**. The drive side is boxed in between the seat mast and the chain at the pivot (15.5 mm of width). "
  "The non-drive side has no chain, so its pivot eye is 31 mm wide and its upright and strut are 26–31 mm wide.")
w("- Lower spars widened to 27–31 mm where the tyre and crank allow; upper spars to 20–22 mm; the yoke lengthened from 20 to 26 mm; "
  "the strut now continues the lower spar's line into the pivot eye.")
w("- Swingarm laminate: spars 22 plies (3.48 mm), pivot eyes, lugs and dropouts 32 plies (5.00 mm), yoke junction 36 plies (5.60 mm).")
w("- Head tube 70.8 mm outside diameter with a 7.4 mm wall (48 plies). Rocker boss enlarged to hold its bush sleeve.")
w("- An asymmetric swingarm has to take the side load from either side, so the sideways landing is now run both ways (LC3 and LC3m).\n")

w("## 4. Parts\n")
w("| Part | Description | Qty | Material | Mass each (g) | Mass basis | Status |")
w("|---|---|---|---|---|---|---|")
for r in bom[1:]:
    if r[0] == "-":
        continue
    w(f"| {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[6]} | {r[7]} | {r[9]} |")
w(f"| | **Frame mass by the goal G2 definition** | | | **{1000*V6['frame_mass']:.0f}** | ±12 % → {0.88*V6['frame_mass']:.2f}–{1.12*V6['frame_mass']:.2f} kg | |")
w("\nBought-in and not counted: " + bom[-1][2] + ".\n")
w("Why metal where it is metal: pivots, pins and bolted seats need hard, accurate, wear-resistant surfaces and threads, which laminate cannot give. "
  "Each aluminium part is isolated from the carbon by a glass ply (galvanic corrosion). Bushes instead of ball bearings because the main pivot sees "
  f"{V6['interface_limit_forces']['pivot_bearing']/1e3:.1f} kN per side at limit load, three times the static rating of a ball bearing that would fit.\n")

w("## 5. Geometry and suspension\n")
g = V6["geometry"]
w(f"Unchanged from V5: reach {g['reach']:.0f} mm, stack {g['stack']:.1f} mm, head angle {g['head_angle']:.1f}°, rear centre {g['chainstay_length_static']:.0f} mm, "
  f"wheelbase {g['wheelbase']:.0f} mm, {g['rear_travel']:.0f} mm rear travel, leverage ratio {V6['suspension']['lr_start']:.2f} → {V6['suspension']['lr_end']:.2f}, "
  f"{st6['pressure_psi']:.0f} psi at 25 % sag with 2 tokens. The goal-G1 numbers are therefore the same as V5's.\n")
w("The idler moved, which changes the chain effects (calculated, at sag, 32-tooth ring and 17-tooth cog):\n")
w("| | V5 | V6 |"); w("|---|---|---|")
w(f"| Idler centre | ({designs.v5()['idler']['centre'][0]:.1f}, {designs.v5()['idler']['centre'][1]:.1f}) | ({d['idler']['centre'][0]:.1f}, {d['idler']['centre'][1]:.1f}) |")
w(f"| Anti-squat | {kin5['anti_squat']:.0f} % | {kin6['anti_squat']:.0f} % |")
w(f"| Anti-rise | {kin5['anti_rise']:.0f} % | {kin6['anti_rise']:.0f} % |")
w(f"| Change in length of the upper chain run, top-out to bottom-out | {kin5['chain_growth_total']:+.1f} mm | {kin6['chain_growth_total']:+.1f} mm "
  f"({'the run gets shorter, so the suspension does not pull on the pedals; the derailleur takes up the slack' if kin6['chain_growth_total'] < 0 else 'growth'}) |".replace("-", "−"))
w(f"| Gap between idler teeth and chainring teeth | not checked | {tooth_gap:.1f} mm with a 32-tooth ring; {tooth_gap34:.1f} mm with 34, so 32 is the largest ring |")
w("")

w("## 6. Clearances measured on the solid model\n")
w("Minimum distance between solids over nine travel positions (0 to 200 mm in 25 mm steps), and for the fork at 0, 20 and 40° of steering "
  "at both ends of its travel (calculated on the solid model). Designed joints are excluded inside a small radius around the joint axis. "
  "The right-hand column says how good the other part's envelope is.\n")
w("| Pair | Minimum (mm) | Where | My rule (mm) | Verdict | Envelope of the other part |")
w("|---|---|---|---|---|---|")
tm, stc = cl["travel_min"], cl["static"]
def row(label, val, where, rule, basis, note=""):
    verdict = "ok" if val >= rule else ("marginal" if val >= rule - 0.5 else "**too close**")
    w(f"| {label} | {val:.1f} | {where} | {rule:.0f} | {verdict}{note} | {basis} |")
T = lambda k: (tm[k]["min"], "at %s mm travel" % tm[k]["at"])
row("Rear tyre to swingarm", stc["rear_wheel - swingarm"], "fixed", 6, "64 mm wide, 712 mm diameter tyre: nominal size, estimated")
row("Rear tyre to seat mast", *T("rear_wheel - front_triangle"), 6, "as above")
row("Chain in the 24-tooth cog to swingarm", *T("swingarm - chain_24T"), 4, "cog positions estimated; chain envelope 8.2 × 8.8 mm")
row("Chain in the 10-tooth cog to swingarm", *T("swingarm - chain_10T"), 4, "as above")
row("Chain on the 32-tooth ring to swingarm", *T("swingarm - chainring"), 5, "SRAM chainring radius")
row("Crank arms to swingarm", *T("swingarm - crank_sweep"), 5, "SRAM X01 DH frame-fit profile less 1.5 mm for crank boots")
row("Cassette to swingarm", stc["cassette - swingarm"], "fixed", 3, "cog positions estimated")
row("220 mm rotor to swingarm", stc["rotor - swingarm"], "fixed", 3, "rotor plane estimated")
row("Swingarm to front triangle", *T("swingarm - front_triangle"), 4, "both modelled")
row("Rocker to front triangle", *T("rocker - front_triangle"), 4, "both modelled")
row("Push links to swingarm", *T("links - swingarm"), 4, "both modelled")
row("Push links to front triangle", *T("links - front_triangle"), 4, "both modelled")
row("Shock to front triangle", *T("shock - front_triangle"), 4, "RockShox fit drawing for the 2024 Vivid; **no drawing exists for the 2027 shock**")
row("Shock to rocker", *T("rocker - shock"), 4, "as above; damper-head size estimated")
row("Shock to swingarm", *T("swingarm - shock"), 4, "as above")
row("Shock to idler and its carrier", min(tm["shock - idler"]["min"], tm["shock - idler_carrier"]["min"]), "top-out", 4, "as above")
row("Idler carrier to the chain on the ring", stc["idler_carrier - chainring"], "fixed", 3, "SRAM chainline and ring position")
row("Idler carrier to crank arm", stc["idler_carrier - crank_sweep"], "fixed", 5, "SRAM profile")
row("Idler teeth to chainring teeth", tooth_gap, "fixed", 4, "calculated from tooth radii")
st = cl["steering"]
row("Fork crowns and upper tubes to frame, steering 0–20°", min(st[k]["fork_upper"] for k in st if not k.endswith("40")), "any fork travel", 4,
    "**crown outline and stanchion spacing estimated**; RockShox do not publish them")
row("Front tyre to down tube, fork bottomed", min(st[k]["front_wheel"] for k in st), "200 mm fork travel", 6, "nominal tyre")
w("")
w(f"- The push links run with 1.0 mm on each side inside the rocker's clevis: that is a designed running fit for thrust washers, not a clearance.")
w(f"- At 40° of steering the fork's bump stops are {min(st[k]['fork_upper'] for k in st if k.endswith('40')):.1f} mm from the frame, so steering lock is "
  f"about 40° each way and the frame needs pads where they land. The fork dimensions behind that number are estimates.")
w("- Anything within about a millimetre of its rule, and anything resting on an estimated envelope, has to be confirmed with the real parts in hand.")
w(f"- The analysed surface and the solid model are built from the same primitives but joined differently (smooth blends against plain unions). "
  f"Median gap between them {dev['median']:.1f} mm, 99 % within {dev['p99']:.1f} mm, largest {dev['max']:.0f} mm at junctions and at the pockets for the shock "
  f"fitting and BB flange, which the analysis does not have.\n")

w("## 7. Structure\n")
w("Same loads, limits and method as section 5 of `REPORT.md`, with the corrections of section 3: shell meshes on the laminate mid-plane; "
  "sideways landing from both sides for the swingarm.\n")
w("| Case | Front triangle: governing zone | Index | Mode | Swingarm: governing zone | Index | Mode |")
w("|---|---|---|---|---|---|---|")
for k in list(V6["front_triangle"]) + [x for x in V6["swingarm"] if x not in V6["front_triangle"]]:
    a = V6["front_triangle"].get(k); c = V6["swingarm"][k if k in V6["swingarm"] else "LC3"]
    fa = f"{a['zone']} | {a['fi']:.2f} | {a['mode']}" if a else "(symmetric part: same as LC3) | | "
    w(f"| {k} {names[k]} | {fa} | {c['zone']} | {c['fi']:.2f} | {c['mode']} |")
w("\nIndex = largest ply strain ÷ design limit at 1.5 × limit load, patch-averaged at the hot spot (simulated). 1.00 or less passes.\n")
w("![Front triangle, V5 and V6](results/figures/front_triangle_strain_index_V6.png)\n")
w("![Swingarm, V5 and V6](results/figures/swingarm_strain_index_V6.png)\n")
w("In these two figures the V5 panels come from the uncorrected model (shell on the modelled surface) and the V6 panels from the corrected one, "
  "so they show where the strain sits, not a like-for-like improvement.\n")
w("**Mesh check (simulated).** Governing index by case at three element sizes:\n")
w("| Part | Element size | Nodes | " + " | ".join(case_keys) + " | Laminate (kg) |"); w("|---|---|---|" + "---|" * (len(case_keys) + 1))
for h, v in ft_mesh.items():
    w(f"| Front triangle | {h[2:]} mm | {v['nodes']} | " + " | ".join(f"{v[k]:.2f}" for k in case_keys) + f" | {v['laminate_kg']:.3f} |")
w("")
w("| Part | Element size | Nodes | " + " | ".join(sa_keys) + " | Lateral stiffness (N/mm) |"); w("|---|---|---|" + "---|" * (len(sa_keys) + 1))
for h, v in sa_mesh.items():
    w(f"| Swingarm | {h[2:]} mm | {v['nodes']} | " + " | ".join(f"{v[k]:.2f}" for k in sa_keys) + f" | {v['lateral_stiffness_N_per_mm']} |")
w("")
ft_sp = max(max(v[k] for v in ft_mesh.values()) - min(v[k] for v in ft_mesh.values()) for k in case_keys)
sa_sp = max(max(v[k] for v in sa_mesh.values()) - min(v[k] for v in sa_mesh.values()) for k in sa_keys)
w(f"The values move by up to {ft_sp:.2f} (front triangle) and {sa_sp:.2f} (swingarm) between meshes without a clear trend: that is the numerical noise "
  f"of the hot-spot measure. Read the front triangle's worst case as **{ft_hi:.2f}** and the swingarm's as **{sa_hi:.2f}**, not as the single values in the table above. "
  f"At the finest mesh the front triangle's worst point is on the seat mast beside the rocker boss, where the rocker's {V6['interface_limit_forces']['rocker']/1e3:.0f} kN reaction "
  f"enters through a rigid ring in the model. A local pad of six extra plies there barely moved it (0.93 to 0.91) and raised another case, so I left it out. "
  f"The margin there is thin, and that joint is the first thing a detailed analysis or a test should look at.\n")
w(f"**Buckling (simulated).** Lowest linear buckling load ÷ ultimate load: " +
  "; ".join(f"{part}: " + ", ".join(f"{k} {v:.1f}" for k, v in vals.items()) for part, vals in buck.items()) +
  f". Smallest {buck_min:.1f}; anything above about 2 leaves room for the usual knock-down on linear shell buckling.\n")
w("**Joints and hardware at ultimate load (calculated).**\n")
w("| Check | Demand | Capacity | Unit | Margin | Basis |"); w("|---|---|---|---|---|---|")
for j in sorted(V6["joints"], key=lambda j: j["margin"]):
    w(f"| {j['item']} | {j['demand']:.0f} | {j['capacity']:.0f} | {j['unit']} | {j['margin']:+.0%} | {j['kind']}{'; ' + j['note'] if j['note'] else ''} |")
w("")
w("**Laminate by zone** (areas are mid-plane areas from the analysis meshes; full stacks in `mfg/ply_book_V6.csv`):\n")
w("| " + " | ".join(zones[0]) + " |"); w("|" + "---|" * len(zones[0]))
for r in zones[1:]:
    w("| " + " | ".join(r) + " |")
w("")

w("## 8. What is still not designed, not known, or only estimated\n")
w("Before tooling:\n")
w("1. **Rear brake mount.** The SRAM post-mount pattern is specified, but its position on the swingarm and the caliper's clearance are not designed. "
  "I had no caliper envelope and the gap between the spars at the rotor is too small for a caliper, so it has to sit above the upper spar or below the lower one.")
w("2. **Drive-side pivot lug.** 15.5 mm wide with 5 mm walls: close to solid laminate. A thin-shell model is a poor description of it. "
  "It needs a solid-element analysis or an element test, and it is where I would expect the first surprise.")
w("3. **Production surfacing.** Only three junction fillets exist in the solid model, and spar bends are stepped. Blending adds material where clearances are already 4–6 mm.")
w("4. **RockShox dimensions that are not published:** fork crown outline and stanchion spacing (steering lock and crown clearance rest on estimates), "
  "and the 2027 Vivid's reservoir (the model uses the 2024 drawing).")
w("5. **Estimated component positions:** cassette cogs, rotor plane, tyre and rim section. SRAM's UDH clearance model has not been checked against the dropout.")
w("6. **Chain management below the BB.** With an idler above the ring the chain needs a lower guide or tensioner. Not designed. The lower chain run and the derailleur were not modelled.")
w("7. **Idler carrier and ISCG tabs** are sized by hand calculation, with the tab offset assumed flush with the BB shell face.")
w("8. Cable and hose routing, frame protection, bump-stop pads, seat clamp, drain holes, pocketing of the machined parts.")
w("9. **Bush life and friction.** DU bushes pass on pressure; their wear life under dust and their breakaway friction against an air shock at 68 kg are unknown.")
w("\nAnd everything in section 9 of `REPORT.md` still applies: the loads, the laminate limits and the air-spring curve are estimates.\n")

w("## 9. Effect on the comparison with the Sender CFR and Supreme DH V5\n")
g3 = s["g3"]
w("| Goal | V5 | V6 | What changed |"); w("|---|---|---|---|")
w(f"| G1 rear-wheel force curve | mid ratio {V5['suspension']['setup']['mid_ratio']:.2f}, end ratio {V5['suspension']['setup']['end_ratio']:.2f}, "
  f"{V5['suspension']['setup']['drop_height']:.2f} m, {V5['suspension']['setup']['pressure_frac']:.0%} of max pressure | "
  f"mid ratio {st6['mid_ratio']:.2f}, end ratio {st6['end_ratio']:.2f}, {st6['drop_height']:.2f} m, {st6['pressure_frac']:.0%} | nothing: same linkage |")
w(f"| G2 frame mass, all checks passing | {V5['frame_mass']:.2f} kg | **{V6['frame_mass']:.2f} kg** (±12 %: {0.88*V6['frame_mass']:.2f}–{1.12*V6['frame_mass']:.2f}) | "
  f"heavier: real hardware (BB sleeve with tabs, shock fitting, idler carrier, un-pocketed rocker) and a thicker head tube and swingarm, partly offset by laminate areas now taken at the mid-plane |")
w(f"| G3 head-tube loading per kN at the front wheel | {g3['custom']['moment_Nm']:.0f} N m, {g3['custom']['upper_bearing_kN']:.2f} kN | same | nothing: same fork, head angle and head-tube length |")
w("")
sender = 4.614
w(f"- **G2 against the Sender CFR (4.614 kg claimed):** V6 is {V6['frame_mass'] - sender:+.2f} kg, {(V6['frame_mass']/sender - 1):+.0%}, with a ±12 % band on my figure. "
  f"**No advantage; if anything a small disadvantage, and inconclusive either way.**")
w(f"- **G2 against the Supreme DH V5 (5.3 kg claimed):** V6 is {(V6['frame_mass']/5.3 - 1):+.0%}. My upper bound is {1.12*V6['frame_mass']:.2f} kg, "
  f"{'below' if 1.12*V6['frame_mass'] < 5.3 else 'not below'} 5.3 kg, so by the rule fixed at the start this "
  f"{'counts as an advantage only if Commencal’s figure excludes the shock, which they do not state' if 1.12*V6['frame_mass'] < 5.3 else 'is **inconclusive**: the band reaches the Supreme’s figure'}.")
w("- **G1 and G3:** unchanged from the main report. G3 (17–23 % lower upper-bearing force) is still the firmest result, and still a geometry metric, not a strength comparison.")
w(f"- **Stiffness:** the swingarm's lateral stiffness at the axle is {V6['swingarm_lateral_stiffness']:.0f} N/mm (simulated). V5's 621 N/mm came from the uncorrected model and "
  "a swingarm that would not have fitted, so the two are not comparable, and neither maker publishes a figure.")
w("- **What the production bikes still have that this does not:** they exist, with a brake mount, cable routing and chain guide, and they have been ridden and lab-tested.\n")

w("## 10. Files added in V6\n")
w("| Path | Contents |"); w("|---|---|")
for a, b_ in [("`cad/V6/parts/*.step`", "one STEP solid per frame part (carbon parts are tool surfaces)"),
              ("`cad/V6/assembly_topout.step`, `assembly_sag.step`, `assembly_bottomout.step`", "the whole assembly with fork, shock, wheels, cranks, chain, rotor and cassette envelopes, at three suspension positions"),
              ("`mfg/ply_book_V6.csv`, `mfg/laminate_zones_V6.csv`", "every ply of every zone; zone areas, thicknesses and masses"),
              ("`mfg/BOM_V6.csv`", "bill of materials with mass basis and status per line"),
              ("`mfg/interface_control_V6.md`", "datums, hard points, fits, tolerances (sourced values and my proposals marked separately)"),
              ("`mfg/manufacturing_notes_V6.md`", "tooling concept, lay-up rules, cure cycle, bonding, inspection"),
              ("`sources/interfaces.md`", "the manufacturers' interface drawings and what could not be found"),
              ("`results/V6/clearance_3d.json`", "every clearance at every travel position"),
              ("`results/V6/mesh_and_buckling.json`, `results/V6/as_first_packaged.json`", "mesh-size and buckling checks; the before/after of the mid-plane correction"),
              ("`src/cad_model.py`, `run_v6_cad.py`, `clear_fast.py`, `bom.py`, `run_v6_checks.py`, `make_v6_package.py`, `make_v6_doc.py`", "solid model, clearance study, fast clearance estimate for design iterations, BOM, checks, package and this document")]:
    w(f"| {a} | {b_} |")
w("\nReproduce: `python3 src/run_v6_cad.py` (solid model and clearances, about 10 min), `python3 src/run_all.py`, `python3 src/run_v6_checks.py`, "
  "`python3 src/make_v6_package.py`, `python3 src/make_v6_doc.py`. Needs build123d 0.13 (OpenCascade) in addition to the packages listed in `REPORT.md`.\n")

open(os.path.join(ROOT, "DESIGN_V6.md"), "w").write("\n".join(o))
print("DESIGN_V6.md written,", len(o), "lines")
