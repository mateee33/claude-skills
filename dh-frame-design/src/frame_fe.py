"""Shell finite-element model of the front triangle (idealised outer mould line + zoned laminates).

Idealisation (state it wherever results are quoted):
  * geometry = smooth union of elliptical tubes and bosses defined by the side-view axes in designs.py; fillets come
    from the blending radius; no internal ribs; bearing seats / bonded inserts are rigid rings ("spiders")
  * one laminate per zone, constant thickness, 0-degree direction along the local tube axis
  * linear elastic, small displacement; supported at the bottom bracket (all six components) unless stated
Units N, mm, MPa.
"""
from __future__ import annotations
import numpy as np
from geometry import frame_geometry
from layout import structure_lines
from shellfe import mesh_from_sdf, ShellModel, boundary_nodes
import laminate as lam

# --------------------------------------------------------------------------- laminates (inner -> outer)
def base_layups():
    F, U = "F", "U"
    def sym(half):
        return half + half[::-1]
    return {
        # zone: stack.  F = plain-weave fabric at +/-45, U = unidirectional tape
        "down_tube":  sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 90)]),          # 13 UD-equivalent
        "top_tube":   sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 90)]),
        "seat_mast":  sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 90)]),
        "head_tube":  sym([(F, 45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 90), (U, 0)]),
        "ht_junction": sym([(F, 45), (U, 0), (U, 0), (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0)]),
        "core":       sym([(F, 45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 90)]),
        "boss":       sym([(F, 45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 90), (U, 45), (U, -45), (U, 0), (U, 90),
                           (U, 45), (U, -45), (U, 0), (U, 90)]),
    }


# --------------------------------------------------------------------------- geometry
def smin(a, b, k):
    h = np.clip(k - np.abs(a - b), 0, None) / k
    return np.minimum(a, b) - h * h * k * 0.25


def sd_tube(P, a, b, hd, hw):
    """Elliptical tube with axis a->b in the xy-plane, half-depth hd (in plane), half-width hw (z). Flat ends."""
    a3 = np.array([a[0], a[1]]); ab = np.array([b[0] - a[0], b[1] - a[1]]); L = np.linalg.norm(ab); t = ab / L
    n = np.array([-t[1], t[0]])
    r = P[:, :2] - a3
    s = r @ t; u = r @ n; w = P[:, 2]
    f = np.clip(s / L, 0, 1)
    if np.ndim(hd) > 0:                       # tapered section: (value at a, value at b)
        hd = hd[0] + (hd[1] - hd[0]) * f
    if np.ndim(hw) > 0:
        hw = hw[0] + (hw[1] - hw[0]) * f
    q = np.sqrt((u / hd) ** 2 + (w / hw) ** 2)
    d_rad = (q - 1.0) * np.minimum(hd, hw)
    d_end = np.maximum(-s, s - L)
    return np.maximum(d_rad, d_end)


def sd_zcyl(P, c, r, hz):
    d = np.hypot(P[:, 0] - c[0], P[:, 1] - c[1]) - r
    return np.maximum(d, np.abs(P[:, 2]) - hz)


def primitives(d, g):
    L = structure_lines(d, g)
    ax = g["steer_axis"]
    T, B = g["HT_top"], g["HT_bot"]
    dt0, dt1 = L["down_tube"]; tt0, tt1 = L["top_tube"]; m0, m1 = L["seat_mast"]
    pts = {k: np.asarray(v, float) for k, v in d["pts"].items()}
    sec = d.get("sections", {})
    prim = dict(
        head_tube=dict(kind="tube", a=T - 6 * ax, b=B + 6 * ax, hd=sec.get("ht_r", 33.0), hw=sec.get("ht_r", 33.0)),
        down_tube=dict(kind="tube", a=dt0 - 0.0 * (dt1 - dt0), b=dt1, hd=sec.get("dt_hd", d["down_tube_depth"] / 2), hw=sec.get("dt_hw", 35.0)),
        top_tube=dict(kind="tube", a=tt0, b=tt1, hd=sec.get("tt_hd", d["top_tube_depth"] / 2), hw=sec.get("tt_hw", 30.0)),
        seat_mast=dict(kind="tube", a=np.array([m0[0] + 6.0, 38.0]), b=m1 + 0.02 * (m1 - m0), hd=d["seat_mast_depth"] / 2, hw=sec.get("sm_hw", 28.0)),
        core=dict(kind="tube", a=np.array([-6.0, 22.0]), b=np.array([-28.0, 152.0]), hd=sec.get("core_hd", 33.0), hw=sec.get("core_hw", 32.0)),
        bb=dict(kind="zcyl", c=np.zeros(2), r=29.0, hz=44.5),
        pivot=dict(kind="zcyl", c=pts["P"], r=26.0, hz=49.0),
        rocker=dict(kind="zcyl", c=pts["R"], r=15.0, hz=33.0),
        shock=dict(kind="zcyl", c=pts["M"], r=15.0, hz=22.0),
    )
    cuts = dict(ht_top=(T, -ax), ht_bot=(B, ax), bb=44.5 - 3.0, pivot=49.0 - 3.0, rocker=33.0 - 3.0, mast_top=m1)
    return prim, cuts


