"""Figures and CAD exports for the report."""
from __future__ import annotations
import sys, os, json, csv
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import designs, benchmarks as B, suspension as S, loads as Ld, run_suspension as RSu
from geometry import frame_geometry
from kinematics import Linkage, interp_pose
from layout import structure_lines
from draw import INK, MUTED, ACCENT, ACC2, GRID, draw_side, tube_poly
import frame_fe as FE, swingarm_fe as SW
from cases import CASES, ULT, interface_loads

ROOT = os.path.join(os.path.dirname(__file__), "..")
FIG = os.path.join(ROOT, "results", "figures"); CAD = os.path.join(ROOT, "cad")
os.makedirs(FIG, exist_ok=True); os.makedirs(CAD, exist_ok=True)
C3, C4 = "#1d4ed8", "#7c3aed"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False})


def fig_g1():
    fig, ax = plt.subplots(1, 2, figsize=(13.5, 5.2), dpi=120)
    curves = []
    for name, col, lw in (("v1", MUTED, 1.6), (designs.FINAL, INK, 2.6)):
        d = getattr(designs, name)(); g = frame_geometry(d); d["pts"]["A"] = tuple(g["rear_axle"])
        sw = Linkage(d["pts"], 75).sweep(); w = S.rear_static_load(g["front_centre"], g["wheelbase"])
        st = S.setup(sw, w, 0.25, 2)
        curves.append((f"Custom {d['name']} (simulated linkage)", st["z"] / st["z"][-1], st["f"] / w, col, lw, "-"))
        ax[0].plot(sw["travel"], sw["lr"], color=col, lw=lw, label=f"Custom {d['name']}")
    bm = RSu.benchmark_g1()
    for key, col, ls in (("sender_32.7", ACCENT, "--"), ("sender_37", ACCENT, ":"), ("supreme", C3, "--")):
        v = bm[key]
        lab = {"sender_32.7": "Sender CFR, 32.7 % chip (estimated)", "sender_37": "Sender CFR, 37 % chip (estimated)", "supreme": "Supreme DH V5 (estimated)"}[key]
        curves.append((lab, v["z"] / v["z"][-1], v["f"] / v["w_rear"], col, 1.6, ls))
        tr = v["z"][-1]
        ax[0].plot([0, tr], list(v["lr"]), color=col, lw=1.6, ls=ls, label=lab)
    for lab, x, y, col, lw, ls in curves:
        ax[1].plot(100 * x, y, color=col, lw=lw, ls=ls, label=lab)
    ax[1].fill_between([58, 62], [2.3, 2.3], [2.8, 2.8], color=ACC2, alpha=0.35, lw=0)
    ax[1].annotate("target at 60 %: 2.3–2.8", (62, 2.55), xytext=(66, 1.5), fontsize=8.5, color=ACC2, arrowprops=dict(arrowstyle="-", color=ACC2))
    ax[1].plot([97, 100], [6.5, 6.5], color=ACC2, lw=2); ax[1].text(77, 6.6, "target at 100 %: ≥ 6.5", fontsize=8.5, color=ACC2)
    ax[1].axvline(25, color=MUTED, lw=0.8, ls=":"); ax[1].text(26, 0.25, "sag 25 %", fontsize=8.5, color=MUTED)
    ax[0].set_xlabel("rear wheel travel (mm)"); ax[0].set_ylabel("leverage ratio (wheel travel ÷ shock travel)")
    ax[0].set_title("Leverage ratio", loc="left"); ax[0].legend(frameon=False, fontsize=8); ax[0].grid(color=GRID)
    ax[1].set_xlabel("rear wheel travel (% of each bike's travel)"); ax[1].set_ylabel("spring force at rear wheel ÷ rear sprung load")
    ax[1].set_title("Rear-wheel spring force, same shock model, 68 kg rider, 25 % sag", loc="left"); ax[1].grid(color=GRID)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "g1_force_curves.png")); plt.close(fig)


