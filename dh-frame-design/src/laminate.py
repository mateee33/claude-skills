"""Materials, design allowables and ply-level strain checks.

Material data: Toray 2510 prepreg system datasheet (room temperature, dry), see sources/standards_loads_materials.md.
These are datasheet lot averages, NOT statistically based allowables. The design values below are ESTIMATED by
applying strain cut-offs taken from aerospace damage-tolerance practice; they must be replaced by coupon tests
of the actual prepreg, cure cycle and moulding process before any frame is built.
"""
from __future__ import annotations
import numpy as np
from pyfe3d.shellprop_utils import laminated_plate

# ---- lamina properties (MPa, mm, kg/mm^3)
UD = dict(name="T700G/2510 UD tape 150 gsm", E1=118.5e3, E2=8.41e3, nu12=0.31, G12=4.23e3, G13=4.23e3, G23=3.0e3,
          t=0.152, rho=1.517e-6,
          Xt=2172.0, Xc=1448.0, Yt=44.3, S=154.0, ILSS=86.2)          # E1 = mean of tensile (125) and compressive (112) moduli
FAB = dict(name="T700S-12K/2510 plain weave 190 gsm", E1=55.9e3, E2=55.9e3, nu12=0.04, G12=4.21e3, G13=4.21e3, G23=3.0e3,
           t=0.218, rho=1.502e-6, Xt=912.0, Xc=709.0, Yt=772.0, S=133.0, ILSS=60.0)
MATS = dict(U=UD, F=FAB)

# ---- design strain limits at ULTIMATE load (1.5 x limit), microstrain. ESTIMATED.
#  fibre compression 4500 ue : NASA CR-159296 / CR-198347 damage-tolerant design strain (~50 % of unflawed strain);
#                              sits between the datasheet open-hole compression (hot-wet 247 MPa / 46 GPa = 5400 ue)
#                              and compression-after-impact (137 MPa / 46 GPa = 3000 ue) values for quasi-isotropic tape.
#  fibre tension 6000 ue     : notched-tension design practice; unflawed failure strain is 17 400 ue.
#  in-plane shear 9000 ue    : about the linear limit of the hot-wet shear curve (95 MPa ultimate, G12 3.1 GPa).
#  transverse tension (tape) : no matrix cracking at LIMIT load: 0.85 x 25.9 MPa / 6.34 GPa (hot-wet) = 3400 ue at limit
#                              -> 5100 ue when compared with ultimate-load strains.
EPS_T, EPS_C, GAM, EPS_2T_ULT = 6000e-6, 4500e-6, 9000e-6, 5100e-6


def parse(stack):
    """stack: list of (material key, angle deg). Returns list of dicts bottom (inner) -> top (outer)."""
    return [dict(mat=m, ang=float(a), t=MATS[m]["t"]) for m, a in stack]


def shellprop(stack):
    plies = parse(stack)
    props = [(MATS[p["mat"]]["E1"], MATS[p["mat"]]["E2"], MATS[p["mat"]]["nu12"], MATS[p["mat"]]["G12"],
              MATS[p["mat"]]["G13"], MATS[p["mat"]]["G23"]) for p in plies]
    return laminated_plate(stack=[p["ang"] for p in plies], plyts=[p["t"] for p in plies], laminaprops=props,
                           rhos=[MATS[p["mat"]]["rho"] for p in plies])


def thickness(stack):
    return sum(MATS[m]["t"] for m, _ in stack)


def areal_mass(stack):
    return sum(MATS[m]["t"] * MATS[m]["rho"] for m, _ in stack)        # kg/mm^2


def failure_indices(stack, e0, kap):
    """Ply-by-ply strain check. e0, kap: (n,3) mid-surface strains/curvatures in laminate axes.
    Returns dict of (n,) arrays: worst index per mode over all plies and both ply faces, plus the governing mode."""
    plies = parse(stack)
    h = sum(p["t"] for p in plies)
    z = -h / 2
    n = len(e0)
    out = dict(ft=np.zeros(n), fc=np.zeros(n), fs=np.zeros(n), fm=np.zeros(n))
    for p in plies:
        c, s = np.cos(np.radians(p["ang"])), np.sin(np.radians(p["ang"]))
        for zz in (z, z + p["t"]):
            ex = e0[:, 0] + zz * kap[:, 0]; ey = e0[:, 1] + zz * kap[:, 1]; gxy = e0[:, 2] + zz * kap[:, 2]
            e1 = c * c * ex + s * s * ey + s * c * gxy
            e2 = s * s * ex + c * c * ey - s * c * gxy
            g12 = -2 * s * c * ex + 2 * s * c * ey + (c * c - s * s) * gxy
            dirs = (e1, e2) if p["mat"] == "F" else (e1,)
            for e in dirs:
                out["ft"] = np.maximum(out["ft"], e / EPS_T)
                out["fc"] = np.maximum(out["fc"], -e / EPS_C)
            out["fs"] = np.maximum(out["fs"], np.abs(g12) / GAM)
            if p["mat"] == "U":
                out["fm"] = np.maximum(out["fm"], e2 / EPS_2T_ULT)
        z += p["t"]
    allm = np.stack([out["ft"], out["fc"], out["fs"], out["fm"]], 1)
    out["fi"] = allm.max(1)
    out["mode"] = allm.argmax(1)
    return out


MODE_NAMES = ["fibre tension", "fibre compression", "in-plane shear", "transverse tension (matrix)"]

if __name__ == "__main__":
    qi = [("F", 45), ("U", 0), ("U", 45), ("U", -45), ("U", 90), ("U", 90), ("U", -45), ("U", 45), ("U", 0), ("F", 45)]
    p = shellprop(qi)
    print("check laminate: h=%.3f mm  Ex=%.0f Ey=%.0f Gxy=%.0f MPa  areal mass %.2f kg/m2" % (p.h, p.e1, p.e2, p.g12, areal_mass(qi) * 1e6))
