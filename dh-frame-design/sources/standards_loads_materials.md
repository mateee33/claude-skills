# Standards, measured loads and material data — source record

Collected 2026-11-23. **P** = primary (standard preview text, manufacturer datasheet, paper read in full);
**S** = secondary; **SNIP** = search snippet only (unverified). "NOT FOUND" = not on any page actually read.

## A. Test standards

### ISO 4210:2023 (values read from the official iTeh preview; full text is paywalled) — P
- Scope 4210-2: young adult, city/trekking, mountain and racing bicycles. Excluded verbatim: "bicycles designed and equipped for use in
  severe applications such as sanctioned competition events, stunting, or aerobatic manoeuvres." Downhill/freeride are not named;
  only one "mountain bicycle" class exists.
  https://standards.iteh.ai/catalog/standards/iso/93e6d156-fc7a-4fc2-84e4-7acb6f711cce/iso-4210-2-2023
- 4210-6 mountain-bike frame tests: https://standards.iteh.ai/catalog/standards/iso/50799ea4-45e0-4601-acc4-043e499c1fa1/iso-4210-6-2023
  - Falling mass impact: 22.5 kg from 360 mm onto a roller in the fork dropouts (≈79 J).
  - Falling frame impact: masses 30 kg seat post, 10 kg steering head, 50 kg bottom bracket; drop 300 mm; repeated twice.
  - Pedalling fatigue: 1 200 N per pedal, 7.5° inclination, 150 mm from centreline, 100 000 cycles.
  - Horizontal fatigue: +1 200 N / −600 N at fork dropouts, 50 000 cycles.
  - Vertical fatigue: 1 200 N, 70 mm behind seat-post intersection, 50 000 cycles.
  - Rear brake mount fatigue: 500 N / 200 N, 20 000 cycles. Fork static bending 1 500 N.
- ISO 4210-2 braking requirement (MTB, dry, 25 km/h, both brakes): stop ≤ 6 m (≈0.41 g mean, derived).

### ASTM F2043 use conditions — S (retailer reproduction of the table; standard paywalled)
- Condition 3: jumps and drops < 61 cm. Condition 4: downhill grades on rough trails < 40 km/h, jumps < 122 cm.
- Condition 5: "extreme jumping; or downhill grades on rough trails at speeds in excess of 40 km/h; or a combination thereof." No numeric jump height.
  https://cdn.shopify.com/s/files/1/1430/1526/files/ASTM_F2043_TABLE_R-1.pdf
- Condition 4/5 frame specification with load values: NOT FOUND (F2614 covers Condition 3).

### EFBE Tri-Test — P (lab's own pages)
- Modules: fatigue, maximum load (permanent deformation measured), overload (no catastrophic failure), stiffness; "up to eight individual test stages".
- "ISO 4210 only knows one type of MTB"; EFBE has programmes for XC … Downhill. Category 5 = "jumps and drops of more than 120 cm", downhill, freeride, dirt.
  https://www.efbe.de/tri-test-en.html
- Frame stages: TTF1 pedalling fatigue, TTF2 vertical fatigue, TTF3 horizontal/head-tube fatigue, STF1 rear brake mount fatigue, STF2 vertical
  rear-axle fatigue, STF3 lateral rear-axle fatigue, TTF4 max/overload jump/drop, TTF5 max/overload pedal.
  https://www.efbe.de/pdf/Test-order-1-frame-2024.pdf
- **Category 5 load levels: not published by EFBE.** Third-party figures (low confidence, S): single-pedal max ≈2 500 N; overload ≈7 000 N.
  https://www.mtb-news.de/?p=388014
- Zedler DH protocol: NOT FOUND. Frame-maker in-house DH load numbers (Canyon, Commencal, Trek, Specialized, Santa Cruz): NOT FOUND.

## B. Measured loads

| Source | Finding | Tag |
|---|---|---|
| Phillips, Kilgas, Jensen, ISBS 2015 — 8 riders, 76.6 kg, 130 mm trail bike, flat landing on force plates. https://ojs.ub.uni-konstanz.de/cpa/article/view/6619/5978 | Drop 0.29 / 0.48 / 0.67 m: summed peak vertical ground force 5 442 / 6 800 / 7 878 N = 6.1 / 7.6 / 8.9 × rider+bike weight (884.8 N). Rear 3 358 / 3 868 / 4 425 N; front 2 084 / 2 932 / 3 453 N. Authors: unknown how much the rider absorbed; sloped landings are future work. | P |
| Steck, Husung, Hassler, IFToMM D-A-CH 2022 — strain-gauged cranks, 140 mm bike, 75 kg rider. https://duepublico2.uni-due.de/servlets/MCRFileNodeServlet/duepublico_derivate_00075152/IFToMM_DACH_2022_paper_25.pdf | Downhill/jumps: 1 500 N vertical per pedal, 600–800 N horizontal per pedal. Cites Soden & Adeyefa: up to 2 000 N (2.4–3.0 × body weight). | P |
| Petrone et al., Procedia Eng. 2012 (strain-gauged DH frame) doi 10.1016/j.proeng.2012.04.088 | Exists; numeric peaks NOT FOUND (access refused). | SNIP |
| Lateral wheel/frame forces; landing-slope effect; rider leg energy share; Rampage telemetry | NOT FOUND | — |
| Beck, CMRSC XIV 2004 (116 radar-timed MTB stops) http://www.beckforensics.com/CMRSC14BeckBicycle.pdf | Both brakes 0.37–0.50 g (mean 0.44 g); cites pitch-over at ≈0.67 g. | P |
| Famiglietti et al., SAE 2020-01-0876 (abstract) | Front+rear 0.40–0.71 g on dry asphalt. | P (abstract) |
| Tyre friction coefficient on dry hardpack | NOT FOUND as a measurement. | — |