def fig_loads():
    d = getattr(designs, designs.FINAL)(); g = frame_geometry(d); d["pts"]["A"] = tuple(g["rear_axle"]); sw = Linkage(d["pts"], 75).sweep()
    k, h, F, pred, W = Ld.isbs_effective_stiffness()
    Wsys = (Ld.M_RIDER_STRUCT + Ld.M_BIKE) * 9.81
    hs = np.array([0.3, 0.5, 0.67, 1.0, 1.5, 2.0, 2.5, 3.0])
    rear6 = [Ld.landing("rear", x, sw, mass_share=0.6)["peak_ground"] for x in hs]
    rear7 = [Ld.landing("rear", x, sw, mass_share=0.7)["peak_ground"] for x in hs]
    front = [Ld.landing("front", x, mass_share=0.55)["peak_ground"] for x in hs]
    flat = [a + Ld.landing("front", x, mass_share=0.4)["peak_ground"] for a, x in zip(rear6, hs)]
    fig, ax = plt.subplots(1, 2, figsize=(13.5, 5.0), dpi=120)
    hh = np.linspace(0.1, 3.0, 60)
    ax[0].plot(hh, Ld.empirical_peak(W, hh) / W, color=MUTED, lw=1.5, ls="--", label="one-spring law fitted to the measurements")
    ax[0].plot(h, F / W, "o", color=ACCENT, ms=8, label="measured (Phillips et al. 2015, 130 mm bike, 76.6 kg riders)")
    ax[0].plot(hs, np.array(flat) / Wsys, color=INK, lw=2.2, marker="s", ms=4, label="this study: simulated, both wheels, 200 mm bike, 97 kg")
    ax[0].set_xlabel("equivalent flat-drop height (m)"); ax[0].set_ylabel("peak total ground force ÷ system weight")
    ax[0].set_title("Landing model against measured data", loc="left"); ax[0].legend(frameon=False, fontsize=8); ax[0].grid(color=GRID)
    ax[1].plot(hs, np.array(rear7) / 1e3, color=INK, lw=2.2, marker="s", ms=4, label="rear wheel, 70 % of mass (simulated)")
    ax[1].plot(hs, np.array(rear6) / 1e3, color=INK, lw=1.2, ls=":", label="rear wheel, 60 % of mass")
    ax[1].plot(hs, np.array(front) / 1e3, color=C3, lw=2.0, marker="o", ms=4, label="front wheel, 55 % of mass (simulated)")
    ax[1].axhline(9.2, color=INK, lw=0.9, ls="--"); ax[1].text(0.32, 9.35, "rear limit load 9.2 kN = simulated 2.0 m value × 1.25", fontsize=8.5, color=INK)
    ax[1].axhline(8.0, color=C3, lw=0.9, ls="--"); ax[1].text(0.32, 8.12, "front limit load 8.0 kN", fontsize=8.5, color=C3)
    ax[1].axvline(2.0, color=MUTED, lw=0.8, ls=":")
    ax[1].set_xlabel("equivalent flat-drop height (m)"); ax[1].set_ylabel("peak wheel force (kN)"); ax[1].set_ylim(0, 15)
    ax[1].set_title("Design limit loads from the landing simulation", loc="left"); ax[1].legend(frameon=False, fontsize=8, loc="lower right"); ax[1].grid(color=GRID)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "loads_landing.png")); plt.close(fig)
    return dict(efh=hs.tolist(), rear_70=rear7, rear_60=rear6, front_55=front, flat_total=flat, system_weight=Wsys,
                isbs=dict(h=h.tolist(), measured=F.tolist(), fit=pred.tolist(), k_eff_N_per_mm=k / 1000.0))


def _fi(name, key, h=7.0):
    d = getattr(designs, name)(); g = frame_geometry(d); d["pts"]["A"] = tuple(g["rear_axle"]); sw = Linkage(d["pts"], 75).sweep()
    m = FE.build_model(d, g, h)
    L, _, _ = interface_loads(d, g, sw, [c for c in CASES if c["key"] == key][0])
    u, _, _ = m.solve(L); fi, mode, e0, kp = FE.evaluate(m, u)
    return m, fi * ULT


def fig_fi():
    fig, axs = plt.subplots(2, 2, figsize=(14, 11.5), dpi=110)
    for j, key in enumerate(("LC3", "LC2d")):
        for i, name in enumerate(("v2", designs.FINAL)):
            m, fi = _fi(name, key)
            V, F = m.V, m.F
            side = V[F].mean(1)[:, 2] < 0
            a = axs[j, i]
            tp = a.tripcolor(V[:, 0], V[:, 1], F[side], facecolors=np.clip(fi[side], 0, 1.5), cmap="cividis", vmin=0, vmax=1.5, edgecolors="none")
            a.set_aspect("equal"); a.set_xlabel("x (mm)"); a.set_ylabel("y (mm)")
            a.set_title(f"{name.upper()} — {key}: strain index at ultimate load (1.0 = design limit), right-hand side", loc="left", fontsize=9.5)
            cb = fig.colorbar(tp, ax=a, shrink=0.55); cb.ax.axhline(1.0, color="white", lw=1.5)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "front_triangle_strain_index.png")); plt.close(fig)