def make_sdf(prim, blend=9.0):
    def sdf(P):
        d = None
        for name, p in prim.items():
            v = sd_tube(P, p["a"], p["b"], p["hd"], p["hw"]) if p["kind"] == "tube" else sd_zcyl(P, p["c"], p["r"], p["hz"])
            d = v if d is None else smin(d, v, blend)
        return d
    return sdf


def owner_fields(prim, P):
    names = list(prim.keys())
    D = np.stack([sd_tube(P, p["a"], p["b"], p["hd"], p["hw"]) if p["kind"] == "tube" else sd_zcyl(P, p["c"], p["r"], p["hz"])
                  for p in prim.values()], 1)
    return names, D


def build_mesh(d, g, h):
    prim, cuts = primitives(d, g)
    sdf = make_sdf(prim)
    T, B = g["HT_top"], g["HT_bot"]; ax = g["steer_axis"]
    m1 = np.asarray(d["seat_mast"][1], float); m0 = np.asarray(d["seat_mast"][0], float)
    tm = (m1 - m0) / np.linalg.norm(m1 - m0)
    P_, R_ = np.asarray(d["pts"]["P"], float), np.asarray(d["pts"]["R"], float)

    def keep(V):
        xy = V[:, :2]
        k = np.ones(len(V), bool)
        r_ax = np.abs((xy - T) @ np.array([-ax[1], ax[0]]))                # in-plane distance from the steering axis
        on_ht = (r_ax < 46.0) & (np.abs(V[:, 2]) < 46.0)
        k &= ~(on_ht & (((xy - T) @ (-ax)) > 0.0))                         # above head-tube top
        k &= ~(on_ht & (((xy - B) @ ax) > 0.0))                            # below head-tube bottom
        k &= ~((np.hypot(xy[:, 0], xy[:, 1]) < 27.5) & (np.abs(V[:, 2]) > cuts["bb"]))
        k &= ~((np.hypot(*(xy - P_).T) < 24.5) & (np.abs(V[:, 2]) > cuts["pivot"]))
        k &= ~((np.hypot(*(xy - R_).T) < 13.5) & (np.abs(V[:, 2]) > cuts["rocker"]))
        r_m = np.abs((xy - m1) @ np.array([-tm[1], tm[0]]))
        k &= ~((r_m < 40.0) & (((xy - m1) @ tm) > 0.0))                    # above seat-mast top
        return k
    lo = np.array([-140.0, -80.0, -56.0]); hi = np.array([g["HT_bot"][0] + 60.0, g["HT_top"][1] + 45.0, 56.0])
    V, F = mesh_from_sdf(sdf, (lo, hi), h, clip=keep)
    return V, F, prim


