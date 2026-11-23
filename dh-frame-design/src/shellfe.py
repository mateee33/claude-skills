"""Composite shell finite-element helper built on pyfe3d (Tria3R elements).

Pipeline
  signed-distance function of the outer mould line -> marching cubes (scikit-image)
  -> isotropic remeshing (gpytoolbox, Botsch-Kobbelt) -> Tria3R laminated shells
  -> rigid "spider" interfaces by exact master/slave elimination -> sparse solve
  -> ply-by-ply strain recovery in material axes.

Units: N, mm, MPa. Global axes follow the frame coordinate system (see geometry.py).
"""
from __future__ import annotations
import numpy as np
from scipy.sparse import coo_matrix, csc_matrix
from scipy.sparse.linalg import splu, eigsh, LinearOperator
from pyfe3d import Tria3R, Tria3RData, Tria3RProbe, DOF, INT, DOUBLE
from pyfe3d.shellprop_utils import laminated_plate


# ---------------------------------------------------------------- meshing
def mesh_from_sdf(sdf, bounds, h, clip=None, iters=12, grid=None):
    """Triangulate the zero level set of sdf(points[N,3]) inside bounds=(lo,hi).

    clip : optional function(points)->bool array; triangles whose three vertices are
           all True are kept (used to open tube ends).
    """
    from skimage import measure
    import gpytoolbox as gpy
    lo, hi = np.asarray(bounds[0], float), np.asarray(bounds[1], float)
    g = grid or 0.6 * h
    n = np.maximum(((hi - lo) / g).astype(int) + 1, 4)
    axes = [np.linspace(lo[i], hi[i], n[i]) for i in range(3)]
    X, Y, Z = np.meshgrid(*axes, indexing="ij")
    P = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    vals = np.empty(len(P))
    step = 400000
    for i in range(0, len(P), step):
        vals[i:i + step] = sdf(P[i:i + step])
    vol = vals.reshape(X.shape)
    spacing = tuple((hi - lo) / (n - 1))
    V, F, _, _ = measure.marching_cubes(vol, 0.0, spacing=spacing)
    V = V + lo
    V, F = gpy.remesh_botsch(V.astype(np.float64), F.astype(np.int32), iters, h, True)
    if clip is not None:
        keep = clip(V)
        F = F[keep[F].all(1)]
    # drop unused vertices and tiny disconnected islands
    used = np.unique(F)
    remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    V, F = V[used], remap[F]
    F = _largest_component(F, len(V))
    used = np.unique(F)
    remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    V, F = V[used], remap[F]
    # orient so normals point along +grad(sdf) (outward)
    c = V[F].mean(1)
    nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-30
    eps = 0.05 * h
    out = sdf(c + eps * nrm) - sdf(c - eps * nrm)
    flip = out < 0
    F[flip] = F[flip][:, [0, 2, 1]]
    return V, F


def _largest_component(F, nv):
    from scipy.sparse.csgraph import connected_components
    i = np.concatenate([F[:, 0], F[:, 1], F[:, 2]])
    j = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
    A = coo_matrix((np.ones(len(i)), (i, j)), shape=(nv, nv))
    _, lab = connected_components(A, directed=False)
    fl = lab[F[:, 0]]
    big = np.bincount(fl).argmax()
    return F[fl == big]


def boundary_nodes(F):
    e = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    u, cnt = np.unique(e, axis=0, return_counts=True)
    return np.unique(u[cnt == 1])