Rampage-class features and failures (journalism, no instrumentation, S):
- Rampage 2025: Bienvenido Alba — "the head tube broke off when landing an XXL drop".
  https://www.bike-magazin.de/en/competitions/red-bull-rampage-2025-the-massacre-the-super-competition-has-become-too-extreme/
- Vincent Tupin "Superdrop" 2025 (not Rampage): 25 m down, 14 m out; frame destroyed, front wheel folded. Gee Atherton, Rampage 2023: 22 m drop (crashed).
  https://www.bike-magazin.de/en/events/people-and-types/the-highest-drop-in-mountain-biking-vinny-t-jumps-the-superdrop/
- 2026 venue: 74 ft (22.6 m) step-down; canyon gap 22.6 m across / 19.2 m down. SNIP

## C. Materials

### Toray prepreg lamina data (P). RTA = 22 °C dry, ETW = 82 °C wet.
2510 system rev. 6/2025: https://www.toraycma.com/wp-content/uploads/2510-Prepreg-System.pdf
2511 system rev. 7/2023: https://www.toraycma.com/wp-content/uploads/2511-Prepreg-System.pdf

| Property | T700G UD 150 gsm (2510) RTA / ETW | T800S UD 200 gsm (2511) RTA | T700S-12K plain weave 190 gsm (2510) RTA / ETW |
|---|---|---|---|
| 0° tensile strength, MPa | 2 172 / 2 261 | 2 792 | 912 / 1 049 |
| 0° tensile modulus, GPa | 125 / 122 | 145 | 55.8 / 57.9 |
| 90° tensile strength, MPa | 44.3 / 25.9 | 51 | 772 / 892 |
| 90° tensile modulus, GPa | 8.41 / 6.34 | 9.0 | 56.0 / 54.2 |
| 0° compressive strength, MPa | 1 448 / 1 200 | 1 241 | 709 / 474 |
| 0° compressive modulus, GPa | 112 / 117 | 124 | 54.9 / 54.7 |
| In-plane shear strength, MPa | 154 / 95.1 | 90.3 (5 %) | 133 / 74.6 |
| In-plane shear modulus, GPa | 4.23 / 3.12 | 3.79 | 4.21 / 3.17 |
| Short-beam shear, MPa | 86.2 | 91.7 | 60 |
| ν12 | 0.31 | n/a | 0.04 |
| Open-hole compression, quasi-iso, MPa | 276 / 247 | 296 (ETW 232) | 267 / 227 |
| Compression after impact, quasi-iso, MPa | 137 | n/a | 185 |
| Fibre volume, % | 54.4 | 54.9 | 49.6 |
| Cured ply thickness, mm | 0.152 | 0.201 | 0.218 |
| Laminate density, g/cm³ | 1.517 | 1.54 | 1.502 |

Toray fibre sheets (UD normalised to 60 % Vf): T700S 2 860 MPa / 134 GPa / comp. 1 450; T800S 3 290 / 163 / 1 490; T1100G 3 460 / 185 / 1 870;
M40J 2 500 / 226 / 1 270. T1100G and M40J lamina E2, G12 and ply thickness: NOT FOUND. Transverse compressive strength: not in the report.

### Design-strain and knock-down references (P)
- 14 CFR 25.613 (A-/B-basis definitions): https://www.law.cornell.edu/cfr/text/14/25.613
- FAA AC 20-107B (barely visible impact damage must not reduce strength below ultimate; glass plies to isolate carbon from aluminium):
  https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC20-107B.pdf
- NASA CR-198347 (1996): "current design philosophy limits design ultimate strain to 4000 µin./in." https://ntrs.nasa.gov/api/citations/19960047125/downloads/19960047125.pdf
- NASA CR-159296 (1981): design ultimate strain ≈50 % of unflawed failure strain, representative 4 500 µε. https://ntrs.nasa.gov/api/citations/19810013888/downloads/19810013888.pdf
- Hot-wet ratios derived from the 2510 sheet (ETW ÷ RTA): 0° compression 0.83; 90° tension 0.58; in-plane shear strength 0.62; G12 0.74.
- CMH-17 numeric factors: NOT FOUND (paywalled).

### Adhesives (P)
- Loctite EA 9394 Aero: lap shear (ASTM D1002, aluminium) 28.9 MPa at 25 °C, 20.7 MPa at 82 °C, 22.7 MPa at −55 °C; T-peel ≈0.9 N/mm;
  bulk shear modulus 1.46 GPa dry. https://dm.henkel-dam.com/is/content/henkel/EA-9394-Aero
- 3M DP460: overlap shear 24.1 MPa (aluminium, 22 °C); T-peel ≈10.5 N/mm at 22 °C; data bondline 0.13–0.20 mm.

### Metals (S — ASM/MatWeb sheet copies, "typical, not for design")
- 7075-T6: 2.81 g/cm³, E 71.7 GPa, yield 503 MPa, ultimate 572 MPa, shear 331 MPa, fatigue 159 MPa at 5×10⁸ cycles (fully reversed).
  https://quickparts.com/wp-content/uploads/2024/05/Aluminum-7075.pdf
- Ti-6Al-4V annealed: 4.43 g/cm³, E 113.8 GPa, yield 880 MPa, ultimate 950 MPa, shear 550 MPa, fatigue 510 MPa at 10⁷ (unnotched), 240 MPa at Kt 3.3.
  https://www.aerospacemetals.com/wp-content/uploads/2023/07/Titanium-Ti-6Al-4V-Grade-5-Annealed.pdf