def fig_swingarm():
    fig, axs = plt.subplots(2, 1, figsize=(12, 8.2), dpi=110)
    for a, name in zip(axs, ("v3", designs.FINAL)):
        d = getattr(designs, name)(); g = frame_geometry(d); d["pts"]["A"] = tuple(g["rear_axle"]); sw = Linkage(d["pts"], 75).sweep()
        m = SW.build(d, g, 4.5)
        L, info = SW.case_loads(d, g, sw, [c for c in CASES if c["key"] == "LC3"][0])
        u, _, _ = m.solve(L); e0, kp = m.strains(u)
        fi = np.zeros(len(m.F))
        import laminate as lam
        for z in m.zone_names:
            sel = np.where(m.zone == z)[0]
            if len(sel):
                fi[sel] = lam.failure_indices(m.layups[z], e0[sel], kp[sel])["fi"] * ULT
        V, F = m.V, m.F
        top = V[F].mean(1)[:, 1] > -1e9
        tp = a.tripcolor(V[:, 0], V[:, 2], F[top], facecolors=np.clip(fi[top], 0, 1.5), cmap="cividis", vmin=0, vmax=1.5, edgecolors="none")
        a.set_aspect("equal"); a.set_xlabel("x (mm)"); a.set_ylabel("z (mm, left +)")
        a.set_title(f"Swingarm {name.upper()} — sideways landing (LC3): strain index at ultimate load, plan view", loc="left", fontsize=9.5)
        fig.colorbar(tp, ax=a, shrink=0.8)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "swingarm_strain_index.png")); plt.close(fig)


def fig_revisions(summary):
    names = list(summary["revisions"].keys())
    ft = [summary["revisions"][n]["worst"]["front_triangle"]["fi"] for n in names]
    sa = [summary["revisions"][n]["worst"]["swingarm"]["fi"] for n in names]
    jm = [1 / (1 + summary["revisions"][n]["worst"]["joint_margin"]) for n in names]
    mass = [summary["revisions"][n]["frame_mass"] for n in names]
    mid = [summary["revisions"][n]["suspension"]["setup"]["mid_ratio"] for n in names]
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.4), dpi=120)
    x = np.arange(len(names)); w = 0.26
    ax[0].bar(x - w, ft, w, color=INK, label="front triangle"); ax[0].bar(x, sa, w, color=C3, label="swingarm"); ax[0].bar(x + w, jm, w, color=ACCENT, label="worst joint")
    ax[0].axhline(1.0, color=MUTED, lw=1, ls="--"); ax[0].set_xticks(x, names); ax[0].set_ylim(0, 2.2)
    ax[0].set_ylabel("demand ÷ capacity at ultimate (≤ 1 passes)"); ax[0].set_title("Worst structural utilisation", loc="left"); ax[0].legend(frameon=False, fontsize=8)
    for xi, v in zip(x + w, jm):
        if v > 2.2:
            ax[0].text(xi, 2.1, f"{v:.1f}", ha="center", fontsize=8, color=ACCENT)
    ax[1].bar(x, mid, 0.5, color=INK); ax[1].axhspan(2.3, 2.8, color=ACC2, alpha=0.25, lw=0); ax[1].set_xticks(x, names); ax[1].set_ylim(1.8, 2.9)
    ax[1].set_ylabel("wheel force at 60 % travel ÷ sprung load"); ax[1].set_title("Mid-stroke support (target band shaded)", loc="left")
    ax[2].bar(x, mass, 0.5, color=[MUTED if not summary["revisions"][n]["structure_pass"] else INK for n in names])
    ax[2].errorbar(x, mass, yerr=0.12 * np.array(mass), fmt="none", ecolor=ACCENT, capsize=4)
    ax[2].axhline(4.614, color=ACCENT, lw=1, ls="--"); ax[2].text(-0.4, 4.66, "Sender CFR claimed 4.61 kg", fontsize=8, color=ACCENT)
    ax[2].axhline(5.3, color=C3, lw=1, ls="--"); ax[2].text(-0.4, 5.35, "Supreme DH V5 claimed 5.3 kg", fontsize=8, color=C3)
    ax[2].set_xticks(x, names); ax[2].set_ylim(3, 5.8); ax[2].set_ylabel("frame mass (kg), ±12 % band")
    ax[2].set_title("Frame mass (grey = fails a structural check)", loc="left")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "revision_history.png")); plt.close(fig)


