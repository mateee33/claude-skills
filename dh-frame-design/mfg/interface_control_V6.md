# V6 interface control: datums, hard points, fits and tolerances

Frame coordinates: origin at the bottom-bracket centre, **x forward, y up, z to the rider's left** (drive side is −z), millimetres,
suspension fully extended. Every number is tagged:

- **S** — taken from a manufacturer's drawing or specification (reference in `sources/interfaces.md`).
- **D** — a dimension of this design (what the solid model and the analysis use).
- **P** — a tolerance or fit I propose. These are ordinary precision-machining and bonded-insert values chosen from the
  sensitivity check at the end of this file. They are not validated by a manufacturer and should be reviewed by whoever builds the tooling.

## 1. Datums

| Datum | Feature | Why |
|---|---|---|
| A | Axis of the bottom-bracket thread (BB-001) | every drivetrain and pivot position is measured from it |
| B | Mid-plane between the two BB shell faces | frame centre plane, z = 0 |
| C | Axis through the two headset bearing seats | fixes rotation about A; defines head angle, reach and stack |

Inserts are bonded on a fixture that holds A, the main-pivot bore and the rocker-pivot bore together; the head-tube seats are reamed
last in the same fixture.

## 2. Hard points (side view) and bores

| Feature | x | y | Size and fit | Tolerance on position | Tag |
|---|---|---|---|---|---|
| BB shell | 0 | 0 | width 83 ±0.5; thread 1.37 in × 24 TPI, right-hand on the non-drive side, left-hand on the drive side; thread length ≥ 16 each end; centre bore ≥ Ø33 | datum | S |
| BB shell faces | | | parallel within 0.1, square to A within 0.1 | | P (SRAM value not found) |
| Main pivot P | −25.0 | 120.0 | sleeve bore Ø20 H7 × 58 long (z = ±29); axle Ø20 f7 | ±0.2; parallel to A within 0.05 per 100 | D / P |
| Rocker pivot R | −49.7 | 278.0 | sleeve bore Ø19 H7 × 62 long (z = ±31) for 2 × GGB 1720DU; axle Ø17 f7 | ±0.15; parallel to A within 0.05 per 100 | D / S (bush fits) / P |
| Shock mount M (frame end) | 38.9 | 77.0 | M8 through 2 ears 30.0 +0.2/0 apart, for RockShox 8 × 30 hardware | ±0.2 | D / P |
| ISCG 05 tab holes | −24.2, 31.1, 13.3 | −27.4, −19.0, 34.0 | 3 × M6 on a 73 mm bolt circle; first hole 50° below the BB→axle line, then +100° each | ±0.1 on the bolt circle | S (pattern) |
| ISCG tab face | | | flush with the drive-side shell face, z = −41.5 | ±0.2 | P (offset not found in any standard) |
| Idler axis | 30.0 | 100.5 | M12 seat in ID-003; chain plane z = −56.5 | ±0.2 | D |
| Head tube, top face centre | 475.0 | 632.5 | | ±0.5 | D / P |
| Head tube, bottom face centre | 533.99 | 516.72 | length 129.9; head angle 63.0° | angle ±0.2° | D / P |
| Headset seats | | | ZS56 top and bottom: bore Ø55.90–55.95, 15 deep; head-tube outside Ø70.8 (S.H.I.S. recommends ≥ 62) | coaxial within 0.05; faces square within 0.05 | S (bore) / P |
| Seat post bore | along the mast | | Ø31.6, 107 insertion | | D |
| Rear axle A (on the swingarm) | −439.86 | 11.0 | 12 × 157: dropout inner faces at z = ±78.5; drive side to the SRAM UDH specification (bore Ø20 +0.1/0, thickness 12.5 ±0.2, axle M12 × 1.0) | axle axis parallel to the pivot bore within 0.2 over 157 | S / P |
| Rear brake mount | — | — | SRAM post mount, 2 × M6 × 1, 74.2 spacing, ≥ 12 full thread; for a 200 mm rotor the boss face plane is 73.22 from the axle axis | — | S (pattern); **position on the swingarm not designed** |

## 3. Link lengths that set the suspension curve

