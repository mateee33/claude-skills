"""The V6 geometry as first packaged in 3-D, before the mid-plane correction forced a redesign.

Runs it with the shell on the modelled surface (as V1-V5 were analysed) and on the laminate mid-plane (corrected), and
writes results/V6/as_first_packaged.json. Kept so that the before/after quoted in DESIGN_V6.md can be reproduced."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import designs, swingarm_fe as SW, run_structure as RSt, frame_fe as FE
F, U = "F", "U"; sym = lambda h: h + h[::-1]
def old():
    d = designs.v6()
    A = (-439.86, 11.0); S = d["pts"]["S"]; P = d["pts"]["P"]
    ux, uy = S[0]-A[0], S[1]-A[1]; un = (ux**2+uy**2)**0.5; U1 = (A[0]+115*ux/un, A[1]+115*uy/un)
    d["swingarm"] = dict(layout="v6",
        lower_path=[(A[0], A[1]-12.0, 88.0, 15.0, 12.0), (-330.0, 20.0, 81.0, 17.0, 12.5), (-260.0, 34.0, 64.0, 18.0, 11.5), (-80.0, 72.0, 45.5, 20.0, 12.5)],
        upper_path=[(A[0], A[1], 88.0, 14.0, 7.5), (U1[0], U1[1], 85.0, 14.5, 8.5), (S[0], S[1], 51.0, 15.0, 10.0)],
        upright_path=[(S[0], S[1], 51.0, 16.0, 9.0), (P[0]+0.45*(S[0]-P[0]), P[1]+0.45*(S[1]-P[1]), 40.0, 16.0, 7.5), (P[0], P[1], 38.5, 16.0, 7.0)],
        strut_path=[(-66.0, 84.0, 38.5, 15.0, 7.0), (P[0], P[1], 38.5, 15.0, 7.0)],
        yoke_box=(-80.0, -60.0, 52.0, 92.0, 58.0), eye_r=20.0, eye_z=(31.0, 46.5), lug_r=16.0, lug_z=(38.5, 63.5), drop_r=19.0, drop_z=(78.5, 100.0),
        knee_patches=[((-80.0, 68.0), 44.0)])
    L = SW.sw_layups()
    L["spar"] = sym([(F,45),(U,0),(U,0),(U,45),(U,-45),(U,0),(U,0),(U,45),(U,-45),(U,90)])
    L["knee"] = sym([(F,45),(U,0),(U,0),(U,45),(U,-45),(U,0),(U,0),(U,45),(U,-45),(U,0),(U,0),(U,45),(U,-45),(U,90)])
    L["node"] = sym([(F,45),(U,0),(U,90),(U,45),(U,-45),(U,0),(U,0),(U,45),(U,-45),(U,0),(U,90),(U,45),(U,-45),(U,0)])
    L["strut"] = sym([(F,45),(U,0),(U,0),(U,45),(U,-45),(U,0),(U,0),(U,45),(U,-45),(U,0),(U,90)])
    L["yoke"] = sym([(F,45),(U,45),(U,-45),(U,0),(U,90),(U,45),(U,-45),(U,0),(U,90),(U,45),(U,-45),(U,0),(U,90),(U,45),(U,-45),(U,0),(U,90)])
    d["sw_layups"] = L
    d["sections"] = dict(dt_hd=(41.0, 34.0), sm_hw=26.0)
    Lf = dict(d["layups"]); Lf["head_tube"] = FE.base_layups()["head_tube"]; d["layups"] = designs.v5()["layups"] if designs.v5().get("layups") else Lf
    return d
out = {}
for tag, inset in (("surface", None), ("midplane", "half_thickness")):
    d = old()
    if inset is None: d.pop("shell_inset")
    so, _ = SW.run(d, 4.0, verbose=False)
    d = old()
    if inset is None: d.pop("shell_inset")
    st, _ = RSt.solve_cases(d, 6.0, verbose=False)
    out[tag] = dict(swingarm={k: round(c["governing"]["fi"], 3) for k, c in so["cases"].items()}, swingarm_lateral_stiffness=round(so["lateral_stiffness_N_per_mm"]),
                    swingarm_laminate_kg=round(so["mass_total"], 3),
                    front_triangle={k: (c["governing"]["zone"], round(c["governing"]["fi"], 3)) for k, c in st["cases"].items()}, front_triangle_laminate_kg=round(st["mass_total"], 3),
                    head_tube_zone_LC2d=round(st["cases"]["LC2d"]["zones"]["head_tube"]["fi"], 3))
    print(tag, out[tag], flush=True)
json.dump(out, open(os.path.join(os.path.dirname(__file__), "..", "results", "V6", "as_first_packaged.json"), "w"), indent=1)