# ---------------------------------------------------------------- model
class ShellModel:
    def __init__(self, V, F):
        self.V = np.ascontiguousarray(V, float)
        self.F = np.ascontiguousarray(F, int)
        self.nn = len(V)
        self.masters = {}            # name -> dict(node index, slaves, x)
        self.extra = []              # extra node coordinates (masters)
        self.props = None
        self.elem_prop = None
        self.elem_xmat = None

    # ---- properties
    def set_properties(self, props, elem_prop, elem_xmat):
        """props: list of ShellProp; elem_prop: int index per element;
        elem_xmat: (ne,3) global vector giving the laminate 0-degree direction."""
        self.props, self.elem_prop = props, np.asarray(elem_prop, int)
        self.elem_xmat = np.asarray(elem_xmat, float)

    # ---- interfaces
    def add_spider(self, name, slaves, x_master):
        idx = self.nn + len(self.extra)
        self.extra.append(np.asarray(x_master, float))
        self.masters[name] = dict(node=idx, slaves=np.asarray(slaves, int), x=np.asarray(x_master, float))
        return idx

    # ---- assembly
    def assemble(self):
        V, F = self.V, self.F
        ne = len(F)
        data, probe = Tria3RData(), Tria3RProbe()
        size = data.KC0_SPARSE_SIZE
        r = np.zeros(size * ne, dtype=INT); c = np.zeros(size * ne, dtype=INT)
        v = np.zeros(size * ne, dtype=DOUBLE)
        xf = V.flatten()
        self.elems = []
        k0 = 0
        for e in range(ne):
            t = Tria3R(probe)
            n1, n2, n3 = F[e]
            t.n1, t.n2, t.n3 = int(n1), int(n2), int(n3)
            t.c1, t.c2, t.c3 = DOF * int(n1), DOF * int(n2), DOF * int(n3)
            t.init_k_KC0 = k0
            xm = self.elem_xmat[e]
            t.update_rotation_matrix(xf, float(xm[0]), float(xm[1]), float(xm[2]))
            t.update_probe_xe(xf)
            t.update_KC0(r, c, v, self.props[self.elem_prop[e]])
            k0 += size
            self.elems.append(t)
        ntot = self.nn + len(self.extra)
        N = DOF * ntot
        self.N = N
        self.K = coo_matrix((v, (r, c)), shape=(N, N)).tocsc()
        self._build_T()
        return self.K

    def _build_T(self):
        """u_full = T u_red : slaves follow their master rigidly (all 6 dof)."""
        N = self.N
        slave_of = {}
        for m in self.masters.values():
            for s in m["slaves"]:
                slave_of[int(s)] = m
        ntot = self.nn + len(self.extra)
        red_index = -np.ones(N, int)
        k = 0
        for nd in range(ntot):
            if nd in slave_of:
                continue
            red_index[DOF * nd:DOF * nd + DOF] = np.arange(k, k + DOF); k += DOF
        rows, cols, vals = [], [], []
        for nd in range(ntot):
            if nd not in slave_of:
                for d in range(DOF):
                    rows.append(DOF * nd + d); cols.append(red_index[DOF * nd + d]); vals.append(1.0)
            else:
                m = slave_of[nd]
                mb = red_index[DOF * m["node"]]
                rx, ry, rz = self.V[nd] - m["x"]
                # u_s = u_m + theta x r ; theta_s = theta_m
                G = np.array([[0, rz, -ry], [-rz, 0, rx], [ry, -rx, 0]], float)
                for d in range(3):
                    rows.append(DOF * nd + d); cols.append(mb + d); vals.append(1.0)
                    for q in range(3):
                        if G[d, q] != 0:
                            rows.append(DOF * nd + d); cols.append(mb + 3 + q); vals.append(G[d, q])
                    rows.append(DOF * nd + 3 + d); cols.append(mb + 3 + d); vals.append(1.0)
        self.T = csc_matrix((vals, (rows, cols)), shape=(N, k))
        self.red_index = red_index
        self.nred = k

    # ---- solve
    def factorize(self, fixed):
        """fixed: list of (master name, dof list). Returns nothing; stores LU."""
        Kr = (self.T.T @ self.K @ self.T).tocsc()
        fix = []
        for name, dofs in fixed:
            mb = self.red_index[DOF * self.masters[name]["node"]]
            fix += [mb + d for d in dofs]
        fix = np.array(sorted(fix), int)
        free = np.setdiff1d(np.arange(self.nred), fix)
        self.Kr, self.free, self.fix = Kr, free, fix
        self.lu = splu(Kr[free][:, free].tocsc())

    def solve(self, loads):
        """loads: dict master name -> 6-vector (Fx,Fy,Fz,Mx,My,Mz) applied at the master.
        Returns full displacement vector and reactions at fixed dofs."""
        f = np.zeros(self.nred)
        for name, vec in loads.items():
            mb = self.red_index[DOF * self.masters[name]["node"]]
            f[mb:mb + 6] += np.asarray(vec, float)
        ur = np.zeros(self.nred)
        ur[self.free] = self.lu.solve(f[self.free])
        reac = self.Kr[self.fix] @ ur - f[self.fix]
        u = self.T @ ur
        return u, dict(zip(self.fix.tolist(), reac.tolist())), ur

    def master_disp(self, ur, name):
        mb = self.red_index[DOF * self.masters[name]["node"]]
        return ur[mb:mb + 6]

    def reaction_at(self, reac, name):
        mb = self.red_index[DOF * self.masters[name]["node"]]
        return np.array([reac.get(mb + d, 0.0) for d in range(6)])

    # ---- strain recovery
    def strains(self, u):
        """Mid-surface strains and curvatures per element, in MATERIAL axes
        (x = laminate 0 deg direction projected on the element, z = element normal).
        Returns eps0 (ne,3) [exx, eyy, gxy] and kap (ne,3)."""
        V, F = self.V, self.F
        ne = len(F)
        p1, p2, p3 = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
        ex = p2 - p1; ex /= np.linalg.norm(ex, axis=1)[:, None]
        ez = np.cross(p2 - p1, p3 - p1); A2 = np.linalg.norm(ez, axis=1); ez /= A2[:, None]
        ey = np.cross(ez, ex)
        R = np.stack([ex, ey, ez], axis=1)                       # rows = element axes
        U = u.reshape(-1, 6)
        loc = lambda P: np.einsum("eij,ej->ei", R, P)
        x1, x2, x3 = loc(p1 - p1), loc(p2 - p1), loc(p3 - p1)
        area = 0.5 * A2
        S_x = np.stack([x2[:, 1] - x3[:, 1], x3[:, 1] - x1[:, 1], x1[:, 1] - x2[:, 1]], 1) / (2 * area[:, None])
        S_y = np.stack([x3[:, 0] - x2[:, 0], x1[:, 0] - x3[:, 0], x2[:, 0] - x1[:, 0]], 1) / (2 * area[:, None])
        ue = np.stack([loc(U[F[:, i], :3]) for i in range(3)], 1)   # (ne,3 nodes,3)
        re = np.stack([loc(U[F[:, i], 3:]) for i in range(3)], 1)
        exx = np.sum(S_x * ue[:, :, 0], 1)
        eyy = np.sum(S_y * ue[:, :, 1], 1)
        gxy = np.sum(S_y * ue[:, :, 0] + S_x * ue[:, :, 1], 1)
        # Allman enrichment at the centroid (drilling_model = 0), ported from pyfe3d tria3r.pyx
        xe = np.stack([x1, x2, x3], 1)
        S = np.full((ne, 3), 1 / 3)
        ei, ej = [0, 1, 2], [1, 2, 0]
        cu = np.stack([0.125 * (xe[:, ei[k], 1] - xe[:, ej[k], 1]) for k in range(3)], 1)
        cv = np.stack([0.125 * (xe[:, ej[k], 0] - xe[:, ei[k], 0]) for k in range(3)], 1)
        Sbx = np.stack([4 * (S_x[:, ei[k]] * S[:, ej[k]] + S[:, ei[k]] * S_x[:, ej[k]]) for k in range(3)], 1)
        Sby = np.stack([4 * (S_y[:, ei[k]] * S[:, ej[k]] + S[:, ei[k]] * S_y[:, ej[k]]) for k in range(3)], 1)
        prev = [2, 0, 1]
        rz = re[:, :, 2]
        for m in range(3):
            exx += (cu[:, m] * Sbx[:, m] - cu[:, prev[m]] * Sbx[:, prev[m]]) * rz[:, m]
            eyy += (cv[:, m] * Sby[:, m] - cv[:, prev[m]] * Sby[:, prev[m]]) * rz[:, m]
            gxy += ((cu[:, m] * Sby[:, m] - cu[:, prev[m]] * Sby[:, prev[m]])
                    + (cv[:, m] * Sbx[:, m] - cv[:, prev[m]] * Sbx[:, prev[m]])) * rz[:, m]
        kxx = np.sum(S_x * re[:, :, 1], 1)
        kyy = -np.sum(S_y * re[:, :, 0], 1)
        kxy = np.sum(S_y * re[:, :, 1] - S_x * re[:, :, 0], 1)
        # rotate from element axes to material axes
        xm = self.elem_xmat
        th = np.arctan2(np.einsum("ej,ej->e", xm, ey), np.einsum("ej,ej->e", xm, ex))
        c, s = np.cos(th), np.sin(th)

        def rotate(a, b, g):
            return (c * c * a + s * s * b + s * c * g,
                    s * s * a + c * c * b - s * c * g,
                    -2 * s * c * a + 2 * s * c * b + (c * c - s * s) * g)
        e0 = np.stack(rotate(exx, eyy, gxy), 1)
        kp = np.stack(rotate(kxx, kyy, kxy), 1)
        self._geom = dict(R=R, area=area, theta=th)
        return e0, kp


