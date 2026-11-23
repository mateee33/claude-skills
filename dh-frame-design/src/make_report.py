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
w(f"| Custom V5 | simulated from the hard points, {V['suspension']['lr_start']:.2f} → {V['suspension']['lr_end']:.2f} | 2 | {st['pressure_psi']:.0f} psi | {st['mid_ratio']:.2f} | {st['end_ratio']:.2f} | {st['drop_height']:.3f} | {st['pressure_frac']:.0%} |")
lab = {"sender_32.7": "Sender CFR, 32.7 % chip", "sender_37": "Sender CFR, 37 % chip", "supreme": "Supreme DH V5"}
for k, v in b.items():
    w(f"| {lab[k]} | estimated, {v['lr'][0]:.2f} → {v['lr'][1]:.2f} | {v['tokens']} | {v['pressure_psi']:.0f} psi | {v['mid_ratio']:.2f} | {v['end_ratio']:.2f} | {v['drop_height']:.3f} | {v['pressure_frac']:.0%} |")
w("")
open(os.path.join(ROOT, "results", "report_tables.md"), "w").write("\n".join(out))
print("\n".join(out)[:600]); print("...written", len(out), "lines")
