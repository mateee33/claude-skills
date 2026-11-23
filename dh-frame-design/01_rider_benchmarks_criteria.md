# 1. Rider, benchmarks and fixed comparison criteria

Written and committed **before** any design result existed. These rules do not change across revisions.

Result labels used everywhere: **measured** (by someone, on hardware), **simulated** (numerical model run here),
**calculated** (closed-form from stated inputs), **estimated** (engineering judgement or third-party reconstruction),
**unknown** (no usable data).

## 1.1 Rider inputs

| Item | Value | Status |
|---|---|---|
| Height | 185 cm | given |
| Inseam | not given (shoe size EU 44 was given instead) | **estimated 87 ± 3 cm** from 0.47 × height; only standover depends on it |
| Riding weight | 68 kg including helmet, protection, shoes and pack | given, confirmed |
| Usual tracks | Red Bull Rampage (big-mountain freeride: drops of 10–20 m class onto steep built landings, gaps, steep chutes, hardpack) | given |
| What the bike should do better | not stated ("unlimited budget") | left to me |
| Current bike | not stated | no reference fit to copy or correct |

Choices made because they were left open, with the trade-off:

- **Wheels: 27.5" front and rear.** Red Bull's Rampage bike page says riders' wheels "tend to run smaller" (27.5", 26" or mixed),
  and Commencal's own Rampage riders use the 27.5" FRS, not the Supreme. A 27.5" front wheel is stronger and stiffer for the same rim,
  turns and spins with less inertia, and its shorter fork (586 mm vs 605 mm axle-to-crown) plus longer head tube lowers head-tube loads.
  Cost: less roll-over and less high-speed stability than the 29" front wheel both benchmark bikes use. A 29" front option is not designed here.
- **Travel: 200 mm front, 200 mm rear** with a 250 × 75 mm shock (average leverage 2.67). More rear travel (the Supreme has 220 mm)
  would add energy capacity but raise leverage and shock pressure; I preferred lower shock loads and a lower seat-tyre conflict.
- **Suspension priority:** bottom-out resistance and mid-stroke support for a 68 kg rider on a stiff freeride setup (25 % sag),
  ahead of small-bump sensitivity; predictable rear-centre length on take-offs ahead of square-edge roll-over.
- **Reach target 475 mm.** Canyon places 185 cm in both M (468 mm) and L (495 mm); Commencal places it in L (484–488 mm).
  I took the short end of that span because the terrain rewards control in the air over straight-line stability.
  With no current-bike feedback this is the least certain fit choice, so the frame keeps ±5 mm reach headset cups.

## 1.2 Benchmark bikes (exact configuration used for every comparison)

| | Canyon Sender CFR | Commencal Supreme DH V5 |
|---|---|---|
| Generation / years | Gen 3 (platform M180), model years 2025–2027 | V5, model years 2023–2026 (superseded by V5.2 in mid-2026; same static geometry) |
| Frame material | carbon front and rear | aluminium 6066 |
| Wheel configuration | 29" front / 27.5" rear (only option) | 29" front / 27.5" rear (only option in S–XL) |
| Size matched to 185 cm and 475 mm reach | **M with +8 mm reach cup → reach 476 mm** (cup value from The Loam Wolf; Canyon's chart gives 468 mm neutral) | **L, Low position → reach 484 mm** |
| Adjustment settings | BB high (63.0°, 352 mm), progression chip 32.7 % (as shipped); 37 % also reported | Low + Progressive (stock chips), chainstay chip at 0 (454 mm) |
| Stack / head angle | 630 mm / 63.0° | 649 mm / 63.3° |
| Rear centre (static) / wheelbase | 438 mm / ≈1281 mm (1273 + 8, calculated) | 454 mm / 1311 mm |
| Head tube / fork length / offset | 105 mm / 605 mm (BoXXer 29) / 52 mm | 112 mm / 612 mm (Commencal chart) / 52 mm |
| Rear travel / shock | 200 mm / 250 × 75 | 220 mm / 250 × 75 |
| Frame mass (claimed) | 4 614 g, size M, shock inclusion not stated | 5.3 kg, size and shock inclusion not stated |

Sources and the full charts are in `sources/canyon_sender_cfr.md` and `sources/commencal_supreme_dh_v5.md`.
Neither manufacturer publishes pivot coordinates or leverage curves. Where I use third-party reconstructions they are labelled **estimated**.

## 1.3 The three goals

### G1 — Rear-wheel force curve matched to a 68 kg rider on Rampage-type landings (primary)
Why it matters: stock DH bikes are sprung and valved around an 80–85 kg rider at 30 % sag. A 68 kg rider running a stiff freeride setup
needs the spring to hold the bike up in the middle of the stroke and resist bottom-out without leaving the shock outside its pressure range.

Rule: the same shock model (RockShox Vivid Ultimate DH air, 250 × 75) and the same air-spring model are applied to every bike.
Pressure is set for **25 % sag** under the same rear sprung load W (68 kg rider, same mass distribution assumptions). Tokens 0–4 may be used
within the documented pressure limit. Scored on:

| Check | Target (fixed) |
|---|---|
| a. Mid-stroke support: wheel force at 60 % travel ÷ W | 2.3 – 2.8 |
| b. Bottom-out resistance: wheel force at full travel ÷ W (slow compression) | ≥ 6.5 |
| c. Spring energy from top-out to bottom-out ÷ W ("spring drop height") | ≥ 0.50 m |
| d. Shock pressure at that setting | ≤ 75 % of the documented maximum for the token count |

Uncertainty: the air-spring model is estimated (no manufacturer curve exists), so forces past sag carry about ±15 %; competitor leverage curves
are estimated (±0.1 in leverage ratio). A difference smaller than these bands is reported as **inconclusive**.

### G2 — Frame mass at equivalent fit and travel, with every structural target met
Why it matters: mass the rider has to rotate and place in the air, but only if strength is not traded away.

Rule: frame mass = front triangle + swingarm + links + pivot axles, bearings, bolts, idler, bonded inserts and frame protection;
excluding shock, rear axle, headset, seat clamp. My figure is **calculated** from laminate areas and hardware, with a ±12 % band.
An advantage is claimed only if my mass plus 12 % is below the benchmark's published figure **and** every load case in section 5 passes.
Because neither manufacturer states whether its figure includes a shock, both readings are reported.

### G3 — Head-tube loading per unit of front-wheel landing force
Why it matters: at Rampage 2025 a frame's head tube broke off on landing a large drop. For the same front-wheel force,
a shorter fork and a longer head tube reduce the bending moment and the bearing forces the frame must carry.

Rule: for a 1 kN force at the front axle, normal to the ground, compute (a) the bending moment about the lower head-tube bearing and
(b) the radial force on the upper head-tube bearing, from head angle, fork axle-to-crown length, offset and head-tube length only.
Computed identically for all three bikes from manufacturer geometry and fork documentation (**calculated**).
This is a load-path metric, not a strength comparison: the benchmarks' laminates and section sizes are unknown.

## 1.4 Reported but not scored
Axle path and rear-centre growth, anti-rise, anti-squat, chain growth, fit numbers, stiffness. Competitor values are quoted with their
source type; where no credible source exists the cell says **unknown**.

## 1.5 Structural rule that applies to all goals
No goal is counted as met by a revision that fails any structural pass criterion in section 5. Structural loads use a design rider mass
that is higher than 68 kg (see section 5); suspension setup uses 68 kg.
