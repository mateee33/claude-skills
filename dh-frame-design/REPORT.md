# Custom carbon downhill frame for a 68 kg rider on Red Bull Rampage terrain — design study (V1 → V6)

**Status: a paper design with numerical analysis. Nothing here has been built or physically tested. It is not ready to ride.**
Any prototype and any riding trial depend on review by a qualified composite-structures engineer and on the bench tests in section 5.8 passing.

**The current revision is V6**, the first one modelled and checked as a 3-D assembly. It is documented in [`DESIGN_V6.md`](DESIGN_V6.md), with solid
models in `cad/V6/` and a manufacturing package in `mfg/`. Sections 0, 6 and 7 of this report carry the V6 numbers. **Sections 3 to 5 describe V5**, the last
revision of the idealised side-view model, and are kept as the record of that stage: V6 has the same geometry, hard points, suspension curve and load cases,
but different structure and hardware, and it corrects an error in the V1–V5 structural model that is explained in `DESIGN_V6.md`, section 3.

Every result carries one of five labels: **measured** (by someone, on hardware), **simulated** (numerical model run in this study),
**calculated** (closed-form from stated inputs), **estimated** (engineering judgement or third-party reconstruction), **unknown**.

## 0. The short answer

The final revision, V6, is a 27.5"-wheeled, 200/200 mm frame with a linkage-driven single pivot and an idler, built around a RockShox BoXXer Ultimate
fork and a Vivid Ultimate DH air shock. Against the three goals fixed before design:

| Goal | Result for V6 | Verdict |
|---|---|---|
| G1 rear-wheel force curve for 68 kg at 25 % sag | Meets three of four checks. Mid-stroke ratio 2.31 (target 2.3–2.8), bottom-out ratio 8.08 (≥ 6.5), pressure 69% of maximum (≤ 75 %). Misses the spring-energy check: 0.44 m against a 0.50 m target. | Better than the Supreme estimate on bottom-out resistance (8.1 vs 5.5). Against the Sender the differences are 3–6 %, inside the ±15 % model band: **inconclusive**. |
| G2 frame mass with all structural targets met | 4.77 kg (±12 %: 4.20–5.34 kg), every structural check passing | Sender CFR claims 4.61 kg: V6 is +3 % on paper, inside my ±12 % band: **no advantage shown**. Supreme DH V5 claims 5.3 kg: V6 is −10 %, but my upper bound (5.34 kg) reaches that figure, so by the rule fixed at the start: **inconclusive**. |
| G3 head-tube loading per kN of front-wheel force | Bending moment 307 N m; upper-bearing force 2.36 kN | **Advantage**: upper-bearing force 23 % lower than the Sender (3.07 kN) and 17–18 % lower than the Supreme (2.86–2.89 kN); moment 5 % lower. This is a geometry metric, not a strength comparison. |

Making the design real cost mass: V5, the idealised model, came out at 4.61 kg and V6 at 4.77 kg, and the one mass comparison that V5 appeared to win is no longer a win.

Where a production bike wins is in section 7.3. The largest one is not a number: both benchmarks exist, have been raced and lab-tested, and carry a warranty. This design has none of that.

## 1. Rider, fit and the choices left to me

Inputs, benchmark configurations and the fixed criteria are in [`01_rider_benchmarks_criteria.md`](01_rider_benchmarks_criteria.md), committed before any design result existed.

- Height 185 cm; riding weight 68 kg including helmet, protection, shoes and pack (confirmed). Inseam was not given (shoe size was), so standover is checked against an estimated 87 ± 3 cm.
- Tracks: Red Bull Rampage. No current bike and no stated improvement goal, so wheel format, travel and priorities were my calls (reasons in the criteria file).
- Suspension set-up uses 68 kg. Structural loads use an 80 kg rider and a 17 kg bike (section 5.1).

## 2. Benchmarks and comparison rules

| | Custom V5 | Canyon Sender CFR | Commencal Supreme DH V5 |
|---|---|---|---|
| Exact configuration | this study | Gen 3, MY2025–27, size M, +8 mm reach cup, BB high, 32.7 % chip | MY2023–26, size L, Low + Progressive, chainstay chip 0 |
| Wheels | 27.5 / 27.5 | 29 / 27.5 | 29 / 27.5 |
| Reach / stack (mm) | 475 / 632.5 | 476 / 630 | 484 / 649 |
| Head angle | 63.0° | 63.0° | 63.3° |
| Rear centre static (mm) | 440 | 438 | 454 |
| Wheelbase (mm) | 1281 | ≈1281 (calculated: 1273 + 8) | 1311 |
| Head tube (mm) | 130 | 105 | 112 |
| Travel front / rear (mm) | 200 / 200 | 200 / 200 | 200 / 220 |
| Geometry source | calculated | manufacturer chart; cup value from The Loam Wolf | manufacturer chart |

Charts, manuals and independent tests are linked in [`sources/canyon_sender_cfr.md`](sources/canyon_sender_cfr.md) and [`sources/commencal_supreme_dh_v5.md`](sources/commencal_supreme_dh_v5.md).
Neither maker publishes pivot coordinates or leverage curves. The Sender curve used here is **estimated** from its published progression and travel (a straight-line assumption);
the Supreme curve is an **estimated** third-party reconstruction from a photograph. No independent stiffness or timed-run data was found for either bike.

## 3. The design (V5; for V6 see `DESIGN_V6.md`)

### 3.1 Components and why

| Item | Choice | Checked against manufacturer documentation |
|---|---|---|
| Fork | RockShox BoXXer Ultimate D2, 27.5", 200 mm, DebonAir+, 44 mm offset, Tall upper crown | Axle-to-crown 586 mm; offsets 44/48 mm; crown spacing for the Tall crown 126.8–147 mm, this frame needs 142.9 mm (head tube 129.9 + headset stacks 13, the stacks estimated); chart pressure for 63–72 kg is 110–130 psi (7.6–9.0 bar) against a 260–300 psi maximum; tyre limit Ø732 mm vs ≈712 mm fitted |
| Shock | RockShox Vivid Ultimate DH D1 (air), 250 × 75 mm, standard eyelets, 30 × 8 mm hardware | Size offered; maximum 330 psi with 0–2 tokens; adjustable hydraulic bottom-out in the last 20 % of travel; predicted 229 psi (15.8 bar) at 25 % sag = 69 % of maximum |
| Why these | The BoXXer over the Fox 40 because Fox states that fitting a 40 to a non-approved frame voids its warranty, and RockShox documents the crown limits needed to design the head tube. The Vivid over the Float X2 for its adjustable hydraulic bottom-out. Öhlins makes no air shock in a DH length. | [`sources/fork_and_shock.md`](sources/fork_and_shock.md) |
| Tyres | 27.5 × 2.5 DH casing front and rear, radius taken as 356 mm (estimated, ±4 mm) | within fork and frame limits |
| Drivetrain | 83 mm threaded BB, 32-tooth chainring, 14-tooth idler, 157 × 12 mm rear hub | a 34-tooth ring will not clear the idler position (calculated) |