def fig_convergence():
    c = json.load(open(os.path.join(ROOT, "results", "convergence.json")))
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=120)
    f = c["front_triangle_V3"]
    for k, col in (("LC2d", INK), ("LC3", C3), ("LC2b", ACCENT), ("LC2a", MUTED)):
        ax[0].plot(f["nodes"], f[k], marker="o", color=col, label=k)
    ax[0].axhline(1.0, color=MUTED, ls="--", lw=1); ax[0].set_ylim(0, 1.1); ax[0].set_xlabel("nodes in the model"); ax[0].set_ylabel("hot-spot strain index at ultimate")
    ax[0].set_title("Front triangle (V3 laminate): mesh refinement", loc="left"); ax[0].legend(frameon=False, fontsize=8); ax[0].grid(color=GRID)
    s = c["swingarm_V4"]
    for k, col in (("LC3", C3), ("LC2b", ACCENT), ("LC4", MUTED)):
        ax[1].plot(s["nodes"], s[k], marker="o", color=col, label=k)
    ax[1].axhline(1.0, color=MUTED, ls="--", lw=1); ax[1].set_ylim(0, 1.1); ax[1].set_xlabel("nodes in the model")
    ax[1].set_title("Swingarm (V4): mesh refinement", loc="left"); ax[1].legend(frameon=False, fontsize=8); ax[1].grid(color=GRID)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "mesh_convergence.png")); plt.close(fig)