def buckling(model, u, nmodes=4):
    """Linear buckling: load multipliers lambda with (K + lambda KG) phi = 0 for the stress state of displacement u."""
    m = model
    ne = len(m.F)
    data = Tria3RData()
    size = data.KG_SPARSE_SIZE
    r = np.zeros(size * ne, dtype=INT); c = np.zeros(size * ne, dtype=INT); v = np.zeros(size * ne, dtype=DOUBLE)
    xf = m.V.flatten()
    uu = np.ascontiguousarray(u, dtype=DOUBLE)
    k0 = 0
    for e, t in enumerate(m.elems):
        t.init_k_KG = k0
        t.update_probe_xe(xf)
        t.update_probe_ue(uu)
        t.update_KG(r, c, v, m.props[m.elem_prop[e]])
        k0 += size
    KG = coo_matrix((v, (r, c)), shape=(m.N, m.N)).tocsc()
    KGr = (m.T.T @ KG @ m.T).tocsc()[m.free][:, m.free]
    lu = m.lu
    n = len(m.free)
    # (K^-1 (-KG)) phi = (1/lambda) phi  -> largest positive eigenvalues give the lowest positive load multipliers
    op = LinearOperator((n, n), matvec=lambda x: lu.solve(-(KGr @ x)), dtype=float)
    from scipy.sparse.linalg import eigs
    vals, vecs = eigs(op, k=nmodes, which="LR", tol=1e-5, maxiter=4000)
    lam_ = np.sort(1.0 / vals.real[vals.real > 1e-12])
    return lam_