Materials other than carbon, and why:

- **Pivot axles and idler stub: Ti-6Al-4V.** High strength at low mass, and no galvanic couple with carbon.
- **Rocker and push links: 7075-T6 aluminium**, machined. Stocky parts in compression where carbon offers little; anodised and never in direct contact with carbon.
- **Bonded inserts (BB sleeve, headset seats, dropouts, bushes): 7075-T6 with a glass-fibre isolation ply**, as FAA AC 20-107B recommends for carbon/aluminium interfaces; every insert is also mechanically trapped by the laminate.
- **Pivot bearings: steel-backed PTFE plain bearings (GGB DU type)** instead of ball bearings. The main pivot sees 15.5 kN per side at limit load in the sideways landing; a 6004 ball bearing's static rating is 5 kN (Table C). The price is more breakaway friction.
- **Shock pins: hardened alloy steel**, 12.7 mm. A titanium or aluminium pin fails the bending check.
- **Protection: moulded rubber/TPU down-tube and spar guards**, plus bump-stop blocks at the head tube (section 3.4).
- **Laminate: Toray T700G/2510 unidirectional tape with T700S/2510 plain-weave face plies.** Chosen because its properties are public and include hot-wet, open-hole and compression-after-impact values, so every allowable in this study can be traced. An unlimited budget would buy a tougher resin or T1100-class fibre, but I found no public lamina data set for those to analyse with.

### 3.2 Geometry (calculated)

Conditions: fork and shock fully extended, rider off, level ground, 27.5 × 2.5 tyres at 356 mm radius, fork axle-to-crown 586 mm, offset 44 mm, lower headset stack 4 mm.
Sag column: rear 25 % (50 mm), fork 35 mm.

| Measure | V5 |
|---|---|
| Reach / stack | 475 / 632.5 mm (±5 mm reach headset cups) |
| Head angle / trail | 63.0° / 132 mm |
| Head tube length | 129.9 mm |
| Wheelbase | 1280.9 mm |
| Front-centre (BB to front axle, horizontal) | 841.1 mm |
| Rear-centre (horizontal) | 439.9 mm static; 449.9 mm at sag; 444.2 mm at bottom-out |
| Chainstay (axle to BB, straight line) | 440.0 mm |
| BB height / BB drop below both axles | 345 mm / 11 mm |
| Standover | 759 mm above the BB; 855 mm at mid top tube (estimated inseam 870 ± 30 mm) |
| Seat tube | 408 mm; 78.4° effective; seat-post insertion limited to about 110 mm by the rocker axle |
| Travel | 200 mm front, 200.0 mm rear (vertical) |
| Adjustment positions | none besides reach cups; no flip chips |

### 3.3 Suspension layout and hard points

Linkage-driven single pivot. The one-piece carbon swingarm turns on a main pivot 120 mm above the BB. A pair of push links drives a rocker on the seat mast,
and the rocker compresses a near-vertical shock anchored on the down tube beside the BB. A 14-tooth idler on the front triangle puts the chain line through the main pivot.

Why this suits the tracks and the shock:

- A one-piece triangulated swingarm on a wide pivot has no pivots near the axle to rack sideways in a crooked landing.
- A main pivot study (calculated) showed that a pivot at chainring height needs no idler but moves the axle 19.5 mm forward at bottom-out, which puts the tyre into the seat mast at a 440 mm rear centre.
  At 120 mm the axle is 4 mm rearward at bottom-out and the tyre clears. The idler is the price: without it this pivot height gives about 18° of pedal kickback.
- Rear-centre growth to sag is 10 mm, against about 17.5 mm reported for the Sender, whose reviews criticise pop and manuals. Whether that difference is felt is untested.
- Shock loads enter the frame at its two stiffest places: the BB/down-tube junction and the seat mast, which carries the rocker reaction in tension.

Coordinate system: origin at the BB centre; +x forward, +y up (bike standing unloaded on level ground), +z to the rider's left; millimetres.
Full table with sag and bottom-out positions: [`cad/hard_points_V5.csv`](cad/hard_points_V5.csv). Side view: [`cad/side_view_V5.dxf`](cad/side_view_V5.dxf) and the figure below.

| Point | x | y | z | What it is |
|---|---|---|---|---|
| BB | 0.0 | 0.0 | 0 | bottom-bracket centre |
| P | −25.0 | 120.0 | ±38 | main pivot (bushes in the swingarm arms) |
| R | −49.7 | 278.0 | ±36 | rocker pivot on the seat mast |
| M | 38.9 | 77.0 | 0 | shock eye on the front triangle |
| K | 0.0 | 323.9 | 0 | shock eye on the rocker (top-out) |
| L | −125.4 | 325.0 | ±50 | push-link eye on the rocker (top-out) |
| S | −190.0 | 211.8 | ±50 | push-link eye on the swingarm (top-out) |
| A | −439.9 | 11.0 | ±78.5 | rear axle (top-out); −449.9, 61.0 at sag; −444.2, 211.0 at bottom-out |
| Idler | −54.0 | 92.0 | −56.5 | 14-tooth idler centre |
| Head tube top / bottom | 475.0, 632.5 / 534.0, 516.7 | | 0 | steering axis ends |
| Front axle | 841.1 | 11.0 | 0 | fork at top-out |
| Ground | — | −345.0 | — | under both tyres |

Push link 130.3 mm eye to eye; rocker arms 89.1 mm (link) and 67.7 mm (shock); shock 250.0 mm at top-out.

![V5 side view](results/figures/side_view_V5.png)

### 3.4 Clearances through full travel (calculated, side view plus lateral positions)

