# Interface standards and component envelopes — source record (V6)

Collected 2026-11-25. **R** = read directly in the manufacturer's PDF, drawing or image; **F** = read through a page-extraction
tool; **S** = search snippet only (unverified). "NOT FOUND" = not in any document that could be opened. All dimensions in mm.

## Documents
| Key | Document | URL |
|---|---|---|
| A | SRAM "Eagle Transmission and DH Transmission Frame Fit Specifications", GEN.0000000008642 Rev F | https://www.sram.com/globalassets/document-hierarchy/frame-fit-specifications/mtb/eagle-transmission-and-dh-transmission-frame-fit-specifications.pdf |
| B | SRAM "2024 MTB Components Frame Fit Specifications", GEN.0000000007996 Rev C | https://www.sram.com/globalassets/document-hierarchy/frame-fit-specifications/mtb/2024-mtb-frame-fit-specifications.pdf |
| C | SRAM UDH and Full Mount rear derailleur frame specification, drawing 90-7518-190-000 Rev H | https://www.universalderailleurhanger.com/downloads/UDH_And_Full_Mount_Rear_Derailleur_Rev_H.zip |
| D | SRAM DUB MTB BB Compatibility Chart, Rev K | https://www.sram.com/globalassets/document-hierarchy/compatibility-map/mtb/dub-mtb-bottom-bracket-compatibility-chart.pdf |
| F1 | e*thirteen ISCG tab measurement drawing | https://support.ethirteen.com/hc/article_attachments/202032649 |
| G1 | Cane Creek S.H.I.S. poster, Rev 1 | https://www.bicycleretailer.com/sites/default/files/content/news/CaneCreek%20SHIS%20Poster%20Small.pdf |
| G2 | Cane Creek Forty product page | https://www.canecreek.com/products/40 |
| G3 | Works Components reach-adjust ZS56/ZS56 | https://workscomponents.com/products/reach-adjust-zs56-zs56-to-suit-1-1-8-steerer-6mm |
| H1 | RockShox "Will the MY24 Vivid Air fit my frame?" (fit drawing) | https://support.rockshox.com/hc/en-us/articles/18039359674395-Will-the-MY24-Vivid-Air-fit-my-frame |
| H4 | RockShox Front Suspension Specifications 2027 | https://www.sram.com/globalassets/document-hierarchy/service-manuals/rockshox/front-suspension/2027-front-suspension-specifications.pdf |
| H5 | 2026 RockShox Spare Parts Catalog | https://www.sram.com/globalassets/document-hierarchy/spare-parts/spare-parts-catalog/2026-rockshox-spare-part-catalog.pdf |
| T | Toray 2510 Prepreg System data sheet, Rev 6.5.2025 | https://www.toraycma.com/wp-content/uploads/2510-Prepreg-System.pdf |
| J | GGB DU/DUB Designer's Handbook (2009, distributor mirror) | https://prema.com.pl/wp-content/uploads/2022/06/ozyska_slizgowe_DUB__Warstwa_slizgowa_tasma_brazowaspiek_brazowyPTFEPb.pdf |

## Cranks (83 mm threaded shell, 56.5 mm chainline)
Distance W from the frame centre plane to the crank arm's inside face, at radius X from the BB axis (non-drive side) — R, documents A p.23 and B p.39/64:

| X | 25 | 35 | 65 | 85 | 105 | 130 | 190 |
|---|---|---|---|---|---|---|---|
| XX DH (Q-factor 183) | 69.8 | 71.5 | 75.8 | 78.0 | 79.0 | 79.0 | 79.0 |
| X01 DH DUB (Q-factor 183) | 64.7 | 67.3 | 74.3 | 76.8 | 77.8 | 78.3 | 78.3 |
| Descendant DH DUB (Q-factor 187) | 65.8 | 67.2 | 76.1 | 79.7 | 80.9 | 81 | 81 |

- Boot-equipped cranks: subtract 1.5 from W (A p.25, R). **The model uses the X01 DH row minus 1.5.**
- Drive side, XX DH: chainring tooth centre 56.5; inboard face of ring 54.7–55.2; chainring outer radius 30T 64.3, 32T 68.3, 34T 72.3; arm inside face at the pedal end 79.0 (A p.22, R).
- Crank lengths 150–165 (XX DH), 165/170 (X01 DH).
- DH Transmission: total chain growth must not exceed 90 mm (A p.4, R).

## Bottom bracket (SRAM DUB BSA 83) — R, A p.30 and D
Shell width 83 ±0.5 symmetric about the centre plane; thread 1.37 in × 24 TPI, right-hand on the non-drive side, left-hand on the drive side;
thread length 16 minimum from each face; centre bore Ø33 minimum. Spacers for a DH crank: 2.5 inner left, 2.5 inner right, 4.5 outer right.
Face parallelism tolerance: NOT FOUND.

