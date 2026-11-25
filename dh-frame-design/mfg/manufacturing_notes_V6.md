# V6 manufacturing notes

What a composites shop needs alongside the STEP files, the ply book (`ply_book_V6.csv`), the zone table (`laminate_zones_V6.csv`),
the bill of materials (`BOM_V6.csv`) and the interface control (`interface_control_V6.md`).

Tags: **S** = from a supplier document (see `sources/`), **P** = my proposal, to be reviewed by the shop and a composites engineer.
Nothing here has been proven on a part.

## 1. What the STEP files are, and are not

- `FT-001` and `SA-001` are the **tool (outer) surfaces** as solids. The laminate builds inward from that surface; wall thickness
  comes from the ply book, not from the model. The analysis was run on the laminate mid-plane, half a local thickness inside this surface.
- The surfaces are unions of lofted tubes, cylinders and one box. Only three junction fillets exist in the model (top tube R8,
  rocker boss R3, shock seat R3); OpenCascade failed on the others. **Every junction needs a proper blended surface before tooling is
  cut** (P: R10–R15 on main junctions, R6 minimum elsewhere). Where spar segments change direction the model has small steps
  that the surfacing pass must remove. Blending adds material, so it must be re-checked against the clearances below 5 mm in `DESIGN_V6.md`.
- Machined parts (`RK`, `LK`, `SM`, `AX`, `BB`, `ID`) are functional solids: correct bores, widths and pin positions, no pocketing,
  chamfers, threads or bolt details.
- Not modelled at all: rear brake mount, cable and hose routing, bottle or accessory bosses, chain-guide lower roller, frame protection,
  seat clamp slot, drain holes.

## 2. Materials

| Material | Use | Tag |
|---|---|---|
| Toray T700G / 2510 unidirectional prepreg, 150 g/m², 0.152 mm cured | all UD plies | S (data sheet rev. 6.5.2025) |
| Toray T700S-12K / 2510 plain weave, 190 g/m², 0.218 mm cured | first and last ply of every zone (handling, drilling, impact) | S |
| Glass scrim or 100 g/m² glass fabric, one ply | between carbon and every aluminium insert | S for the principle (FAA AC 20-107B), P for the choice |
| Loctite EA 9394 paste adhesive | all bonded inserts | S for properties; joint design allowables are my estimate (25 % of the 82 °C lap-shear value) |
| 7075-T6, hard anodised | inserts, rocker, links, fittings | properties from typical data sheets, "not for design" |
| Ti-6Al-4V annealed | axles, pins, idler stub | same caveat |
| GGB DU bushes | all pivots | S for sizes and ratings |

The 2510 system is a 132 °C out-of-autoclave resin with a dry glass-transition temperature of 146 °C (131 °C wet) (S). The strength
values the analysis uses are Toray's vacuum-bag-oven numbers with a hot-wet knock-down; a bladder-moulded part is consolidated at higher
pressure, which normally helps, but that is an assumption until coupons cut from a real part say so.

## 3. Tooling concept (P)

- **Front triangle:** two-half aluminium female mould split on the centre plane (z = 0). Inflatable bladders through the down tube,
  top tube and seat mast, meeting at the head tube and at the BB/pivot core. BB-001, the pivot sleeve and the rocker sleeve are located on
  hardened pins in the mould so their positions come from the tool, not from the lay-up.
- **Swingarm:** two-half female mould split on a stepped surface (the part is not symmetric). One bladder per spar loop on each
  side; the yoke box is laid up over a soluble or foam core that stays in, or a bladder branch. Dropout inserts, pivot bush
  sleeves and link-pin bushes located on mould pins. The drive-side pivot lug and strut root are only 15 mm wide with 5 mm
  walls: treat them as **solid laminate** (no bladder), compacted by a silicone intensifier.
- Bladder pressure and tool temperature profile to be set by the shop; the Toray cycle below is the reference.

## 4. Lay-up rules

- Ply book ply 1 is on the bladder side; the last ply is against the tool. 0° runs along the member axis; in the head tube, BB,
  pivot bosses and yoke, 0° runs along the bore or cross-member axis.
- Every stack in the ply book is symmetric about its mid-plane. (P) Keep it balanced when plies are dropped.
- (S) Debulk under vacuum at least every 4 plies.
- (P) Ply drops between zones: stagger so that thickness changes no faster than 1 mm in 20 mm; never drop more than two plies at
  one station; cover every drop with a continuous ply. The analysis mesh already ramps thickness over about 16 mm at zone edges.
- (P) Butt joints in 0° plies staggered by at least 25 mm between plies; ±45° and 90° plies overlapped 10–15 mm.
- (P) At each junction carry at least half of the 0° plies of each tube around the corner onto the neighbouring tube for 60 mm.

## 5. Cure (S, Toray 2510 data sheet)

Hold full vacuum before heat-up (≥ 95 kPa if vacuum-bagged); ramp 0.6–2.8 °C/min to 132 ±5 °C; hold 120 min; cool to 54 °C at no more
than 2.8 °C/min before releasing pressure. For thick or complex lay-ups (head-tube junction 5.9 mm, head tube 7.4 mm, yoke 5.3 mm,
swingarm lugs) use the intermediate hold: 90 min at 88 °C. Prepreg out-life 28 days at 22 °C.

## 6. After cure

1. Trim tube ends and bores to the fixture; ream the two headset seats to Ø55.90–55.95 × 15 in one set-up; face the head tube.
2. Bond SM-001 into its pocket and torque its two M6 bolts; bond any insert that was not co-moulded.
   (P) Surface preparation: carbon abraded and solvent-wiped; aluminium anodised and primed; bond line 0.1–0.25 mm set with glass beads;
   cure the adhesive per its data sheet. Every bonded insert in this design is also trapped mechanically (wrapped, shouldered or bolted),
   so the bond is not the only load path.
3. Press DU bushes into their sleeves (S: housings H7, shafts f7, do not ream the bushes).
4. Assemble with the 1.0 mm thrust washers at the links and check the linkage turns freely through 200 mm of travel without the shock.

## 7. Inspection and first-article tests (P)

| Check | Method | Accept when |
|---|---|---|
| Hard points and alignment | coordinate measuring machine against `interface_control_V6.md` | inside the stated tolerances |
| Mass of each carbon part | scale | within ±8 % of the BOM laminate mass; lighter means missing plies, heavier means resin-rich or wrinkled |
| Wall thickness by zone | ultrasonic gauge or sectioned first article | within ±10 % of the zone table |
| Voids and wrinkles in thick zones | CT scan or section cuts at the head-tube junction, yoke and pivot lugs of the first article | no wrinkle deeper than one ply in a 0° stack; porosity under 2 % |
| Bond lines | tap test or ultrasonic on every insert | no disbond indication |
| Resin cure | DMA glass-transition temperature on a traveller coupon cured with each part | ≥ 140 °C dry |
| Laminate strength | short-beam shear and compression coupons from a traveller panel per batch | at or above the data-sheet values used in `src/laminate.py` |
| Clearances | assembled frame with the real fork, shock, wheel, cranks, chain and brake, cycled through full travel and steering lock | every clearance in `DESIGN_V6.md` confirmed, especially the ones marked estimated |
| Stiffness correlation | strain-gauged frame on a bench under the LC2 and LC3 load cases at limit load | measured strains within ±20 % of the model, otherwise the model is corrected before any further claim |

The structural test programme that must be passed before anyone rides the frame is in section 7 of `REPORT.md`.