| Check | Value | Criterion | Result |
|---|---|---|---|
| Rear tyre to seat-mast rear face, minimum | 11.5 mm | ≥ 6 mm | pass |
| Rear tyre to seat-tube top, minimum | 52.5 mm | ≥ 6 mm | pass |
| Shock air can (Ø58) to seat-mast front face | 4.3 mm | ≥ 3 mm (Fox's rule; RockShox states none) | pass, but below my own 5 mm aim; got worse in V2 |
| Shock air can to main-pivot sleeve | 3.4 mm | ≥ 3 mm | marginal pass |
| Shock eye to top-tube underside | 10.8 mm | ≥ 5 mm | pass |
| Push links, rocker arms and swingarm spars beside the tyre | need \|z\| ≥ 46 mm | tyre half-width 32 mm + 14 mm | designed at ±50 mm; **not verified in 3-D CAD** |
| Rocker and links passing the seat mast and top-tube junction | arms at \|z\| ≥ 44 mm, tube half-width 30 mm | — | **not verified in 3-D CAD** |
| Tyre top at bottom-out | 567 mm above the BB | saddle underside must stay above 582 mm | rider set-up limit |
| Shock reservoir | must point to the non-drive side | — | **unknown**: no drawing of the D1 reservoir is published |
| Fork tyre-to-crown at full compression | fork-internal | tyre Ø712 mm vs Ø732 mm limit | pass |
| Fork stanchion to frame at steering lock | contact at about 74° without stops; stop blocks sized for ±40° lock sit 49 mm from the centre plane, 30 mm behind the steering axis | — | **estimated**: stanchion spacing (160 mm) and crown offset (28 mm) are assumed, not documented by RockShox |

## 4. How the suspension behaves

![V5 suspension curves](results/figures/suspension_curves_V5.png)

Full table: [`results/V5/kinematics.csv`](results/V5/kinematics.csv). Leverage ratio is rear-wheel vertical travel per unit of shock travel.

| Wheel travel | Shock stroke | Leverage ratio | Axle rearward | Spring force at wheel, slow | Spring force at wheel, fast | Anti-rise | Anti-squat (32/17) |
|---|---|---|---|---|---|---|---|
| 0 mm | 0.0 mm | 3.48 | 0.0 mm | 0 N | — | 141 % | 120 % |
| 25 mm | 7.4 mm | 3.27 | 5.8 mm | 262 N | 233 N | 137 % | 123 % |
| 50 mm | 15.3 mm | 3.07 | 10.0 mm | 469 N | 504 N | 134 % | 126 % |
| 75 mm | 23.7 mm | 2.88 | 12.7 mm | 667 N | 754 N | 130 % | 129 % |
| 100 mm | 32.7 mm | 2.69 | 14.0 mm | 882 N | 1028 N | 127 % | 131 % |
| 120 mm | 40.3 mm | 2.55 | 13.9 mm | 1082 N | 1287 N | 124 % | 133 % |
| 150 mm | 52.6 mm | 2.35 | 12.1 mm | 1459 N | 1799 N | 120 % | 135 % |
| 175 mm | 63.6 mm | 2.22 | 9.0 mm | 1878 N | 2402 N | 117 % | 137 % |
| 190 mm | 70.4 mm | 2.17 | 6.4 mm | 2290 N | 2977 N | 114 % | 138 % |
| 200 mm | 75.0 mm | 2.17 | 4.3 mm | 3787 N | 4609 N | 113 % | 138 % |

- Leverage (simulated from the hard points): 3.48 at top-out, 3.07 at sag, 2.17 at bottom-out; 37.7 % progression; average 2.67.
- Axle path (simulated): 10.0 mm rearward at sag, 14.1 mm maximum near 55 % travel, 4.3 mm rearward at bottom-out.
- Spring force (estimated): the air-spring curve is a two-chamber gas model with estimated dimensions, scaled to one frame-specific pressure chart
  (Commencal's Vivid Air chart for the Supreme V5.2: 80 kg, 264 psi) and cross-checked against RockShox's rule of thumb, which it matches within 13 %.
  RockShox publishes no curve. Treat every force past sag as ±15 %.
- Anti-rise 134 % at sag, anti-squat 126 % at sag, upper chain growth 0.4 mm over full travel, pedal kickback at most 0.55° (all calculated).
  Assumptions: 32-tooth ring, 17-tooth cog, 14-tooth idler at (−54, 92); rider centre of mass 30 mm ahead of and 780 mm above the BB; whole-bike mass 17 kg;
  combined centre of mass 946 mm above the ground at sag; fork at 35 mm of travel; rear wheel locked to the swingarm for chain growth.
  Both scale inversely with centre-of-mass height: 100 mm higher lowers anti-rise by about 13 points, 100 mm lower raises it by about 16.

What you should feel:

- **Near sag** the bike rides at about 2.0 Hz at the rear (wheel rate 7.9 N/mm on a 48 kg sprung share), with a high leverage ratio that helps an air shock start moving. This is a firm freeride set-up, not a plush race one.
- **In the middle of the stroke** the wheel force at 60 % travel is 2.3 times the force at sag. That is the support that keeps the bike from sinking on a take-off lip or a G-out. V1 gave 2.06 and the benchmark estimates give 2.0–2.2.
- **Near bottom-out** force climbs from about 4.6 times the sag load at 94 % travel to 8.1 times at full travel (9.8 times in a fast hit), before the hydraulic bottom-out adds damping. You will use full travel only on the largest landings.

Starting set-up, using the manufacturers' procedures:

1. **Shock sag: 25 % of wheel travel, range 22–28 %.** That is 50 mm (44–56 mm) at the axle, or 15.3 mm (13.4–17.3 mm) of shock stroke, measured standing centred in riding kit. It sits inside RockShox's 30 % ± 5 % guidance for DebonAir shocks.
2. **Shock pressure:** follow RockShox's method. Start from pressure in psi equal to your kitted weight in pounds (150 psi, 10.3 bar), add air in 50 psi steps, cycling the shock to equalise the chambers each time, then adjust to the sag above.
   My model predicts about 229 psi (15.8 bar); trust the measured sag, not the prediction. Do not exceed 330 psi with 0–2 tokens or 300 psi with 3–4.
3. **Tokens: start with 2.** Hydraulic bottom-out: start at the middle of its 5 settings and add until the hardest landing you ride uses about 95 % of travel.
4. **Fork:** RockShox's chart gives 110–130 psi (7.6–9.0 bar) for 63–72 kg and no sag procedure. Start at 130 psi with 2 tokens (0 fitted as delivered, 6 maximum) and raise pressure before adding tokens.
5. **Damping:** RockShox publishes no click settings for a custom frame. Start every adjuster at mid-range and set rebound so the bike does not kick after a drop to flat from about 0.5 m. Red Bull's Rampage notes say riders run everything stiffer than World Cup downhill and tyres at 35–45 psi (2.4–3.1 bar).

Competitor comparison for this section: Sender anti-rise 124–130 %, anti-squat about 125 %, chain growth 0.1 mm (manufacturer or repeated from the manufacturer); Supreme anti-rise about 93 %,
anti-squat 83–94 %, axle path 14 mm rearward maximum (third-party estimate). Their leverage curves, pivot coordinates and shock tunes are **unknown**.

## 5. Structural assessment

### 5.1 Where the loads come from

Design mass: rider 80 kg (68 kg × 1.18, to cover body-mass change, extra protection and a second rider) plus a 17 kg bike, 97 kg in all. The frame placard would read "maximum rider weight 80 kg in riding kit".

No published test standard gives loads for this use, and no Rampage telemetry was found, so the landing loads come from a model checked against the one relevant measurement:

1. **Measured anchor.** Phillips, Kilgas and Jensen (2015) measured ground forces for riders dropping 0.29, 0.48 and 0.67 m to flat ground on a 130 mm bike: 5.4, 6.8 and 7.9 kN in total. A single 39.9 N/mm spring reproduces all three within 1 % (calculated).
2. **Landing model (simulated).** Rider mass on a leg spring and damper, sprung bike mass, the estimated air spring through the simulated leverage curve, a damper with hydraulic bottom-out, unsprung mass and a tyre that bottoms on the rim.
   At 0.67 m it predicts 7.8 kN for this bike against 8.4 kN from the measured law scaled to 97 kg, which is 7 % lower and plausible for a bike with more travel. Its parameters are estimated and it is not validated above 0.67 m.
3. **Design landing.** An equivalent flat-drop height of 2.0 m: the height that gives the same speed into the ground as the real landing gives normal to its slope. A 19 m vertical drop reaches that when the landing is about 16° flatter than the flight path; a well-matched landing is nearer 0.8 m.
4. **Limit loads** = simulated peak at 2.0 m × 1.25 for model uncertainty: **9.2 kN at the rear tyre, 8.0 kN at the front**. These equal what the model gives at about 3.0 m without the factor.
5. **Ultimate loads** = 1.5 × limit. Material design values then carry their own reductions (section 5.4).
6. **Side loads** are limited to 1.5 kN per tyre. Two bounds agree on that order: a 27.5" wheel folds sideways at roughly that load (estimated from typical lateral stiffness), and the rider cannot react more than about 0.5 kN m of roll or yaw through the pedals (calculated).
   My first run used 3.0 and 2.5 kN; that implied a frame twist no rider could hold, and I corrected it before sizing anything. No measured side-load data was found, so this is the least certain load in the study.
7. **Braking** is limited by the brake, not the tyre: 1.5 kN at the front contact patch and 0.5 kN at the rear (estimated), applied during a 3 kN front compression.

![Landing model and limit loads](results/figures/loads_landing.png)

### 5.2 Load cases

Each case fixes the hand load and all but one vertical tyre force; the last is solved so that the bike is in balance about the BB and the rider's feet supply a pure force there.

| Case | Covers | Load enters at | Carried by | Derived from | Pass criterion |
|---|---|---|---|---|---|
| LC1 | hard braking | front and rear contact patches, hands | fork → head-tube bearings; swingarm → pivot, links, rocker, shock; reaction at BB | brake-limited force during a 3 kN compression | composite index ≤ 1.0 at ultimate; joints margin ≥ 0 |
| LC2a/b/c | bottom-out landings, rider centred, back, forward | both tyres, suspension at full travel | as above; shock and rocker loads peak here | landing model at 2.0 m × 1.25 | as above, plus buckling factor ≥ 2 on ultimate |
| LC2d | front wheel cases a knuckle | front tyre, 8 kN at 45° rearward | head-tube bearings (the largest bearing loads of any case) | front limit load redirected | as above |
| LC3 | sideways landing | 1.5 kN side load at each tyre with 60 % of the landing loads | head tube in lateral bending and torsion; swingarm in lateral bending; BB reacts roll and yaw | wheel-collapse and rider-reaction bounds | as above |
| LC4 | cornering compression | 3 g in the bike's plane, side load 0.35 of normal | as LC3 at lower load | estimated | as above; also the reference for fatigue |
| LC5 | repeated rough-track impacts | LC2a scaled: 200 000 cycles at 40 %, 20 000 at 60 %, 2 000 at 80 %, 200 at 100 % of limit (estimated spectrum) | whole frame | — | laminate strain at limit load below a 3 000 microstrain no-growth threshold; metal stresses below endurance values |

**Table A. Load cases: limit forces at the tyres and resulting interface forces (V5)**
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


### 5.3 Standards, and what they do not cover

| Standard | Covers this use? | Use made of it |
|---|---|---|
| ISO 4210-2/-6:2023 | No. Its scope excludes bicycles "for use in severe applications such as sanctioned competition events, stunting, or aerobatic manoeuvres", and it has a single mountain-bike class. | Its frame tests (falling mass 22.5 kg from 360 mm; falling frame; pedalling 1 200 N × 100 000; horizontal +1 200/−600 N × 50 000; vertical 1 200 N × 50 000) are the minimum a prototype should pass. |
| ASTM F2043 Condition 5 | It classifies the use ("extreme jumping; downhill above 40 km/h") but gives no loads; no Condition 5 frame specification was found. | Classification only. |
| EFBE Tri-Test Category 5 | Closest match (downhill, freeride, drops over 1.2 m). Fatigue, maximum-load and overload stages. Load levels are not published. | The lab test to commission; Commencal cites it for the V5.2, Canyon cites its own Category 5 testing. |
| Manufacturer categories | Canyon's Category 5 text sets no drop limit; both makers exclude damage from jumps from warranty. | Shows that no production warranty covers this use either. |

### 5.4 Laminate, properties and allowables

Fibre directions are measured from each tube's axis; stacks are symmetric, listed from the inner (bladder) face to the mid-plane; F = plain-weave fabric at ±45°, numbers = unidirectional plies.

| Zone | Plies | Thickness | Half-stack |
|---|---|---|---|
| Down tube | 20 | 3.17 mm | F / 0 / 0 / +45 / −45 / 0 / 0 / +45 / −45 / 90 |
| Top tube | 16 | 2.56 mm | F / 0 / 0 / +45 / −45 / 0 / 0 / 90 |
| Seat mast | 20 | 3.17 mm | F / 0 / 0 / +45 / −45 / 0 / 90 / +45 / −45 / 0 |
| Head tube | 32 | 5.00 mm | F / (0 / 90 / +45 / −45) × 3 / 0 / 90 / 0 |
| Head-tube junction (within 140 mm of the steering axis) | 38 | 5.91 mm | F / 0 / 0 / +45 / −45 / 0 / 90 / +45 / −45 / 0 / 0 / +45 / −45 / 0 / 90 / +45 / −45 / 0 / 0 |
| Seat-mast and top-tube junction | 22 | 3.48 mm | F / (0 / 90 / +45 / −45) × 2 / 0 / 90 |
| Bosses and BB core (around BB, pivot, rocker, shock mount) | 30 | 4.69 mm | F / (0 / 90 / +45 / −45) × 3 / 0 / 90 |
| Swingarm spars | 20 | 3.17 mm | F / 0 / 0 / +45 / −45 / 0 / 0 / +45 / −45 / 90 |
| Swingarm knee build-up | 28 | 4.39 mm | F / (0 / 0 / +45 / −45) × 3 / 90 |
| Swingarm nodes (pivot, link eye, dropout) | 22 | 3.48 mm | as the mast/top-tube junction |
| Swingarm yoke web | 18 | 2.87 mm | F / (+45 / −45 / 0 / 90) × 2 |

Lamina properties, room temperature, from the Toray 2510 datasheet (lot averages, not statistical allowables):

| | T700G/2510 tape | T700S/2510 plain weave |
|---|---|---|
| Modulus along / across fibres | 118.5 GPa (mean of 125 tension and 112 compression) / 8.41 GPa | 55.9 / 55.9 GPa |
| Shear modulus, Poisson ratio | 4.23 GPa, 0.31 | 4.21 GPa, 0.04 |
| Strength: tension / compression / shear | 2 172 / 1 448 / 154 MPa | 912 / 709 / 133 MPa |
| Ply thickness, density | 0.152 mm, 1.517 g/cm³ | 0.218 mm, 1.502 g/cm³ |

Design strain limits applied at ultimate load (**estimated**; they stand in for allowables that only coupon testing can supply):

| Mode | Limit | Basis |
|---|---|---|
| Fibre compression | 4 500 microstrain | NASA damage-tolerant design practice (about half the unflawed strain); between the datasheet's hot-wet open-hole value (≈5 400) and its compression-after-impact value (≈3 000) |
| Fibre tension | 6 000 microstrain | notched-tension practice; unflawed failure is 17 400 |
| In-plane shear | 9 000 microstrain | about the linear limit of the hot-wet shear curve |
| Transverse tension (matrix cracking) | 3 400 microstrain at limit load | 0.85 × hot-wet transverse strength ÷ modulus; no matrix cracking in normal use |

### 5.5 Models

- **Front triangle and swingarm (simulated):** laminated triangular shell elements (pyfe3d) on a surface made from the side-view tube axes, with blended junctions.
  Bearing seats and inserts are rigid rings. The front triangle is held at the BB; the swingarm at the main pivot with the push-link force applied.
  Models, loads and results: `src/frame_fe.py`, `src/swingarm_fe.py`, `src/cases.py`, `results/V5/`. The analysed surfaces are in `cad/*.stl`.
- **Solver checks (simulated against theory):** a cantilever tube deflects within 0.6 % of beam theory at 4–6 mm elements, isotropic and laminated; an axially compressed cylinder buckles within 3 % of the classical load.
- **Do the loads balance?** The support reaction from each finite-element run equals the reaction computed independently from whole-bike statics to better than 10⁻⁶ N. In the swingarm the pivot's reaction moment about its own axis is zero, as it must be.
- **Does the mesh matter?** Yes at single elements, no for the conclusion. Raw single-element peaks beside the lower headset seat wander by ±25 % with mesh size, so the pass criterion uses a 10–12 mm patch average.
  Front triangle, 8 350 → 20 422 nodes: the governing index moves 0.78 → 0.85 → 0.84. Swingarm, 7 267 → 16 987 nodes: 0.66 → 0.72 → 0.77, still rising, with 23 % margin left at the finest mesh.

![Mesh refinement](results/figures/mesh_convergence.png)

### 5.6 Results

**Table B. Composite strain check at ultimate load, by load case (simulated)**
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


![Front triangle strain index, V2 against V5](results/figures/front_triangle_strain_index.png)

![Swingarm strain index, V3 against V5](results/figures/swingarm_strain_index.png)

- **Head tube:** governing index 0.84 in LC2d, bearing loads 21.3 kN (upper) and 23.8 kN (lower) at limit. Single-element values up to about 1.4 remain in the ring of elements next to the lower headset seat.
  The model cannot say whether those are real: they depend on insert shape, fillet radius and ply drops that it does not contain. This is the first place for a detailed solid sub-model and a strain-gauged test.
- **Shock mount, BB core, main pivot:** boss zone 0.74–0.84 in the landing cases; shock force 19.9 kN, rocker-pivot force 35.9 kN at limit.
- **Dropouts and swingarm:** 0.38 in the worst landing, 0.72 in the sideways landing at the knee where the lower spar turns inward. Lateral stiffness at the axle 621 N/mm (simulated).
- **Buckling (simulated, linear):** lowest load factor on ultimate load is 4.6 (LC2d), 7.5 (LC3), 18.9 and 23.5 in the landing cases. With a 0.5 knock-down for shape imperfections that leaves at least 2.3. Walls of 2.6–3.2 mm are not buckling-critical.
- **Fatigue (LC5):** the highest fibre strain at limit load is 0.84 ÷ 1.5 × 4 500 = 2 500 microstrain, below the 3 000 microstrain threshold. Metal parts: shock pin 570 MPa at limit, pivot axle 260 MPa, both below their endurance values for the 200-cycle top block (calculated; pin strength unverified).

**Table C. Joints, pins, bearings and bonded inserts at ultimate load (calculated, V5)**
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


Which failure modes this model can and cannot judge:

| Mode | Evaluated? |
|---|---|
| Fibre tension and compression, in-plane shear, matrix cracking, ply by ply | Yes, simulated, against estimated strain limits |
| Wall and panel buckling | Yes, linear eigenvalue with a knock-down; no post-buckling |
| Pin, bolt, bush and seat bearing; insert bond average shear | Yes, calculated |
| Damage between plies (delamination) at radii, ply drops, lug run-outs and free edges | **No.** A shell model carries no through-thickness stress. Needs solid sub-models and element tests. |
| Impact damage from rocks or crashes | Only through the conservative compression strain limit; not simulated |
| Bond peel, bondline fatigue, moisture ageing | **No.** Average shear only; every insert is therefore also mechanically trapped |
| Moulding defects: wrinkles, voids, resin-rich corners | **No.** Process-dependent; needs cut-ups and CT of first articles |
| Fatigue life of the laminate | Not as a life prediction; a strain threshold only |
| Headset bearing capacity under 24 kN | **Unknown**; not a frame part, but likely to indent |

### 5.7 What the first structural run taught me

Two corrections came from the first front-triangle run and are part of the record: the side loads above, and the supports. Holding the BB rigid against unbalanced loads made the frame carry pitching moments a rider's feet cannot supply.
Balancing each case about the BB removed that, and the BB-core overstress it had produced disappeared. The head-tube junction overstress did not, and drove V3.

### 5.8 Prototype tests this design needs before anyone rides it

1. **Coupons** in the actual prepreg and cure: tension, compression, shear, open-hole, compression after impact, interlaminar shear and tension, at room temperature and hot-wet, to replace every estimated limit in 5.4.
2. **Elements:** head-tube junction with headset seats; shock-mount lug; main-pivot and rocker bosses; dropout; bonded-insert pull-out and push-out; swingarm knee.
3. **Full frame, static:** LC2c, LC2d and LC3 to limit load with no permanent set, then to ultimate with no failure, strain-gauged at the hot spots to check the model.
4. **Full frame, fatigue:** the ISO 4210-6 tests as a floor, the EFBE Category 5 Tri-Test at the lab, and the LC5 block spectrum in vertical and lateral loading.
5. **Impact:** ISO falling-mass and falling-frame tests as a floor, then drop-tower landings with an instrumented dummy at 1.0, 1.5 and 2.0 m equivalent height.
6. **Damage tolerance:** a visible-threshold impact on the down tube and head-tube junction, then limit load.
7. **First-article inspection:** CT or ultrasonic scan and a sectioned frame.
8. **Instrumented riding**, only after 1–7 pass: wheel-force and shock data on real landings to test the loads in 5.1, especially the side load.

## 6. Revision history

Each revision answers the worst finding of the analysis before it.

| Step | Finding that triggered it | Likely cause | Change | Before → after | Penalty | Kept? |
|---|---|---|---|---|---|---|
| V1 | — | — | Baseline: leverage 3.08 → 2.30, base laminate | mid-stroke ratio 2.06 (fails G1a), spring drop height 0.39 m (fails G1c) | — | baseline |
| V1 → V2 | Suspension analysis: too little mid-stroke support at 25 % sag | Air springs sag in the middle; a flat leverage curve needs low pressure to reach the sag | Moved the push-link eye, rocker pivot and shock eyes to steepen leverage to 3.48 → 2.17 | mid ratio 2.06 → 2.31; pressure 202 → 229 psi; bottom-out ratio 7.06 → 8.08; drop height 0.393 → 0.439 m; shock force at limit 21.2 → 19.9 kN; rocker pivot 43.6 → 35.9 kN | shock-to-mast clearance 7.7 → 4.3 mm, shock-to-pivot 7.2 → 3.4 mm | yes |
| (tried) | — | — | A leverage curve with most of its progression before 60 % travel | this four-bar could not produce it inside the packaging; best was 3.6 → 2.03 with mid ratio 2.38 | exceeds my 3.5 start and 2.15 end guides | no |
| loads | First front-triangle run | Side loads set too high; supports reacting moments a rider cannot | Side load 3.0/2.5 → 1.5 kN; every case balanced about the BB; hot-spot value changed from a single element to a patch average | V2 laminate, sideways landing: single-element peak 6.8 → 3.8, patch-averaged value 1.9; BB-core index in the forward landing 1.7 → 0.8 | — | yes (correction) |
| V2 → V3 | Front triangle fails the sideways landing (1.86) and the knuckle impact (1.61) at the head-tube junction | 3.2 mm junction walls bending under the lateral bearing couple | Junction laminate 3.17 → 5.91 mm over 140 mm, head tube 3.78 → 5.00 mm, down tube and seat mast 2.26 → 3.17 mm, top tube 1.96 → 2.56 mm | worst index 1.86 → 0.84; head-tube side deflection in LC3 7.6 → 5.0 mm | front-triangle laminate 1.56 → 2.10 kg | yes |
| (tried) | same | same | Widening the top and down tubes at the head tube (60 → 76 mm, 70 → 84 mm) | no gain: 2.08 against 1.89 alone; 0.86 against 0.84 with the laminate | +0.07 kg | no |
| V3 → V4 | Swingarm fails the sideways landing (1.07–1.14) | Lower spar too narrow where it turns inward ahead of the tyre | Lower spar 22 → 30 mm wide, upright 22 → 26 mm, spar laminate 2.56 → 3.17 mm, 4.39 mm knee build-up, thicker yoke web | index 1.07 → 0.72; lateral stiffness at the axle 346 → 621 N/mm | swingarm laminate 0.64 → 0.84 kg | yes |
| V4 → V5 | Joint check: shock-mount inserts at 24.9 MPa bond shear against a 5.2 MPa allowance | The bond was the only load path for 30 kN | Flanged bushes bearing on lug walls built up to 8 mm; the bond only retains them | worst joint margin −79 % → +17 % (now the shock pin in bending) | +0.02 kg | yes |
| stop | — | — | A mass-trimming pass could remove perhaps 0.15–0.25 kg from low-stressed zones | smaller than the ±12 % mass band | — | not pursued: any gain would be inconclusive |
| V5 → V6, packaging | First 3-D assembly with manufacturers' component envelopes: ten clashes or impossibilities (shock and reservoir, rocker, fork crown, rotor, cassette, chain, crank arms, idler mount) | V1–V5 were checked in side view only, with placeholder envelopes | Solid model of every part; shock turned round; bolted aluminium shock fitting; rocker plates outside the seat mast; spars rerouted around rotor, cassette, chain and cranks; idler on a carrier on ISCG tabs | clashes 10 → 0; tightest clearance 2.9 mm | swingarm members narrower than the ones analysed; 30–32-tooth ring only; Tall fork crown only | yes |
| model | Re-checking the narrowed swingarm | The shell model sat on the modelled surface, half the wall outside it; a tool surface has the wall inside | Analysis mesh moved to the laminate mid-plane; accurate distance function for flat tubes | V6 as first packaged: swingarm 0.75 → 1.24, lateral stiffness 408 → 208 N/mm, head-tube zone 0.75 → 1.03 | V1–V5 results describe parts half a wall larger than drawn | yes (correction) |
| V6, structure | Swingarm 1.24 and head tube 1.03 on the corrected model | Sections smaller than the analysis had assumed | Asymmetric swingarm (31 mm non-drive pivot eye, 15.5 mm drive side), wider spars, longer yoke, 3.5–5.6 mm laminate; head tube 70.8 mm outside diameter with a 7.4 mm wall; sideways landing run from both sides | swingarm 1.24 → 0.69; front triangle 0.82 (up to 0.93 across mesh sizes); lateral stiffness 407 N/mm | frame mass 4.61 → 4.77 kg | yes |

**Table E. Revision log**
| Rev | Leverage start → end | Pressure at 25 % sag | Mid-stroke ratio | End ratio | Spring drop height | Shock force at limit | Front triangle worst index | Swingarm worst index | Worst joint margin | Frame mass | All structural checks |
|---|---|---|---|---|---|---|---|---|---|---|---|
| V1 | 3.08 → 2.30 | 202 psi / 13.9 bar (61% of max) | 2.06 | 7.06 | 0.393 m | 21.2 kN | 1.86 (LC3, ht_junction) | 1.29 (LC3) | -80% | 3.75 kg | FAIL |
| V2 | 3.48 → 2.17 | 229 psi / 15.8 bar (69% of max) | 2.31 | 8.08 | 0.439 m | 19.9 kN | 1.86 (LC3, ht_junction) | 1.07 (LC3) | -79% | 3.78 kg | FAIL |
| V3 | 3.48 → 2.17 | 229 psi / 15.8 bar (69% of max) | 2.31 | 8.08 | 0.439 m | 19.9 kN | 0.84 (LC2d, boss) | 1.07 (LC3) | -79% | 4.37 kg | FAIL |
| V4 | 3.48 → 2.17 | 229 psi / 15.8 bar (69% of max) | 2.31 | 8.08 | 0.439 m | 19.9 kN | 0.84 (LC2d, boss) | 0.72 (LC3) | -79% | 4.59 kg | FAIL |
| V5 | 3.48 → 2.17 | 229 psi / 15.8 bar (69% of max) | 2.31 | 8.08 | 0.439 m | 19.9 kN | 0.84 (LC2d, boss) | 0.72 (LC3) | +17% | 4.61 kg | pass |
| V6 | 3.48 → 2.17 | 229 psi / 15.8 bar (69% of max) | 2.31 | 8.08 | 0.439 m | 19.9 kN | 0.82 (LC2d, ht_junction) | 0.69 (LC3) | +17% | 4.77 kg | pass |


![Revision history](results/figures/revision_history.png)

## 7. Scorecard

### 7.1 Scored goals

**Table F. Goal G1 with the same shock model and rule (25 % sag, 68 kg)**
| Bike | Leverage curve used | Tokens | Pressure | a. Force at 60 % ÷ W (2.3–2.8) | b. Force at 100 % ÷ W (≥ 6.5) | c. Spring drop height (≥ 0.50 m) | d. Pressure ÷ max (≤ 75 %) |
|---|---|---|---|---|---|---|---|
| Custom V5 and V6 (same linkage) | simulated from the hard points, 3.48 → 2.17 | 2 | 229 psi | 2.31 | 8.08 | 0.439 | 69% |
| Sender CFR, 32.7 % chip | estimated, 3.23 → 2.17 | 0 | 214 psi | 2.11 | 7.44 | 0.400 | 65% |
| Sender CFR, 37 % chip | estimated, 3.33 → 2.10 | 0 | 222 psi | 2.17 | 7.88 | 0.414 | 67% |
| Supreme DH V5 | estimated, 3.45 → 2.60 | 0 | 231 psi | 2.02 | 5.52 | 0.403 | 70% |


![Goal G1](results/figures/g1_force_curves.png)

| Metric | Custom V6 | Sender CFR | Supreme DH V5 | Method / source | Margin and verdict |
|---|---|---|---|---|---|
| G1a mid-stroke ratio | 2.31 | 2.11 (2.17 with 37 % chip) | 2.02 | same estimated shock model; custom curve simulated, others estimated | +6 to +9 % vs Sender, +14 % vs Supreme: inside ±15 %, **inconclusive** |
| G1b bottom-out ratio | 8.08 | 7.44 (7.88) | 5.52 | as above | +3 to +9 % vs Sender: **inconclusive**. +46 % vs Supreme: **advantage, if the third-party curve is right** |
| G1c spring drop height | 0.44 m | 0.40 (0.41) m | 0.40 m | as above | target 0.50 m missed by all; +6 to +10 %: **inconclusive** |
| G1d pressure ÷ maximum | 69 % | 65 % (67 %) | 70 % | as above | all pass; no meaningful difference |
| G2 frame mass | 4.77 kg ±12 % | 4.614 kg claimed, size M | 5.3 kg claimed | custom calculated from the bill of materials; others manufacturer; shock inclusion unstated for both | vs Sender +3 %: **no advantage**. vs Supreme −10 %: upper bound 5.34 kg is not below 5.3 kg: **inconclusive** |
| G3 moment at lower head-tube bearing per kN | 307 N m | 323 N m | 320–323 N m | calculated from geometry and fork length | −5 %: small **advantage** |
| G3 upper head-tube bearing force per kN | 2.36 kN | 3.07 kN | 2.86–2.89 kN | as above | −23 % and −17 to −18 %: **advantage** |

On G1c: the energy a spring stores over the full stroke does not depend on the leverage curve's shape, only on the pressure the sag setting demands.
At 25 % sag the 75 % pressure cap limits it to about 0.47 m with this shock, so the 0.50 m target and the pressure rule conflict. I did not move the target. Running 22 % sag or 80 % of maximum pressure would reach it.

### 7.2 Reported, not scored

| Metric | Custom V6 | Sender CFR | Supreme DH V5 | Source |
|---|---|---|---|---|
| Rear-centre growth to sag | 10 mm | ≈17.5 mm | unknown at sag | simulated; independent outlets repeating Canyon |
| Maximum rearward axle travel | 14 mm | ≈24 mm | ≈14 mm | simulated; repeated; third-party estimate |
| Anti-rise at sag | 134 % | 124–130 % | ≈93 % | calculated; manufacturer and repeated; third-party estimate |
| Anti-squat at sag | 117 % (32/17) | ≈125 % | 83–94 % (34/14–18) | calculated; repeated; third-party estimate |
| Chain growth / kickback | −5.2 mm / −4.6° | 0.1 mm / 0.5° | about −5° at full travel | calculated; repeated; third-party estimate |
| Rear travel | 200 mm | 200 mm | 220 mm | manufacturer |
| Head tube length | 130 mm | 105 mm | 112 mm | manufacturer |
| Frame stiffness | swingarm 407 N/mm lateral at the axle (simulated) | unknown | unknown | no published data found |
| Structural margins at Rampage-class loads | positive in this model | unknown | unknown | makers publish none |
| Lab certification | none | Canyon Category 5 (in-house) | none found for V5; EFBE Cat 5 for V5.2 | manufacturer |

### 7.3 Where this design shows an advantage, and where the production bikes win

**Advantage (within what a paper study can show)**
- Head-tube bearing loads for a given front-wheel hit are 17–23 % lower, because the fork is 19 mm shorter and the head tube 18–25 mm longer. This follows from published geometry and is the firmest result here.
- Bottom-out resistance at 25 % sag is clearly higher than the Supreme estimate, with the caveat that the Supreme curve is a third-party reconstruction whose chip position is not stated.
- The spring and structure are sized for you: pressure sits at 69 % of the shock's limit with room to go stiffer, and the structure is checked against an explicit load set for big landings, which no production maker publishes.

**Inconclusive**
- Mid-stroke support and spring energy against the Sender: differences of 3–9 % inside a ±15 % model band.
- Frame mass: 4.77 kg ±12 % against the Sender's 4.61 kg and the Supreme's 5.3 kg. My band covers both figures, so no claim either way.
- Less rear-centre growth than the Sender (10 mm against 17.5 mm) may help pop and manuals, which Sender reviews criticise. That is a hypothesis, not a result.

**The production bikes win**
- **They are real.** Both have been raced; the Sender is Category 5 tested by Canyon and the V5.2 is EFBE Category 5 certified. They come with a warranty and crash replacement. This frame is unbuilt and untested, and several of its inputs are estimates.
- **Front wheel.** Both use a 29" front wheel, which rolls over holes better and is more stable at speed. My 27.5" front follows Rampage practice and trades that away.
- **Supreme:** 20 mm more rear travel, about 30 mm more wheelbase, and lower anti-rise (≈93 % against 134 %), so its rear suspension stays more active under braking on rough ground.
- **Sender:** ±8 mm reach, BB-height and progression adjustments, the same claimed mass, a kinematic tune developed with race teams, and ball-bearing pivots with less friction than my plain bearings.
- **Open design items that are mine alone (V6):** no rear brake mount, cable routing or lower chain guide designed yet; a drive-side pivot lug only 15.5 mm wide that a shell model cannot judge; clearances of 4–6 mm that partly rest on estimated envelopes (fork crowns, 2027 shock reservoir, cassette, rotor); a seat post limited to about 107 mm insertion; and a drivetrain restricted to a 30–32-tooth ring with a small idler on a cantilevered carrier.

### 7.4 Questions only physical testing can answer

1. Real laminate allowables and joint strengths for the chosen prepreg and moulding process.
2. Whether the head-tube junction and lower headset seat survive ultimate load: the model's single-element peaks there are unresolved.
3. Delamination at radii and ply drops, impact damage tolerance, bond durability.
4. The actual Vivid air-spring curve (dyno) and the frame's measured leverage curve, which together decide G1.
5. Real landing and side loads on Rampage-type features.
6. Frame and swingarm stiffness, and how it feels.
7. Fork crown, shock reservoir and rocker clearances on hardware.
8. Actual frame mass.
9. Whether any of this is faster or better to ride.

### 7.5 If the real goal is faster or better runs: a timed comparison

Only after an independent engineering review and after the bench tests in 5.8 have passed.

- **Bikes:** the prototype, a Sender CFR size M (+8 cup) and a Supreme DH V5 size L, each with the same wheels and tyres where the frames allow (the benchmarks need a 29" front; use the same tyre model, compound, casing and pressure), the same brakes, bar, stem length, bar height and pedals.
- **Set-up:** the same procedure on each bike: sag at the same percentage, rebound by the same drop test, pressures recorded. One shakedown day per bike before timing.
- **Track:** one track with a rough section, a steep braking section and at least two repeatable jumps or drops; not a first descent of anything. Conditions logged; stop if they change.
- **Runs:** at least 6 timed runs per bike in an alternating order that reverses halfway (A-B-C, C-B-A, …), with equal rest. Discard runs with a crash or a stop, and say how many.
- **Data:** timing gates for the full run and each section; wheel-travel sensors for travel used and bottom-outs; landing position on the jump; the rider's ratings written before seeing times.
- **Analysis:** compare medians; treat a difference smaller than the run-to-run spread on the same bike as no difference. One rider on one track answers the question for that rider and track only.
- **Rampage-type features** are not a place to compare bikes by stopwatch. Compare measured travel use, bottom-out count and landing stability on drops built up in height in steps.

## 8. Files

| Path | Contents |
|---|---|
| `01_rider_benchmarks_criteria.md` | rider inputs, benchmark configurations, fixed goals |
| `sources/` | manufacturer charts, manuals, standards, measured data and material data, each with its URL and source type |
| `DESIGN_V6.md` | the current revision: what the 3-D check changed, parts, clearances, structure, open items |
| `cad/V6/` | STEP solids of every V6 part and of the assembly at top-out, sag and bottom-out |
| `mfg/` | V6 ply book, laminate zones, bill of materials, interface control, manufacturing notes |
| `cad/hard_points_V5.csv`, `cad/side_view_V5.dxf` (and `_V6`) | coordinate table (top-out, sag, bottom-out) and layered side view |
| `cad/*_surface_V5.stl`, `cad/*_analysis_midplane_V6.stl` | the surfaces that were analysed (not production surfaces) |
| `results/summary.json` | every number in the tables above, for all six revisions |
| `results/V1…V6/` | kinematics table, suspension results, finite-element results per revision; clearances and checks for V6 |
| `results/convergence.json`, `results/landing_simulation.json` | mesh, verification and landing-model records |
| `src/` | all code; `python3 src/run_all.py && python3 src/make_figures.py && python3 src/make_report.py` reproduces the results |

Software: Python 3.13 with numpy, scipy, matplotlib, pyfe3d 0.12 (shell elements), scikit-image and gpytoolbox (surface meshing), ezdxf.
V1–V5 had no CAD kernel behind them: their geometry is the coordinate table, the DXF and the code. V6 adds solid models built with build123d 0.13 (OpenCascade).
No commercial solver or solid-element laminate analysis was available.

## 9. Limits of this study

- The structural geometry is an idealisation built from tube axes. Real frame surfaces, insert shapes and ply drops will change local strains.
- V1–V5 were analysed with the shell on the modelled surface; V6 on the laminate mid-plane. Indices of V6 and of earlier revisions are therefore not on the same footing (`DESIGN_V6.md`, section 3).
- Thin-shell elements are a poor model of nearly solid parts such as the V6 drive-side pivot lug, and of load introduction at bosses.
- Material limits, the air-spring curve, the landing model's parameters, side loads, brake limits and half of the mass budget are estimates, each labelled where used.
- Competitor kinematics are estimates or unknown. No claim against either bike rests on measured data from that bike beyond its published geometry and mass.
- Nothing here replaces testing, and nothing here makes the frame safe to ride.
