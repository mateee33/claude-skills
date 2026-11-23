"""Suspension analysis for one design revision. Writes tables and plots to results/<name>/."""
from __future__ import annotations
import sys, os, json, csv
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from geometry import frame_geometry
from kinematics import Linkage, interp_pose
from layout import structure_lines, signed_height, dist_point_segment
import suspension as S
import benchmarks as B
from airspring import calibrated, MAX_PRESSURE_PSI
from draw import draw_side, INK, MUTED, ACCENT, ACC2, GRID

C3 = "#1d4ed8"


def geometry_table(d, g, sw):
    L = structure_lines(d, g)
    tt0, tt1 = L["top_tube"]
    def tt_top(x):
        t = (x - tt0[0]) / (tt1[0] - tt0[0])
        ang = np.arctan2(tt1[1] - tt0[1], tt1[0] - tt0[0])
        return tt0[1] + t * (tt1[1] - tt0[1]) + d["top_tube_depth"] / 2 / np.cos(ang)
    mid = 0.5 * (tt0[0] + tt1[0])
    m0, m1 = L["seat_mast"]
    q_sag = interp_pose(sw, d["sag_frac"] * sw["travel"][-1])
    q_bo = interp_pose(sw, sw["travel"][-1])
    eff_sta = np.degrees(np.arctan2(m1[1], -m1[0]))
    return dict(
        reach=d["reach"], stack=d["stack"], head_angle=d["head_angle"],
        head_tube_length=g["head_tube_len"], wheelbase=g["wheelbase"], front_centre=g["front_centre"],
        rear_centre_static=g["rear_centre_h"], chainstay_length_static=float(np.hypot(*g["rear_axle"])),
        rear_centre_at_sag=float(-q_sag["A"][0]), rear_centre_at_bottom_out=float(-q_bo["A"][0]),
        bb_height=d["bb_height"], bb_drop=float(g["front_axle"][1]),
        trail=g["trail"], standover_at_bb=float(tt_top(0.0) - g["ground_y"]),
        standover_mid_top_tube=float(tt_top(mid) - g["ground_y"]),
        seat_tube_length=float(np.hypot(*m1)), seat_tube_angle_effective=float(eff_sta),
        seat_tube_angle_actual=float(np.degrees(np.arctan2(m1[1] - m0[1], -(m1[0] - m0[0])))),
        rear_travel=float(sw["travel"][-1]), front_travel=d["fork_travel"],
        crown_stack_needed=g["head_tube_len"] + d["lower_headset_stack"] + d["upper_headset_stack"])


def clearances(d, g, sw):
    L = structure_lines(d, g)
    m0, m1 = L["seat_mast"]; dt0, dt1 = L["down_tube"]; tt0, tt1 = L["top_tube"]
    P = np.asarray(d["pts"]["P"], float); M = np.asarray(d["pts"]["M"], float)
    rr = d["rear_tyre_radius"]
    out = {}
    tyre_mast = min(dist_point_segment(a, m0, m1) for a in sw["A"]) - rr - d["seat_mast_depth"] / 2
    out["rear tyre to seat-mast rear face, min over travel (centre plane)"] = tyre_mast
    out["rear tyre to seat-tube top, min over travel"] = min(np.linalg.norm(a - m1) for a in sw["A"]) - rr
    can_r = 29.0
    def seg_seg_min(K):
        ts = np.linspace(0, 1, 40)
        pts = M + ts[:, None] * (K - M)
        return pts
    d_mast = min(min(dist_point_segment(p, m0, m1) for p in seg_seg_min(K)) for K in sw["K"][::10]) - d["seat_mast_depth"] / 2 - can_r
    out["shock air can to seat-mast front face, min over travel"] = d_mast
    d_piv = min(dist_point_segment(P, M, K) for K in sw["K"][::10]) - 24.0 - can_r
    out["shock air can to main-pivot housing (24 mm radius), min over travel"] = d_piv
    tt_ang = np.arctan2(tt1[1] - tt0[1], tt1[0] - tt0[0])
    k_tt = min(-signed_height(K, tt0, tt1) for K in sw["K"]) - d["top_tube_depth"] / 2 - 15.0
    out["shock eye (15 mm radius) to top-tube underside, min over travel"] = k_tt
    out["shock mount M above down-tube surface"] = signed_height(M, dt0, dt1) - d["down_tube_depth"] / 2
    out["link/rocker rear arm lateral position needed to clear tyre (|z|, mm)"] = d["tyre_width"] / 2 + 8 + 6
    q = interp_pose(sw, sw["travel"][-1])
    out["tyre top above BB at bottom-out (saddle underside must stay above this + 15)"] = q["A"][1] + rr
    return out