| Part | Dimension | Value | Tolerance | Tag |
|---|---|---|---|---|
| Swingarm SA-001 | pivot P to link lug S | 188.82 | ±0.2 | D / P |
| Swingarm SA-001 | pivot P to axle A | 428.94 | ±0.3 | D / P |
| Swingarm SA-001 | link lug S to axle A | 320.55 | ±0.3 | D / P |
| Push link LK-001 | eye to eye | 130.34 | ±0.05, the two links matched within 0.03 | D / P |
| Rocker RK-001 | R to shock eye K | 67.65 | ±0.05 | D / P |
| Rocker RK-001 | R to link pin L | 89.10 | ±0.05 | D / P |
| Rocker RK-001 | K to L | 125.40 | ±0.05, the two plates machined as a pair | D / P |
| Shock | eye to eye × stroke | 250 × 75 | | S |

Top-out positions of the moving points: S (−190.0, 211.8), L (−125.4, 325.0), K (0.0, 323.9). Over the full 200 mm of wheel travel the
swingarm turns 27.0° and the rocker 67.3° (calculated).

## 4. Lateral positions (z)

| Feature | z range | Tag |
|---|---|---|
| Frame pivot boss | −29 … +29 | D |
| Swingarm pivot eyes | drive side −46.5 … −31; non-drive side +31 … +62 | D |
| Main pivot axle AX-001 | −49 … +64.5 | D |
| Rocker mast boss / rocker plates / link-clevis cheeks | ±31 / 32–40 / 39–44.5 and 57.5–63 each side | D |
| Push links | 45.5–56.5 each side (1.0 side clearance to the clevis cheeks, for thrust washers) | D |
| Shock ears (frame and rocker) | 15–23 each side | D |
| Chain plane at chainring and idler | −56.5 (SRAM DH 83 mm chainline) | S |
| Idler carrier ID-003 | −49.5 … −41.5 | D |
| Dropout inner faces | ±78.5 | S |

## 5. Component limits that follow from the clearance study

| Item | Limit | Why |
|---|---|---|
| Chainring | 30 or 32 teeth | a 34-tooth ring would leave 0.9 mm between its teeth and the idler's (calculated from SRAM's ring radii) |
| Rear tyre | 27.5 × 2.5 (64 mm wide, 712 mm diameter as modelled) | 5–6 mm to the swingarm; no larger |
| Rear rotor | up to 220 mm | checked at 220 mm; rotor plane position is estimated |
| Fork | RockShox BoXXer 27.5, 200 mm, 44 mm offset, **Tall** upper crown | the crowns must sit 141.9 mm apart (Tall range 126.8–147) |
| Shock | RockShox Vivid 250 × 75, standard eyelets, 8 × 30 hardware at both ends, **damper body and reservoir at the rocker end, reservoir facing forward** | the reservoir does not fit at the frame end |
| Crank | SRAM X01 DH or XX DH on an 83 mm shell, 165 mm | the clearance model uses the X01 DH envelope |

## 6. How tight do the hard points need to be?

Moving one hard point by 0.2 mm and recomputing the linkage (calculated, `src/kinematics.py`):

| Point moved 0.2 mm | Wheel travel changes by up to | Leverage ratio at sag | Leverage ratio at full travel |
|---|---|---|---|
| Rocker pivot R | 0.84 mm | 0.48 % | 0.37 % |
| Rocker shock eye K | 0.35 mm | 0.23 % | 0.43 % |
| Rocker link pin L | 0.38 mm | 0.20 % | 0.15 % |
| Main pivot P | 0.14 mm | 0.05 % | 0.12 % |
| Link lug S | 0.07 mm | 0.07 % | 0.07 % |
| Rear axle A | 0.09 mm | 0.05 % | 0.04 % |

The rocker is the sensitive part, which is why its three bores carry the tightest tolerance and are machined in one set-up. Even so,
a 0.2 mm error anywhere moves the leverage ratio by less than 0.5 %, far inside the ±15 % uncertainty of the air-spring model.
Alignment (pivot axes parallel, wheel in the frame's centre plane) matters more to how the bike rides than these positions do.
