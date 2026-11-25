"""Writes REPORT.md tables from results/summary.json (numbers are never typed by hand into the tables)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
ROOT = os.path.join(os.path.dirname(__file__), "..")
s = json.load(open(os.path.join(ROOT, "results", "summary.json")))
R = s["revisions"]; V = R["V5"]; b = s["benchmarks_g1"]; g3 = s["g3"]
geo = V["geometry"]; kin = V["suspension"]["kin"]; st = V["suspension"]["setup"]; cl = V["suspension"]["clearances"]
names = {"LC1": "Hard braking into a compression", "LC2a": "Bottom-out landing, rider centred", "LC2b": "Bottom-out landing, weight back",
         "LC2c": "Bottom-out landing, weight forward", "LC2d": "Front wheel cases a knuckle", "LC3": "Sideways landing", "LC4": "Cornering compression"}
out = []
w = out.append

w("### Table A. Load cases: limit forces at the tyres and resulting interface forces (V5)\n")
w("| Case | Rear tyre x / y / z (kN) | Front tyre x / y / z (kN) | Hands x / y (kN) | Feet at BB x / y / z (kN) | BB moment roll / yaw (N m) | Shock | Push links (total) | Main pivot | Rocker pivot | Head tube upper / lower bearing |")
w("|---|---|---|---|---|---|---|---|---|---|---|")
for k, c in V["case_forces"].items():
    f = lambda v: " / ".join(f"{x/1e3:.2f}" for x in v)
    w(f"| {k} {names[k]} | {f(c['rear'])} | {f(c['front'])} | {f(c['hands'][:2])} | {f(c['bb'][:3])} | {c['bb'][3]/1e3:.0f} / {c['bb'][4]/1e3:.0f} | {c['shock']/1e3:.1f} | {c['link']/1e3:.1f} | {c['pivot']/1e3:.1f} | {c['rocker']/1e3:.1f} | {c['ht_upper']/1e3:.1f} / {c['ht_lower']/1e3:.1f} |")
w("\nForces in kN at limit load; ultimate = 1.5 × these. The BB column is the support reaction (what the rider's feet must supply). "
  f"Largest difference between the finite-element support reaction and the independent whole-bike statics: {max(c['balance'] for c in V['case_forces'].values()):.1e} N.\n")

w("### Table B. Composite strain check at ultimate load, by load case (simulated)\n")
w("| Case | Front triangle: governing zone | Index | Margin | Mode | Swingarm: governing zone | Index | Mode |")
w("|---|---|---|---|---|---|---|---|")
for k in V["front_triangle"]:
    a, c = V["front_triangle"][k], V["swingarm"][k]
    w(f"| {k} | {a['zone']} | {a['fi']:.2f} | {a['ms']:+.0%} | {a['mode']} | {c['zone']} | {c['fi']:.2f} | {c['mode']} |")
w("\nIndex = largest ply strain ÷ design strain limit, at 1.5 × limit load, averaged over a 12 mm (front triangle) or 10 mm (swingarm) patch at the hot spot. ≤ 1.00 passes.\n")

w("### Table C. Joints, pins, bearings and bonded inserts at ultimate load (calculated, V5)\n")
w("| Check | Demand | Capacity | Unit | Margin | Basis |")
w("|---|---|---|---|---|---|")
for j in V["joints"]:
    w(f"| {j['item']} | {j['demand']:.0f} | {j['capacity']:.0f} | {j['unit']} | {j['margin']:+.0%} | {j['kind']}{'; ' + j['note'] if j['note'] else ''} |")
w("")

w("### Table D. Frame mass build-up (V5)\n")
w("| Item | kg | Basis |"); w("|---|---|---|")
for a, m_, c in V["mass_items"]:
    w(f"| {a} | {m_:.3f} | {c} |")
w(f"| **Total (goal G2 definition)** | **{V['frame_mass']:.2f}** | ±12 % → {0.88*V['frame_mass']:.2f}–{1.12*V['frame_mass']:.2f} kg |\n")

w("### Table E. Revision log\n")
w("| Rev | Leverage start → end | Pressure at 25 % sag | Mid-stroke ratio | End ratio | Spring drop height | Shock force at limit | Front triangle worst index | Swingarm worst index | Worst joint margin | Frame mass | All structural checks |")
w("|---|---|---|---|---|---|---|---|---|---|---|---|")
for n, r in R.items():
    su = r["suspension"]; t = su["setup"]
    w(f"| {n} | {su['lr_start']:.2f} → {su['lr_end']:.2f} | {t['pressure_psi']:.0f} psi / {t['pressure_bar']:.1f} bar ({t['pressure_frac']:.0%} of max) | {t['mid_ratio']:.2f} | {t['end_ratio']:.2f} | {t['drop_height']:.3f} m | {r['interface_limit_forces']['shock']/1e3:.1f} kN | {r['worst']['front_triangle']['fi']:.2f} ({r['worst']['front_triangle']['case']}, {r['worst']['front_triangle']['zone']}) | {r['worst']['swingarm']['fi']:.2f} ({r['worst']['swingarm']['case']}) | {r['worst']['joint_margin']:+.0%} | {r['frame_mass']:.2f} kg | {'pass' if r['structure_pass'] else 'FAIL'} |")
w("")

w("### Table F. Goal G1 with the same shock model and rule (25 % sag, 68 kg)\n")
w("| Bike | Leverage curve used | Tokens | Pressure | a. Force at 60 % ÷ W (2.3–2.8) | b. Force at 100 % ÷ W (≥ 6.5) | c. Spring drop height (≥ 0.50 m) | d. Pressure ÷ max (≤ 75 %) |")
w("|---|---|---|---|---|---|---|---|")
w(f"| Custom V5 and V6 (same linkage) | simulated from the hard points, {V['suspension']['lr_start']:.2f} → {V['suspension']['lr_end']:.2f} | 2 | {st['pressure_psi']:.0f} psi | {st['mid_ratio']:.2f} | {st['end_ratio']:.2f} | {st['drop_height']:.3f} | {st['pressure_frac']:.0%} |")
lab = {"sender_32.7": "Sender CFR, 32.7 % chip", "sender_37": "Sender CFR, 37 % chip", "supreme": "Supreme DH V5"}
for k, v in b.items():
    w(f"| {lab[k]} | estimated, {v['lr'][0]:.2f} → {v['lr'][1]:.2f} | {v['tokens']} | {v['pressure_psi']:.0f} psi | {v['mid_ratio']:.2f} | {v['end_ratio']:.2f} | {v['drop_height']:.3f} | {v['pressure_frac']:.0%} |")
w("")
open(os.path.join(ROOT, "results", "report_tables.md"), "w").write("\n".join(out))

# ---- assemble REPORT.md from the template: tables are dropped in at their placeholders, headings become bold captions
import csv
text = "\n".join(out)
tables = {}
for block in text.split("### Table ")[1:]:
    letter = block[0]
    head, _, body = block.partition("\n\n")
    tables[letter] = "**Table " + head.strip() + "**\n" + body.strip() + "\n"
kin_rows = []
for r in csv.DictReader(open(os.path.join(ROOT, "results", "V5", "kinematics.csv"))):
    z = float(r["wheel_travel_mm"])
    if z in (0, 25, 50, 75, 100, 120, 150, 175, 190, 200):
        fast = "—" if z == 0 else f"{float(r['wheel_force_fast_N']):.0f} N"
        kin_rows.append(f"| {z:.0f} mm | {float(r['shock_stroke_mm']):.1f} mm | {float(r['leverage_ratio']):.2f} | {abs(float(r['axle_rearward_mm'])):.1f} mm | "
                        f"{max(float(r['wheel_force_slow_N']), 0) if z else 0:.0f} N | {fast} | {float(r['anti_rise_pct']):.0f} % | {float(r['anti_squat_pct']):.0f} % |")
rep = open(os.path.join(ROOT, "src", "report_template.md")).read()
rep = rep.replace("{{KIN_ROWS}}", "\n".join(kin_rows))
for letter in "ABCEF":
    rep = rep.replace("{{TABLE_%s}}" % letter, tables[letter])
# ---- V6 numbers for sections 0, 6 and 7
V6 = R["V6"]; st6 = V6["suspension"]["setup"]; k6 = V6["suspension"]["kin"]
clr = json.load(open(os.path.join(ROOT, "results", "V6", "clearance_3d.json")))
bf = json.load(open(os.path.join(ROOT, "results", "V6", "as_first_packaged.json")))
mb = json.load(open(os.path.join(ROOT, "results", "V6", "mesh_and_buckling.json")))
hi = lambda part: max(v2 for v in mb[part].values() for k2, v2 in v.items() if k2.startswith("LC"))
skip = ("links - rocker", "swingarm - main_axle")          # designed fits, not clearances
clr_min = min([v["min"] for k_, v in clr["travel_min"].items() if k_ not in skip] + list(clr["static"].values()))
M6, M5 = V6["frame_mass"], V["frame_mass"]
mhi = 1.12 * M6
pct = lambda x: f"{100 * x:+.0f} %".replace("-", "−")
def with_mesh(val, top):
    return f"{val:.2f}" + (f" (up to {top:.2f} across mesh sizes)" if top - val >= 0.01 else "")
vals = dict(
    MID=f"{st6['mid_ratio']:.2f}", END=f"{st6['end_ratio']:.2f}", END1=f"{st6['end_ratio']:.1f}", PFRAC=f"{st6['pressure_frac']:.0%}", DROP=f"{st6['drop_height']:.2f}",
    MASS=f"{M6:.2f}", MASS_LO=f"{0.88 * M6:.2f}", MASS_HI=f"{mhi:.2f}", MASS5=f"{M5:.2f}",
    G3_M=f"{g3['custom']['moment_Nm']:.0f}", G3_F=f"{g3['custom']['upper_bearing_kN']:.2f}",
    CLR_MIN=f"{clr_min:.1f}",
    BF_SA0=f"{max(bf['surface']['swingarm'].values()):.2f}", BF_SA1=f"{max(bf['midplane']['swingarm'].values()):.2f}",
    BF_K0=str(bf["surface"]["swingarm_lateral_stiffness"]), BF_K1=str(bf["midplane"]["swingarm_lateral_stiffness"]),
    BF_HT0=f"{bf['surface']['head_tube_zone_LC2d']:.2f}", BF_HT1=f"{bf['midplane']['head_tube_zone_LC2d']:.2f}",
    SA6=with_mesh(V6["worst"]["swingarm"]["fi"], hi("swingarm")), FT6=with_mesh(V6["worst"]["front_triangle"]["fi"], hi("front_triangle")),
    K6=f"{V6['swingarm_lateral_stiffness']:.0f}",
    AR6=f"{k6['anti_rise']:.0f}", AS6=f"{k6['anti_squat']:.0f}", CG6=f"{k6['chain_growth_total']:.1f}".replace("-", "−"),
    KB6=("−" if k6["chain_growth_total"] < 0 else "") + f"{k6['max_kickback_deg']:.1f}",
    D_SENDER=pct(M6 / 4.614 - 1), D_SUPREME=pct(M6 / 5.3 - 1),
    G2_SENDER=f"Sender CFR claims 4.61 kg: V6 is {pct(M6 / 4.614 - 1)} on paper, inside my ±12 % band: **no advantage shown**.",
    G2_SUPREME=(f"Supreme DH V5 claims 5.3 kg: lighter by the rule only if that figure excludes the shock, which Commencal does not state." if mhi < 5.3 else
                f"Supreme DH V5 claims 5.3 kg: V6 is {pct(M6 / 5.3 - 1)}, but my upper bound ({mhi:.2f} kg) reaches that figure, so by the rule fixed at the start: **inconclusive**."),
    G2_SUPREME_SHORT=("advantage only if 5.3 kg excludes the shock" if mhi < 5.3 else f"upper bound {mhi:.2f} kg is not below 5.3 kg: **inconclusive**"))
for k_, v_ in vals.items():
    rep = rep.replace("{{%s}}" % k_, v_)
assert "{{" not in rep, "unfilled placeholder in the report template"
open(os.path.join(ROOT, "REPORT.md"), "w").write(rep)
print("REPORT.md written,", len(rep.splitlines()), "lines")