## ISCG 05 — R (F1) unless noted
Three M6 bosses on a 73 mm bolt circle (chord 55.92 between adjacent holes). Seen from the drive side, with the reference line from the BB centre
to the rear axle at full extension: the lower-rear hole is 50° below that line, the next two follow at +100° each.
Tab thickness and tab-face offset from the BB shell face: NOT FOUND as standard values (guide makers assume tabs flush with the shell face and use about 2 mm of spacers on 83 mm shells).

## Headset (S.H.I.S. ZS56 upper and lower) — R (G1, G2)
Head-tube bore 55.90–55.95, ream depth 15, recommended head-tube outside diameter 62. Cane Creek Forty stack: 8 top (short cover), 4 bottom.
Reach-adjust cups for ZS56/ZS56 with a straight 1 1/8 in steerer: Works Components ±3 and ±6 (F; cup insertion 11.5, upper stack with cover 9.5); Syncros and Airdrop ±5 (S).

## Rear brake post mount (SRAM, B p.130) — R
Bolt spacing 74.2; 2 × M6 × 1, 12 minimum full thread. For a 200 mm rotor: boss face plane 73.22 from the axle axis, nearer hole offset 16.8 along that plane.
Hole-pattern centre plane 9.2 from the dropout face (quoted for 12 × 157 Super Boost; no separate DH-157 row). 220 mm rotor: 81.88 and 21.8.
Rotor mounting-face offset from the dropout: NOT FOUND (rotor plane taken as 62.5 from the centre plane, **estimated**).

## Rear axle, hub and derailleur mount (C, B) — R
UDH specification applies to 142, 148 and 157 mm hubs. Axle M12 × 1.0, shaft Ø11.96; drive-side dropout bore Ø20 +0.1/0, dropout thickness 12.5 ±0.2,
inner contact face Ø28 minimum, 60° minimum clear rotation behind the hanger. SRAM publishes a STEP clearance model (90-7518-190-070 Rev H) that must be checked in the tooling CAD.
HG driver on 157 mm: 44.1 from the dropout to the body shoulder, body width 34.9. Smallest-cog pitch diameter 41.1.
Cassette XS-797 / XG-795: 10-12-14-16-18-21-24. Cassette width, largest-cog diameter and cog positions: NOT FOUND
(model uses **estimated** cog planes from 70 mm (10T) to 47 mm (24T) from the centre plane).

## RockShox BoXXer (Gen D crowns) — R (H4, H5) unless noted
Axle-to-crown 586 (27.5 in, 200 mm). Offsets 44/48. Crown spacing: Tall 126.8–147, Short 106.8–127. Top of upper tube to top of lower crown 120–132.6.
Lower crown assemblies are coded "6OS", "10OS", "14OS" for the 44, 48 and 52 mm offsets, read here as the stanchion plane sitting 6, 10 and 14 mm ahead of the steerer axis (**inference from part codes**, a forum snippet agrees).
**Stanchion centre spacing, lower-crown thickness and crown outline: NOT FOUND.** Frame bumpers: kit of two fitted on the upper tubes; no dimensional steering-stop guidance is published.

## RockShox Vivid Air (C1, 2024+) fit drawing — R (H1)
Shock axis to the outer edge of the reservoir 63; reservoir runs from 11.39 beyond the body-eyelet axis to 98.21 toward the air can; air can Ø58; lower sleeve Ø48.25;
lower eyelet centre to sleeve shoulder 19.25. The reservoir sits at the damper-body end. Reservoir diameter and eyelet width: NOT FOUND.
**No fit drawing exists for the D1 (2027+) shock, which has a new reservoir. The model uses the C1 envelope and that must be re-checked on hardware.**

## Toray 2510 cure — R (T)
Oven, vacuum bag: full vacuum (≥ 95 kPa) held before cure; ramp 0.6–2.8 °C/min to 132 ±5 °C; hold 120 min; cool to 54 °C at ≤ 2.8 °C/min.
Thick or complex lay-ups: intermediate hold 90 min at 88 °C. Debulk every 4 plies. Tg (resin, DMA) 146 °C dry, 131 °C wet. Out life 28 days at 22 °C.

## GGB DU plain bushes — R (J)
| Shaft | Housing | Lengths available | Fits |
|---|---|---|---|
| 12 | 14 | 8, 10, 12, 15, 20, 25 | shaft f7, housing H7 |
| 17 | 19 | 20 only | shaft f7, housing H7 |
| 20 | 23 | 10, 15, 20, 25, 30 | shaft f7, housing H7 |
Bushes are pre-finished and must not be reamed. Load ratings (250 N/mm² static, 140 N/mm² dynamic) are in `standards_loads_materials.md`.