def steering_lock(d, stanchion_cc=160.0, stanchion_fwd=28.0, stanchion_r=19.0, tube_half_width=30.0, bumper_r=30.0, lock=40.0):
    """ESTIMATED: crown dimensions are not in RockShox documentation."""
    rho = np.hypot(stanchion_fwd, stanchion_cc / 2)
    th0 = np.degrees(np.arctan2(stanchion_cc / 2, stanchion_fwd))
    contact = 180 - np.degrees(np.arcsin((tube_half_width + stanchion_r) / rho)) - th0
    z_block = rho * np.sin(np.radians(th0 + lock)) - bumper_r
    x_block = rho * np.cos(np.radians(th0 + lock))
    return dict(contact_angle_without_stops_deg=contact, stop_block_face_z_mm=z_block, stop_block_x_behind_axis_mm=-x_block,
                lock_deg=lock, assumed=dict(stanchion_cc=stanchion_cc, stanchion_fwd=stanchion_fwd))


def benchmark_g1(sag_frac=0.25):
    """G1 metrics for the benchmark bikes with the same shock model and rule (ESTIMATED leverage curves)."""
    out = {}
    for key, bk, curve in (("sender_32.7", B.SENDER, B.SENDER["lr"]["curve"]), ("sender_37", B.SENDER, B.SENDER["lr_alt"]["curve"]),
                           ("supreme", B.SUPREME, B.SUPREME["lr"]["curve"])):
        sw = B.sweep_from_lr(bk["travel"], *curve)
        fc = bk["wheelbase"] - bk["rear_centre"]
        w = S.rear_static_load(fc, bk["wheelbase"])
        best = None
        for tok in range(5):
            st = S.setup(sw, w, sag_frac, tok, travel=bk["travel"])
            sc = S.g1_score(st)
            n = sum(bool(v) for v in sc.values())
            if best is None or n > best[0]:
                best = (n, tok, st, sc)
        n, tok, st, sc = best
        out[key] = dict(name=bk["name"], lr=curve, stroke_check=float(sw["stroke"][-1]), w_rear=w, tokens=tok, pressure_psi=st["pressure_psi"],
                        pressure_frac=st["pressure_frac"], mid_ratio=st["mid_ratio"], end_ratio=st["end_ratio"],
                        drop_height=st["drop_height"], energy_J=st["energy_J"], checks=sc, z=st["z"], f=st["f"])
    return out