def classify(d, g, V, F, prim):
    """Zone per element and laminate 0-degree direction."""
    c = V[F].mean(1)
    names, D = owner_fields(prim, c)
    own = np.array(names)[D.argmin(1)]
    T, B = g["HT_top"], g["HT_bot"]; ax = g["steer_axis"]
    zone = np.empty(len(F), dtype=object)
    xmat = np.zeros((len(F), 3))
    dirs = {}
    for n, p in prim.items():
        if p["kind"] == "tube":
            t = (p["b"] - p["a"]) / np.linalg.norm(p["b"] - p["a"]); dirs[n] = np.array([t[0], t[1], 0.0])
        else:
            dirs[n] = np.array([0.0, 0.0, 1.0])
    for n in names:
        m = own == n
        xmat[m] = dirs[n]
        zone[m] = dict(head_tube="head_tube", down_tube="down_tube", top_tube="top_tube", seat_mast="seat_mast", core="core",
                       bb="boss", pivot="boss", rocker="boss", shock="boss")[n]
    # head-tube junction reinforcement: tube elements within 95 mm of the steering axis
    xy = c[:, :2]
    s = (xy - T) @ ax; dist_ax = np.abs((xy - T) @ np.array([-ax[1], ax[0]]))
    near_ht = (dist_ax < d.get("htj_len", 95.0)) & np.isin(own, ["down_tube", "top_tube"])
    zone[near_ht] = "ht_junction"
    # local reinforcement around hard points on tube walls
    for key, rad in (("P", 48.0), ("R", 36.0), ("M", 40.0)):
        pt = np.asarray(d["pts"][key], float)
        m = (np.hypot(*(xy - pt).T) < rad) & ~np.isin(zone, ["head_tube"])
        zone[m] = "boss"
    m = (np.hypot(xy[:, 0], xy[:, 1]) < 46.0)
    zone[m] = "boss"
    # seat-mast / top-tube junction region uses the core laminate
    tt0 = np.asarray(d["top_tube_end"], float)
    m = (np.hypot(*(xy - tt0).T) < 55.0) & np.isin(zone, ["top_tube", "seat_mast"])
    zone[m] = "core"
    return zone, xmat, own


def build_model(d, g, h, layups=None):
    V, F, prim = build_mesh(d, g, h)
    zone, xmat, own = classify(d, g, V, F, prim)
    layups = layups or d.get("layups") or base_layups()
    order = list(layups.keys())
    props = [lam.shellprop(layups[z]) for z in order]
    idx = np.array([order.index(z) for z in zone])
    m = ShellModel(V, F)
    m.set_properties(props, idx, xmat)
    # interfaces
    b = boundary_nodes(F)
    T, B = g["HT_top"], g["HT_bot"]
    P_, R_, M_ = (np.asarray(d["pts"][k], float) for k in ("P", "R", "M"))
    xy = V[:, :2]
    def near(pt, r, nodes):
        return nodes[np.hypot(*(xy[nodes] - pt).T) < r]
    rings = dict(HTU=near(T, 45.0, b), HTL=near(B, 45.0, b), BB=near(np.zeros(2), 33.0, b), PIV=near(P_, 30.0, b), ROCK=near(R_, 19.0, b))
    allv = np.arange(len(V))
    lug = allv[(np.hypot(*(xy - M_).T) < 13.0)]
    rings["SHK"] = lug
    centres = dict(HTU=[T[0], T[1], 0], HTL=[B[0], B[1], 0], BB=[0, 0, 0], PIV=[P_[0], P_[1], 0], ROCK=[R_[0], R_[1], 0], SHK=[M_[0], M_[1], 0])
    used = set()
    for name, nodes in rings.items():
        nodes = np.array([n for n in nodes if n not in used], int)
        used.update(nodes.tolist())
        assert len(nodes) >= 6, f"interface {name} has too few nodes ({len(nodes)})"
        m.add_spider(name, nodes, centres[name])
    m.zone, m.zone_names, m.layups, m.own = zone, order, layups, own
    m.assemble()
    m.factorize([("BB", [0, 1, 2, 3, 4, 5])])
    return m


def mass_of(m):
    V, F = m.V, m.F
    area = 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    out = {}
    for z in m.zone_names:
        sel = m.zone == z
        out[z] = dict(area_mm2=float(area[sel].sum()), thickness=lam.thickness(m.layups[z]),
                      mass_kg=float(area[sel].sum() * lam.areal_mass(m.layups[z])))
    return out


def evaluate(m, u):
    """Failure indices per element (strains from loads as applied; scale outside)."""
    e0, kp = m.strains(u)
    fi = np.zeros(len(m.F)); mode = np.zeros(len(m.F), int)
    comp = {}
    for z in m.zone_names:
        sel = np.where(m.zone == z)[0]
        if len(sel) == 0:
            continue
        r = lam.failure_indices(m.layups[z], e0[sel], kp[sel])
        fi[sel] = r["fi"]; mode[sel] = r["mode"]
    return fi, mode, e0, kp
