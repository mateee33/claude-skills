"""Verification: cantilever tube, shell FE vs Timoshenko beam theory (isotropic and laminated)."""
import sys, time
sys.path.insert(0, "src")
import numpy as np
from shellfe import mesh_from_sdf, ShellModel, boundary_nodes
from pyfe3d.shellprop_utils import laminated_plate, isotropic_plate

Rm, L, t, E, nu, Pz = 30.0, 400.0, 2.0, 70000.0, 0.3, 1000.0


def sdf(P):  # tube along x from -20 to L+20, radius Rm
    return np.sqrt(P[:, 1] ** 2 + P[:, 2] ** 2) - Rm


def run(h, prop, label):
    t0 = time.time()
    V, F = mesh_from_sdf(sdf, ([-25, -Rm - 8, -Rm - 8], [L + 25, Rm + 8, Rm + 8]), h,
                         clip=lambda P: (P[:, 0] > 0) & (P[:, 0] < L))
    m = ShellModel(V, F)
    xmat = np.tile([1.0, 0, 0], (len(F), 1))
    m.set_properties([prop], np.zeros(len(F), int), xmat)
    b = boundary_nodes(F)
    root = b[V[b, 0] < L / 2]; tip = b[V[b, 0] > L / 2]
    m.add_spider("root", root, [V[root, 0].mean(), 0, 0])
    m.add_spider("tip", tip, [V[tip, 0].mean(), 0, 0])
    m.assemble(); m.factorize([("root", [0, 1, 2, 3, 4, 5])])
    u, reac, ur = m.solve({"tip": [0, 0, Pz, 0, 0, 0]})
    Le = V[tip, 0].mean() - V[root, 0].mean()
    d = m.master_disp(ur, "tip")
    Rr = m.reaction_at(reac, "root")
    e0, kp = m.strains(u)
    return dict(label=label, h=h, nodes=len(V), tris=len(F), Le=Le, w_tip=d[2], reaction=Rr,
                exx_max=np.abs(e0[:, 0]).max(), secs=time.time() - t0, model=m, e0=e0)


iso = isotropic_plate(thickness=t, E=E, nu=nu)
print("isotropic tube")
for h in (10.0, 6.0, 4.0):
    r = run(h, iso, "iso")
    Le = r["Le"]; I = np.pi * Rm ** 3 * t; A = 2 * np.pi * Rm * t; G = E / (2 * (1 + nu))
    w_beam = Pz * Le ** 3 / (3 * E * I) + Pz * Le / (G * A / 2)
    eps_beam = Pz * Le * Rm / (E * I)
    print(f" h={h:4.1f} nodes={r['nodes']:6d} tris={r['tris']:6d} w_tip={r['w_tip']:.4f} beam={w_beam:.4f} ratio={r['w_tip']/w_beam:.4f}"
          f"  exx_max={r['exx_max']*1e6:.0f}ue beam_root={eps_beam*1e6:.0f}ue  Rz={r['reaction'][2]:.2f} My={r['reaction'][4]:.1f} (expect {-Pz:.0f}, {Pz*Le:.0f})  {r['secs']:.1f}s")
# laminated tube: [0/45/-45/90]s T700 UD
lam = (125000., 8410., 0.31, 4230., 4230., 3000.)
stack = [0, 45, -45, 90, 90, -45, 45, 0]
prop = laminated_plate(stack=stack, plyt=0.25, laminaprop=lam)
Ex = prop.e1; Gxy = prop.g12
print("quasi-isotropic laminate tube: Ex=%.0f Gxy=%.0f h=%.2f" % (Ex, Gxy, prop.h))
for h in (10.0, 6.0, 4.0):
    r = run(h, prop, "lam")
    Le = r["Le"]; I = np.pi * Rm ** 3 * prop.h; A = 2 * np.pi * Rm * prop.h
    w_beam = Pz * Le ** 3 / (3 * Ex * I) + Pz * Le / (Gxy * A / 2)
    print(f" h={h:4.1f} nodes={r['nodes']:6d} w_tip={r['w_tip']:.4f} beam={w_beam:.4f} ratio={r['w_tip']/w_beam:.4f}  {r['secs']:.1f}s")