def run(d, outdir):
    os.makedirs(outdir, exist_ok=True)
    g = frame_geometry(d)
    d["pts"]["A"] = tuple(float(v) for v in g["rear_axle"])
    lk = Linkage(d["pts"], d["shock_stroke"]); sw = lk.sweep(n=401)
    assert sw["ok"], "linkage does not reach full stroke"
    geo = geometry_table(d, g, sw)
    rows = S.kinematic_table(d, g, sw, nz=41)
    w = S.rear_static_load(g["front_centre"], g["wheelbase"])
    setups = {tok: S.setup(sw, w, d["sag_frac"], tok) for tok in range(5)}
    st = setups[d["tokens"]]
    res = dict(name=d["name"], geometry=geo, hard_points={k: [round(float(c), 2) for c in v] for k, v in d["pts"].items()},
               linkage=dict(link_length=lk.link_len, rocker_arm_link=lk.rock_L, rocker_arm_shock=lk.rock_K, e2e=lk.e2e,
                            swingarm_rotation_deg=float(np.degrees(sw["theta"][-1])), rocker_rotation_deg=float(np.degrees(sw["phi"][-1])),
                            lr_start=float(sw["lr"][0]), lr_end=float(sw["lr"][-1]), lr_sag=float(np.interp(d["sag_frac"] * sw["travel"][-1], sw["travel"], sw["lr"])),
                            progression=float(1 - sw["lr"][-1] / sw["lr"][0]), average_lr=float(sw["travel"][-1] / d["shock_stroke"])),
               rear_static_load_N=w,
               setup={k: v for k, v in st.items() if k not in ("z", "f", "f_fast")},
               g1=S.g1_score(st),
               setups_by_tokens={t: dict(pressure_psi=s["pressure_psi"], pressure_frac=s["pressure_frac"], mid_ratio=s["mid_ratio"],
                                         end_ratio=s["end_ratio"], drop_height=s["drop_height"]) for t, s in setups.items()},
               clearances=clearances(d, g, sw), steering_lock=steering_lock(d))
    zs = np.array([r["z"] for r in rows])
    f_at = lambda k, z: float(np.interp(z, zs, [r[k] for r in rows]))
    zsag = d["sag_frac"] * sw["travel"][-1]
    res["kinematics_at_sag"] = dict(anti_rise=f_at("anti_rise", zsag), anti_squat=f_at("anti_squat", zsag), com_height=f_at("com_height", zsag),
                                    axle_rearward=-f_at("axle_dx", zsag), max_rearward=float(-min(r["axle_dx"] for r in rows)),
                                    axle_rearward_bottom=-f_at("axle_dx", sw["travel"][-1]),
                                    chain_growth_total=f_at("chain_growth", sw["travel"][-1]), max_kickback_deg=float(max(abs(r["kickback_deg"]) for r in rows)))
    # ---- tables
    with open(os.path.join(outdir, "kinematics.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["wheel_travel_mm", "shock_stroke_mm", "leverage_ratio", "axle_x_mm", "axle_y_mm", "axle_rearward_mm",
                     "wheel_force_slow_N", "wheel_force_fast_N", "anti_rise_pct", "anti_squat_pct", "chain_growth_mm", "kickback_deg", "rear_centre_mm"])
        for r in rows:
            z = r["z"]; q = interp_pose(sw, z)
            wr.writerow([f"{z:.1f}", f"{q['stroke']:.2f}", f"{q['lr']:.3f}", f"{q['A'][0]:.1f}", f"{q['A'][1]:.1f}", f"{-q['axle_dx']:.1f}",
                         f"{np.interp(z, st['z'], st['f']):.0f}", f"{np.interp(z, st['z'], st['f_fast']):.0f}",
                         f"{r['anti_rise']:.0f}", f"{r['anti_squat']:.0f}", f"{r['chain_growth']:.2f}", f"{r['kickback_deg']:.2f}", f"{-q['A'][0]:.1f}"])
    json.dump(res, open(os.path.join(outdir, "suspension.json"), "w"), indent=1, default=float)
    # ---- plots
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})
    fig, axs = plt.subplots(2, 2, figsize=(13, 8.6), dpi=110)
    a = axs[0, 0]
    a.plot(sw["travel"], sw["lr"], color=INK, lw=2.2, label=f"{d['name']} (simulated linkage)")
    tz = np.array(d["lr_target"]["z"]); a.plot(tz, d["lr_target"]["v"], color=MUTED, lw=1, ls=":", label="design target")
    for bk, col in ((B.SENDER, ACCENT), (B.SUPREME, C3)):
        lr0, lr1 = bk["lr"]["curve"]
        a.plot([0, bk["travel"]], [lr0, lr1], color=col, lw=1.4, ls="--", label=bk["name"].split(" size")[0] + " (estimated)")
    a.set_xlabel("rear wheel travel (mm)"); a.set_ylabel("leverage ratio (wheel travel / shock travel)"); a.legend(frameon=False, fontsize=8); a.grid(color=GRID)
    a.set_title("Leverage ratio", loc="left")
    a = axs[0, 1]
    a.plot(-sw["axle_dx"], sw["travel"], color=INK, lw=2.2)
    a.axvline(0, color=MUTED, lw=0.8); a.set_xlabel("rearward axle movement (mm)"); a.set_ylabel("rear wheel travel (mm)"); a.grid(color=GRID)
    a.set_title("Axle path relative to the frame", loc="left"); a.set_xlim(-25, 25)
    a = axs[1, 0]
    a.plot(st["z"], st["f"], color=INK, lw=2.2, label=f"slow (isothermal), {st['pressure_psi']:.0f} psi, {d['tokens']} tokens")
    a.plot(st["z"], st["f_fast"], color=ACC2, lw=1.6, label="fast (polytropic 1.3)")
    a.fill_between(st["z"], 0.85 * st["f"], 1.15 * st["f"], color=INK, alpha=0.08, lw=0, label="±15 % model uncertainty")
    a.axhline(w, color=MUTED, lw=0.8, ls=":"); a.axvline(zsag, color=MUTED, lw=0.8, ls=":")
    a.text(zsag + 3, 0.05 * st["f"][-1], f"sag {zsag:.0f} mm", color=MUTED, fontsize=8)
    a.set_xlabel("rear wheel travel (mm)"); a.set_ylabel("force at the rear wheel (N)"); a.legend(frameon=False, fontsize=8); a.grid(color=GRID)
    a.set_title("Rear-wheel spring force (estimated air spring ÷ leverage ratio)", loc="left")
    a = axs[1, 1]
    a.plot(zs, [r["anti_rise"] for r in rows], color=INK, lw=2.2, label="anti-rise (%)")
    a.plot(zs, [r["anti_squat"] for r in rows], color=ACC2, lw=2.0, label=f"anti-squat, {d['chainring']}/{d['cog']} (%)")
    a.set_xlabel("rear wheel travel (mm)"); a.set_ylabel("%"); a.grid(color=GRID)
    a2 = a.twinx(); a2.plot(zs, [r["chain_growth"] for r in rows], color=ACCENT, lw=1.4, ls="--", label="chain growth (mm, right)")
    a2.set_ylabel("chain growth (mm)", color=ACCENT); a2.set_ylim(-10, 10)
    h1, l1 = a.get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
    a.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8); a.set_title("Anti-rise, anti-squat, chain growth", loc="left")
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "suspension_curves.png")); plt.close(fig)
    draw_side(d, g, sw, os.path.join(outdir, "side_view.png"))
    return res, g, sw


if __name__ == "__main__":
    import designs
    name = sys.argv[1] if len(sys.argv) > 1 else "v1"
    d = getattr(designs, name)()
    res, g, sw = run(d, os.path.join(os.path.dirname(__file__), "..", "results", d["name"]))
    print(json.dumps({k: res[k] for k in ("geometry", "linkage", "rear_static_load_N", "setup", "g1", "setups_by_tokens", "kinematics_at_sag", "clearances", "steering_lock")}, indent=1, default=lambda v: round(float(v), 3)))
