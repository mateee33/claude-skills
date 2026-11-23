"""Verification: linear buckling of an axially compressed isotropic cylinder, shell FE vs the classical formula."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from shellfe import mesh_from_sdf, ShellModel, boundary_nodes, buckling
from pyfe3d.shellprop_utils import isotropic_plate

Rm, L, t, E, nu = 30.0, 160.0, 0.6, 70000.0, 0.3
V, F = mesh_from_sdf(lambda P: np.sqrt(P[:, 1] ** 2 + P[:, 2] ** 2) - Rm, ([-10, -Rm - 6, -Rm - 6], [L + 10, Rm + 6, Rm + 6]), 3.0,
                     clip=lambda P: (P[:, 0] > 0) & (P[:, 0] < L))
m = ShellModel(V, F)
m.set_properties([isotropic_plate(thickness=t, E=E, nu=nu)], np.zeros(len(F), int), np.tile([1.0, 0, 0], (len(F), 1)))
b = boundary_nodes(F); root = b[V[b, 0] < L / 2]; tip = b[V[b, 0] > L / 2]
m.add_spider("root", root, [V[root, 0].mean(), 0, 0]); m.add_spider("tip", tip, [V[tip, 0].mean(), 0, 0])
m.assemble(); m.factorize([("root", [0, 1, 2, 3, 4, 5])])
u, reac, ur = m.solve({"tip": [-1000.0, 0, 0, 0, 0, 0]})
lam_ = buckling(m, u, 4)
P_classical = 2 * np.pi * E * t ** 2 / np.sqrt(3 * (1 - nu ** 2))
print("FE critical load %.0f N, classical %.0f N, ratio %.3f" % (lam_[0] * 1000, P_classical, lam_[0] * 1000 / P_classical))