def cad_exports():
    import ezdxf
    d = getattr(designs, designs.FINAL)(); g = frame_geometry(d); d["pts"]["A"] = tuple(g["rear_axle"]); sw = Linkage(d["pts"], 75).sweep()
    L = structure_lines(d, g)
    travel = sw["travel"][-1]
    states = [("top-out", 0.0), ("sag (25 %)", 0.25 * travel), ("bottom-out", travel)]
    zlat = dict(BB=0, P=38, R=36, M=0, S=50, L=50, K=0, A=78.5)
    rows = [["point", "description", "state", "x_mm", "y_mm", "z_mm (half-spacing; 0 = on centre plane)"]]
    desc = dict(BB="bottom-bracket centre (origin)", P="main pivot axis", R="rocker pivot axis", M="shock eye on front triangle",
                S="push-link eye on swingarm", L="push-link eye on rocker", K="shock eye on rocker", A="rear axle")
    for st, z in states:
        q = interp_pose(sw, z)
        cur = dict(BB=np.zeros(2), P=np.array(d["pts"]["P"]), R=np.array(d["pts"]["R"]), M=np.array(d["pts"]["M"]), S=q["S"], L=q["L"], K=q["K"], A=q["A"])
        for k in ("BB", "P", "R", "M", "S", "L", "K", "A"):
            rows.append([k, desc[k], st, f"{cur[k][0]:.1f}", f"{cur[k][1]:.1f}", f"±{zlat[k]:.1f}" if zlat[k] else "0.0"])
    fixed = [("HT_top", "head-tube top centre (stack/reach point)", g["HT_top"]), ("HT_bottom", "head-tube bottom centre", g["HT_bot"]),
             ("crown_race", "fork crown-race seat", g["crown_race"]), ("front_axle", "front axle, fork at top-out", g["front_axle"]),
             ("idler", "idler sprocket centre (14 T)", np.array(d["idler"]["centre"])),
             ("seat_mast_bottom", "seat-mast axis, lower end", L["seat_mast"][0]), ("seat_mast_top", "seat-mast axis, top (seat-tube top)", L["seat_mast"][1]),
             ("down_tube_bb_end", "down-tube axis at BB end", L["down_tube"][0]), ("down_tube_ht_end", "down-tube axis at head tube", L["down_tube"][1]),
             ("top_tube_mast_end", "top-tube axis at seat mast", L["top_tube"][0]), ("top_tube_ht_end", "top-tube axis at head tube", L["top_tube"][1]),
             ("ground", "ground level under both tyres (y only)", np.array([0.0, g["ground_y"]]))]
    for k, de, p in fixed:
        zz = "-56.5 (drive side)" if k == "idler" else "0.0"
        rows.append([k, de, "fixed", f"{p[0]:.1f}", f"{p[1]:.1f}", zz])
    with open(os.path.join(CAD, f"hard_points_{d['name']}.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(rows)
    # DXF side view
    doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    for lay, col in (("FRAME", 7), ("SWINGARM_TOPOUT", 5), ("SWINGARM_SAG", 3), ("SWINGARM_BOTTOMOUT", 1), ("WHEELS", 8), ("FORK", 7), ("POINTS", 2), ("GROUND", 8)):
        doc.layers.add(lay, color=col)
    for nm, depth in (("down_tube", d["down_tube_depth"]), ("top_tube", d["top_tube_depth"]), ("seat_mast", d["seat_mast_depth"]), ("head_tube", 66.0)):
        a, b = L[nm]
        poly = tube_poly(a, b, depth)
        msp.add_lwpolyline([tuple(p) for p in poly], close=True, dxfattribs=dict(layer="FRAME"))
        msp.add_line(tuple(a), tuple(b), dxfattribs=dict(layer="FRAME", linetype="CENTER"))
    msp.add_circle((0, 0), 23.0, dxfattribs=dict(layer="FRAME"))
    P = np.array(d["pts"]["P"]); R = np.array(d["pts"]["R"]); M = np.array(d["pts"]["M"])
    msp.add_circle(tuple(P), 10.0, dxfattribs=dict(layer="FRAME")); msp.add_circle(tuple(R), 8.5, dxfattribs=dict(layer="FRAME")); msp.add_circle(tuple(M), 6.35, dxfattribs=dict(layer="FRAME"))
    C, Fa = g["crown_race"], g["front_axle"]
    msp.add_line(tuple(g["HT_top"]), tuple(C), dxfattribs=dict(layer="FORK", linetype="CENTER")); msp.add_line(tuple(C), tuple(Fa), dxfattribs=dict(layer="FORK"))
    msp.add_circle(tuple(Fa), d["front_tyre_radius"], dxfattribs=dict(layer="WHEELS"))
    msp.add_line((-900, g["ground_y"]), (1300, g["ground_y"]), dxfattribs=dict(layer="GROUND"))
    for (st, z), lay in zip(states, ("SWINGARM_TOPOUT", "SWINGARM_SAG", "SWINGARM_BOTTOMOUT")):
        q = interp_pose(sw, z)
        A, Sp, Lk, K = q["A"], q["S"], q["L"], q["K"]
        msp.add_lwpolyline([tuple(P), tuple(A), tuple(Sp)], close=True, dxfattribs=dict(layer=lay))
        msp.add_line(tuple(Sp), tuple(Lk), dxfattribs=dict(layer=lay)); msp.add_lwpolyline([tuple(Lk), tuple(R), tuple(K)], close=True, dxfattribs=dict(layer=lay))
        msp.add_line(tuple(K), tuple(M), dxfattribs=dict(layer=lay)); msp.add_circle(tuple(A), d["rear_tyre_radius"], dxfattribs=dict(layer="WHEELS" if z == 0 else lay))
        for p in (A, Sp, Lk, K):
            msp.add_circle(tuple(p), 4.0, dxfattribs=dict(layer=lay))
    ic = np.array(d["idler"]["centre"]); msp.add_circle(tuple(ic), S.sprocket_radius(d["idler"]["teeth"]), dxfattribs=dict(layer="POINTS"))
    msp.add_circle((0, 0), S.sprocket_radius(d["chainring"]), dxfattribs=dict(layer="POINTS"))
    for k, p in dict(BB=(0, 0), P=P, R=R, M=M).items():
        msp.add_text(k, height=8, dxfattribs=dict(layer="POINTS")).set_placement((p[0] + 8, p[1] + 8))
    doc.saveas(os.path.join(CAD, f"side_view_{d['name']}.dxf"))
    # STL of the analysed outer mould line (idealised) for 3-D inspection
    def stl(path, V, F):
        import struct
        n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); n /= np.linalg.norm(n, axis=1)[:, None] + 1e-30
        with open(path, "wb") as fh:
            fh.write(b"DH frame study - idealised analysis surface, mm".ljust(80, b" ")); fh.write(struct.pack("<I", len(F)))
            for i in range(len(F)):
                fh.write(struct.pack("<12fH", *n[i], *V[F[i, 0]], *V[F[i, 1]], *V[F[i, 2]], 0))
    V, F, _ = FE.build_mesh(d, g, 8.0); stl(os.path.join(CAD, f"front_triangle_surface_{d['name']}.stl"), V, F)
    m = SW.build(d, g, 6.0); stl(os.path.join(CAD, f"swingarm_surface_{d['name']}.stl"), m.V, m.F)
    draw_side(d, g, sw, os.path.join(FIG, f"side_view_{d['name']}.png"))
    import shutil
    shutil.copy(os.path.join(ROOT, "results", d["name"], "suspension_curves.png"), os.path.join(FIG, f"suspension_curves_{d['name']}.png"))


if __name__ == "__main__":
    summary = json.load(open(os.path.join(ROOT, "results", "summary.json")))
    fig_g1(); print("g1")
    ld = fig_loads(); json.dump(ld, open(os.path.join(ROOT, "results", "landing_simulation.json"), "w"), indent=1); print("loads")
    fig_revisions(summary); fig_convergence(); print("rev/conv")
    cad_exports(); print("cad")
    fig_fi(); print("fi")
    fig_swingarm(); print("swingarm")
