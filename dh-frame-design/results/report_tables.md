### Table A. Load cases: limit forces at the tyres and resulting interface forces (V5)

| Case | Rear tyre x / y / z (kN) | Front tyre x / y / z (kN) | Hands x / y (kN) | Feet at BB x / y / z (kN) | BB moment roll / yaw (N m) | Shock | Push links (total) | Main pivot | Rocker pivot | Head tube upper / lower bearing |
|---|---|---|---|---|---|---|---|---|---|---|
| LC1 Hard braking into a compression | -0.50 / 1.57 / 0.00 | -1.50 / 3.00 / 0.00 | 0.80 / -1.20 | 1.20 / -3.37 / -0.00 | -0 / -0 | 7.0 | 4.7 | 3.8 | 11.0 | 3.5 / 3.4 |
| LC2a Bottom-out landing, rider centred | 0.00 / 8.30 / 0.00 | 0.00 / 6.09 / 0.00 | 0.00 / -2.00 | -0.00 / -12.39 / -0.00 | -0 / 0 | 18.0 | 18.7 | 14.3 | 32.4 | 11.6 / 13.4 |
| LC2b Bottom-out landing, weight back | 0.00 / 9.20 / 0.00 | 0.00 / 4.62 / 0.00 | 0.00 / 1.00 | -0.00 / -14.82 / -0.00 | -0 / 0 | 19.9 | 20.7 | 15.9 | 35.9 | 8.4 / 10.9 |
| LC2c Bottom-out landing, weight forward | 0.00 / 9.20 / 0.00 | 0.00 / 7.24 / 0.00 | 0.00 / -3.00 | -0.00 / -13.44 / -0.00 | -0 / 0 | 19.9 | 20.7 | 15.9 | 35.9 | 14.0 / 15.9 |
| LC2d Front wheel cases a knuckle | 0.00 / 7.00 / 0.00 | -5.66 / 5.66 / 0.00 | 0.00 / 0.00 | 5.66 / -12.66 / 0.00 | 0 / -0 | 18.8 | 16.1 | 11.0 | 32.9 | 21.3 / 23.8 |
| LC3 Sideways landing | 0.00 / 5.50 / 1.50 | 0.00 / 3.23 / 1.50 | 0.00 / 0.00 | -0.00 / -8.73 / -3.00 | 458 / 631 | 12.1 | 12.5 | 9.4 | 22.3 | 10.2 / 12.3 |
| LC4 Cornering compression | 0.00 / 1.71 / 0.60 | 0.00 / 0.98 / 0.40 | 0.00 / 0.00 | -0.00 / -2.69 / -1.00 | 216 / 88 | 4.4 | 3.9 | 2.8 | 7.8 | 3.2 / 3.8 |

