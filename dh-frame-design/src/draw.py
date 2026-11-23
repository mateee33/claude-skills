"""Side-view drawing (matplotlib PNG/SVG) of a design at top-out, sag and bottom-out."""
from __future__ import annotations
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from kinematics import interp_pose
from layout import structure_lines

INK, MUTED, ACCENT, ACC2, GRID = "#1f2933", "#7b8794", "#c2410c", "#0f766e", "#d9dee3"


def tube_poly(a, b, depth):
    a, b = np.asarray(a, float), np.asarray(b, float)
    t = (b - a) / np.linalg.norm(b - a); n = np.array([-t[1], t[0]]) * depth / 2
    return np.array([a + n, b + n, b - n, a - n])


def draw_side(d, g, sw, path, title="", show_states=(0.0, None, 1.0), dims=True):
    L = structure_lines(d, g)
    P = np.asarray(d["pts"]["P"], float)
    pts = {k: np.asarray(v, float) for k, v in d["pts"].items()}
    fig, ax = plt.subplots(figsize=(15, 9.2), dpi=110)
    gy = g["ground_y"]
    ax.axhline(gy, color=MUTED, lw=1)
    # front triangle tubes
    for name, depth in (("down_tube", d["down_tube_depth"]), ("top_tube", d["top_tube_depth"]),
                        ("seat_mast", d["seat_mast_depth"]), ("head_tube", 64.0)):
        a, b = L[name]
        ax.add_patch(Polygon(tube_poly(a, b, depth), closed=True, fc="#e8ecef", ec=INK, lw=1.2, zorder=2))
    ax.add_patch(Circle((0, 0), 27, fc="#e8ecef", ec=INK, lw=1.2, zorder=3))
    # fork
    C, F = g["crown_race"], g["front_axle"]
    ax.plot([g["HT_top"][0], C[0]], [g["HT_top"][1], C[1]], color=MUTED, lw=1, ls="--", zorder=1)
    ax.plot([C[0], F[0]], [C[1], F[1]], color=INK, lw=5, solid_capstyle="round", zorder=2)
    # wheels
    rr, rf = d["rear_tyre_radius"], d["front_tyre_radius"]
    ax.add_patch(Circle(F, rf, fill=False, ec=INK, lw=1.4))
    ax.add_patch(Circle(F, rf - 60, fill=False, ec=GRID, lw=1))
    travel = sw["travel"][-1]
    states = [0.0, d.get("sag_frac", 0.25) * travel, travel]
    styles = [dict(color=INK, lw=2.2, alpha=1.0, ls="-"), dict(color=ACC2, lw=1.4, alpha=0.9, ls="-"),
              dict(color=ACCENT, lw=1.4, alpha=0.9, ls="--")]
    for z, st in zip(states, styles):
        q = interp_pose(sw, z)
        A, S, Lk, K = q["A"], q["S"], q["L"], q["K"]
        ax.add_patch(Circle(A, rr, fill=False, ec=st["color"], lw=1.2 if z else 1.4, ls=st["ls"], alpha=st["alpha"]))
        ax.plot([P[0], A[0], S[0], P[0]], [P[1], A[1], S[1], P[1]], **st, zorder=4)          # swingarm triangle
        ax.plot([S[0], Lk[0]], [S[1], Lk[1]], **st, zorder=5)                                  # push link
        ax.plot([Lk[0], pts["R"][0], K[0]], [Lk[1], pts["R"][1], K[1]], **st, zorder=5)        # rocker
        ax.plot([K[0], pts["M"][0]], [K[1], pts["M"][1]], color=st["color"], lw=6 if z == 0 else 2.5,
                alpha=0.55 if z == 0 else 0.8, solid_capstyle="round", zorder=4)                # shock
    # hard points
    q0 = interp_pose(sw, 0.0)
    labels = dict(BB=np.zeros(2), P=P, R=pts["R"], M=pts["M"], S=q0["S"], L=q0["L"], K=q0["K"], A=q0["A"], F=F)
    for k, v in labels.items():
        ax.plot(*v, "o", ms=5, color=ACCENT, zorder=7)
        ax.annotate(k, v, xytext=(6, 6), textcoords="offset points", fontsize=9, color=INK, zorder=8)
    if d.get("idler"):
        ic = np.asarray(d["idler"]["centre"], float)
        ax.add_patch(Circle(ic, 12.7 / (2 * np.sin(np.pi / d["idler"]["teeth"])), fill=False, ec=MUTED, lw=1))
    ax.add_patch(Circle((0, 0), 12.7 / (2 * np.sin(np.pi / d["chainring"])), fill=False, ec=MUTED, lw=1))
    if dims:
        ax.annotate("", (g["front_axle"][0], gy - 40), (q0["A"][0], gy - 40), arrowprops=dict(arrowstyle="<->", color=MUTED))
        ax.text((g["front_axle"][0] + q0["A"][0]) / 2, gy - 62, f"wheelbase {g['wheelbase']:.0f}", ha="center", color=INK, fontsize=9)
        ax.annotate("", (d["reach"], d["stack"] + 30), (0, d["stack"] + 30), arrowprops=dict(arrowstyle="<->", color=MUTED))
        ax.text(d["reach"] / 2, d["stack"] + 38, f"reach {d['reach']:.0f}", ha="center", color=INK, fontsize=9)
        ax.annotate("", (d["reach"] + 60, d["stack"]), (d["reach"] + 60, 0), arrowprops=dict(arrowstyle="<->", color=MUTED))
        ax.text(d["reach"] + 68, d["stack"] / 2, f"stack {d['stack']:.1f}", color=INK, fontsize=9, rotation=90, va="center")
    ax.set_aspect("equal"); ax.set_xlim(-860, 1260); ax.set_ylim(gy - 90, 760)
    ax.set_xlabel("x (mm, forward)"); ax.set_ylabel("y (mm, up)   origin = bottom-bracket centre")
    ax.grid(True, color=GRID, lw=0.5); ax.set_axisbelow(True)
    ax.set_title(title or f"{d['name']} side view: top-out (dark), sag (teal), bottom-out (orange dashed)", loc="left", fontsize=11)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)