Forces in kN at limit load; ultimate = 1.5 × these. The BB column is the support reaction (what the rider's feet must supply). Largest difference between the finite-element support reaction and the independent whole-bike statics: 5.6e-08 N.

### Table B. Composite strain check at ultimate load, by load case (simulated)

| Case | Front triangle: governing zone | Index | Margin | Mode | Swingarm: governing zone | Index | Mode |
|---|---|---|---|---|---|---|---|
| LC1 | boss | 0.29 | +250% | fibre compression | node | 0.20 | fibre compression |
| LC2a | boss | 0.66 | +51% | fibre compression | node | 0.34 | transverse tension (matrix) |
| LC2b | boss | 0.74 | +35% | fibre compression | node | 0.38 | transverse tension (matrix) |
| LC2c | boss | 0.74 | +36% | fibre compression | node | 0.38 | transverse tension (matrix) |
| LC2d | boss | 0.84 | +19% | fibre compression | node | 0.27 | transverse tension (matrix) |
| LC3 | ht_junction | 0.74 | +35% | transverse tension (matrix) | knee | 0.72 | fibre tension |
| LC4 | ht_junction | 0.22 | +355% | transverse tension (matrix) | knee | 0.27 | fibre tension |

Index = largest ply strain ÷ design strain limit, at 1.5 × limit load, averaged over a 12 mm (front triangle) or 10 mm (swingarm) patch at the hot spot. ≤ 1.00 passes.

### Table C. Joints, pins, bearings and bonded inserts at ultimate load (calculated, V5)

| Check | Demand | Capacity | Unit | Margin | Basis |
|---|---|---|---|---|---|
| Shock eye pin bending (12.7 mm steel pin, both ends of the shock) | 855 | 1000 | MPa | +17% | calculated; simply supported pin, load spread over the 22 mm eyelet; yield criterion; pin strength unverified |
| Shock eye pin double shear | 118 | 580 | MPa | +391% | calculated |
| Shock mount clevis tabs, bearing in 7075 inserts (2 x 8 mm) | 147 | 754 | MPa | +413% | calculated; bearing yield taken as 1.5 x tensile yield |
| Shock mount top-hat bushes bearing on carbon lug walls (2 x 20 mm OD x 8 mm wall) | 93 | 250 | MPa | +167% | estimated; load carried in bearing; the bond only retains the bushes |
| Rocker pivot axle double shear (17 mm Ti-6Al-4V, 11 mm bore) | 204 | 550 | MPa | +169% | calculated |
| Rocker pivot plain bearings, pressure at ultimate (2 x 17 x 12 mm) | 132 | 250 | MPa | +89% | calculated; static rating |
| Rocker pivot plain bearings, pressure at limit | 88 | 140 | MPa | +59% | calculated; dynamic rating |
| Rocker pivot sleeve bearing on carbon seat mast (22 mm sleeve x 56 mm) | 44 | 250 | MPa | +471% | estimated |
| Push link column buckling (each, 7075, 12 x 16 mm, 130 mm) | 15523 | 96475 | N | +521% | calculated; Euler, pinned ends |
| Push link compressive stress | 81 | 503 | MPa | +522% | calculated |
| Push link eye plain bearings at limit (12 x 10 mm) | 86 | 140 | MPa | +62% | calculated; dynamic rating |
| Main pivot axle bending (20/14 mm Ti-6Al-4V, 10 mm overhang) | 389 | 880 | MPa | +126% | calculated |
| Main pivot plain bearing pressure at limit (20 x 16 mm each side) | 48 | 140 | MPa | +190% | calculated; dynamic rating |
| Main pivot: same load on a 6004 ball bearing (for comparison) | 15459 | 5000 | N | -68% | calculated; static rating C0 of an SKF 6004; negative margin is why plain bearings are specified |
| Main pivot sleeve bearing on carbon (26 mm sleeve x 56 mm) | 16 | 250 | MPa | +1429% | estimated |
| Lower headset cup bearing on carbon head tube (56 x 12 mm) | 53 | 250 | MPa | +371% | estimated |
| Upper headset cup bearing on carbon head tube (56 x 12 mm) | 48 | 250 | MPa | +426% | estimated |
| BB shell bearing pressure on carbon (46 x 83 mm) | 6 | 250 | MPa | +4195% | estimated |
| Dropout insert, axle bearing (12 x 10 mm) | 73 | 754 | MPa | +931% | calculated |
| Dropout insert bond shear (3600 mm2 each) | 2 | 5 | MPa | +112% | estimated; average shear; insert is also wrapped by the spar laminate |
| Idler stub bending (16 mm Ti-6Al-4V, 20 mm overhang) | 582 | 880 | MPa | +51% | calculated; sprint load, 2.0 kN on one pedal |

### Table D. Frame mass build-up (V5)

| Item | kg | Basis |
|---|---|---|
| Front triangle laminate (shell model area x areal mass) | 2.103 | calculated |
| Front triangle overlaps, ply drops, resin fillets (+8 %) | 0.168 | estimated |
| Front triangle inserts: BB sleeve, headset seats, pivot and rocker sleeves, shock and idler inserts | 0.290 | estimated |
| Main pivot axle (Ti 20/14 x 110) and rocker axle (Ti 17/11 x 80) | 0.125 | calculated |
| Swingarm laminate (shell model) | 0.838 | calculated |
| Swingarm overlaps and fillets (+8 %) | 0.067 | estimated |
| Swingarm inserts: dropouts, brake mount, pivot and link bushes | 0.175 | estimated |
| Rocker (7075-T6 yoke) with bushes | 0.195 | estimated |
| Push links (2 x 7075) with bushes | 0.160 | estimated |
| Pins, bolts, idler sprocket and stub | 0.215 | estimated |
| Frame protection (down-tube guard, spar and chain protection) and paint | 0.250 | estimated |
| Shock-mount lug wall build-up to 8 mm and top-hat bushes | 0.020 | estimated |
| **Total (goal G2 definition)** | **4.61** | ±12 % → 4.05–5.16 kg |

### Table E. Revision log

| Rev | Leverage start → end | Pressure at 25 % sag | Mid-stroke ratio | End ratio | Spring drop height | Shock force at limit | Front triangle worst index | Swingarm worst index | Worst joint margin | Frame mass | All structural checks |
|---|---|---|---|---|---|---|---|---|---|---|---|
| V1 | 3.08 → 2.30 | 202 psi / 13.9 bar (61% of max) | 2.06 | 7.06 | 0.393 m | 21.2 kN | 1.86 (LC3, ht_junction) | 1.29 (LC3) | -80% | 3.75 kg | FAIL |
| V2 | 3.48 → 2.17 | 229 psi / 15.8 bar (69% of max) | 2.31 | 8.08 | 0.439 m | 19.9 kN | 1.86 (LC3, ht_junction) | 1.07 (LC3) | -79% | 3.78 kg | FAIL |
| V3 | 3.48 → 2.17 | 229 psi / 15.8 bar (69% of max) | 2.31 | 8.08 | 0.439 m | 19.9 kN | 0.84 (LC2d, boss) | 1.07 (LC3) | -79% | 4.37 kg | FAIL |
| V4 | 3.48 → 2.17 | 229 psi / 15.8 bar (69% of max) | 2.31 | 8.08 | 0.439 m | 19.9 kN | 0.84 (LC2d, boss) | 0.72 (LC3) | -79% | 4.59 kg | FAIL |
| V5 | 3.48 → 2.17 | 229 psi / 15.8 bar (69% of max) | 2.31 | 8.08 | 0.439 m | 19.9 kN | 0.84 (LC2d, boss) | 0.72 (LC3) | +17% | 4.61 kg | pass |
| V6 | 3.48 → 2.17 | 229 psi / 15.8 bar (69% of max) | 2.31 | 8.08 | 0.439 m | 19.9 kN | 0.82 (LC2d, ht_junction) | 0.69 (LC3) | +17% | 4.77 kg | pass |

### Table F. Goal G1 with the same shock model and rule (25 % sag, 68 kg)

| Bike | Leverage curve used | Tokens | Pressure | a. Force at 60 % ÷ W (2.3–2.8) | b. Force at 100 % ÷ W (≥ 6.5) | c. Spring drop height (≥ 0.50 m) | d. Pressure ÷ max (≤ 75 %) |
|---|---|---|---|---|---|---|---|
| Custom V5 and V6 (same linkage) | simulated from the hard points, 3.48 → 2.17 | 2 | 229 psi | 2.31 | 8.08 | 0.439 | 69% |
| Sender CFR, 32.7 % chip | estimated, 3.23 → 2.17 | 0 | 214 psi | 2.11 | 7.44 | 0.400 | 65% |
| Sender CFR, 37 % chip | estimated, 3.33 → 2.10 | 0 | 222 psi | 2.17 | 7.88 | 0.414 | 67% |
| Supreme DH V5 | estimated, 3.45 → 2.60 | 0 | 231 psi | 2.02 | 5.52 | 0.403 | 70% |
