# TELANICO — Our original VorGun visual references (mandatory for asset batch)

## Authority
**These are our own curated production references**, not internet image-search results.
Read and actually VIEW the images before creating new Blender models. Source repository
`sgdenikin-sys/VorGun-Godot-Clean-Test` contains source 2D artwork; these exact paths were confirmed from the current
GitHub tree. Google Drive [VorGun / 03_BUILDINGS](https://drive.google.com/drive/folders/1yjbvqNQZDo0HVOK-MrCiWJVioSCTK-8_)
and [04_OBJECTS](https://drive.google.com/drive/folders/1uCP-mWP3ynK8a7VLaOTmAHoZJABJKTSl)
are the backup asset library. Use existing GitHub authorization; never expose tokens
or change permissions. Do not rely on dead sandbox links from old conversations.

**Primary approved 3D quality benchmark:** [Settlements Hall V3 Lite](../../artifacts/settlements_hall/v3-lite/README.md)
(render: [hero](../../artifacts/settlements_hall/v3-lite/hero.png), source GLB/BLEND).
V3 Lite is already integrated: DO NOT overwrite, rebuild or simplify the Hall
as part of the batch. Study its real 3D materials, muted ivory/teal/brass,
semi-transparent glass, geometry density and adult tabletop-diorama look.

## Buildings — eight verified original PNGs

| Target / purpose | Site ID | 2D reference | Role | Modeling guidance |
| --- | --- | --- | --- | --- |
| Operations | `operations` | `assets/buildings/building_operations_dome.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/buildings/building_operations_dome.png) | **DIRECT** | Preserve the dome/headquarters silhouette, windows and roof massing. Building not a generic barracks. |
| Contracts | `contracts` | `assets/buildings/building_contracts_office.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/buildings/building_contracts_office.png) | **DIRECT** | Architecture should read legal/archival. Retain major silhouette; omit micro-ornament. |
| FX Desk | `fx` | `assets/buildings/building_fx_tower.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/buildings/building_fx_tower.png) | **DIRECT** | Vertical landmark tower and recognisable roof; scale within the FX site. |
| VAT / Tax | `vat` | `assets/buildings/building_vat_office.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/buildings/building_vat_office.png) | **DIRECT** | Preserve compact symmetrical office character. |
| Compliance Annex | `compliance` | `assets/buildings/building_compliance_annex.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/buildings/building_compliance_annex.png) | **DIRECT** | Retain its stricter institutional character and basic massing. |
| Archive Rotunda | `archive` | `assets/buildings/glass_rotunda.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/buildings/glass_rotunda.png) | **PARTIAL** | Reference for rounded/transparent pavilion and glass design; not a complete canonical archive facade. |
| Industrial ancillary architecture | `operations / compliance / tube` | `assets/buildings/industrial_service_house.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/buildings/industrial_service_house.png) | **PARTIAL** | Only industrial service motifs, not a template for every office. |
| Settlements Hall (OLD 2D) | `settlements` | `assets/buildings/building_settlements_hall.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/buildings/building_settlements_hall.png) | **HISTORICAL** | Original 2D historical source; approved V3 Lite is the *real game reference*; do not remodel it. |

DIRECT = preserve recognizable original silhouette and architectural identity.
PARTIAL = use only as stylistic/shape inspiration. HISTORICAL = preserve, do not
replace the approved 3D V3 Lite asset.

**Important: four remaining office exteriors have no verified direct 2D building
PNG** in the curated `assets/buildings` folder: Trade Finance, LC Desk,
Coffee Area and Trader/Eagle. Do not pretend an unrelated 2D building is their
canonical exterior. Derive recognizable designs from the already established
palette, relevant story-scene artwork below, and established gameplay site roles.
Do not turn them into generic low-poly sheds.

## Trees, infrastructure and decoration — verified original artwork

| Subject | Site(s) | Source | Role |
| --- | --- | --- | --- |
| Pneumatic station | `tube_w, tube_e` | `assets/objects/pneumatic_tube_station.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/pneumatic_tube_station.png) | DIRECT |
| Pneumatic dispatch | `tube_w, tube_e` | `assets/objects/pneumatic_dispatch_column.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/pneumatic_dispatch_column.png) | DIRECT |
| Tube arches | `tube_w, tube_e` | `assets/objects/glass_pipe_arch.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/glass_pipe_arch.png) | DIRECT |
| Tube system | `tube_w, tube_e` | `assets/objects/pipeline_hub.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/pipeline_hub.png) | SUPPORT |
| Tube system | `tube_w, tube_e` | `assets/objects/pipeline_plant.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/pipeline_plant.png) | SUPPORT |
| Tube system | `tube_w, tube_e` | `assets/objects/pipeline_tee.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/pipeline_tee.png) | SUPPORT |
| Dock | `dock_w, dock_e` | `assets/objects/dock_large.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/dock_large.png) | DIRECT |
| Secondary dock | `dock_w, dock_e` | `assets/objects/dock_small.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/dock_small.png) | DIRECT |
| Launch vessel | `dock_w, dock_e` | `assets/objects/commuter_boat.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/commuter_boat.png) | DIRECT |
| Small launch | `dock_w, dock_e` | `assets/objects/courier_mini_launch.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/courier_mini_launch.png) | SUPPORT |
| Large leafy tree | `vegetation` | `assets/objects/tree_large.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/tree_large.png) | DIRECT |
| Small leafy tree | `vegetation` | `assets/objects/tree_small.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/tree_small.png) | DIRECT |
| Tree grouping | `vegetation` | `assets/objects/tree_cluster.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/tree_cluster.png) | DIRECT |
| Bench | `coffee / public space` | `assets/objects/bench.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/bench.png) | DIRECT |
| Lamp | `public space` | `assets/objects/lamp_post.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/lamp_post.png) | DIRECT |
| Signpost | `public space` | `assets/objects/signpost.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/objects/signpost.png) | DIRECT |

These PNGs set form language and proportions. Produce true standalone 3D
geometry, **not image planes/billboards**, from them. For nature make a few
lightweight reusable trees, shrubs and rocks; instance them with restrained
variations. Nature should be calmer and less geometrically crude than the
existing placeholder cones/ball shapes. Keep paths and entrance points clear.

## Department interior artwork (mood/details only, NOT exterior shape references)

| Department | Existing original art |
| --- | --- |
| Finance architecture / motifs | `assets/story_scenes/ornate_navy_finance_reception_desk.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/story_scenes/ornate_navy_finance_reception_desk.png) |
| Formal prestige / vault | `assets/story_scenes/opulent_compass_treasury_study.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/story_scenes/opulent_compass_treasury_study.png) |
| Contracts identity | `assets/story_scenes/grand_fantasy_contracts_hall.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/story_scenes/grand_fantasy_contracts_hall.png) |
| Compliance identity | `assets/story_scenes/grand_neo_classical_compliance_hall.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/story_scenes/grand_neo_classical_compliance_hall.png) |
| Archive identity | `assets/story_scenes/background_archive_hall.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/story_scenes/background_archive_hall.png) |
| Trader/Eagle identity only | `assets/mascots/FRONTAL/EXPRESSIONS/inquisitive_eagle_in_a_navy_suit.png` — [PNG](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/mascots/FRONTAL/EXPRESSIONS/inquisitive_eagle_in_a_navy_suit.png) |

These interiors are especially useful for colors, ornament restraint, signs,
door/material treatments, departmental differentiation and fantasy-industrial
motifs. They are **not** permission to change the canonical original office
interiors or recreate them as building exteriors.

## Overall world / composition

- Original approved 2D [island artwork](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/blob/main/assets/maps/VorGun_island_test_transparent.png)
  serves as a **mood and art-direction reference only**, not as coordinates
  or mesh source for terrain.
- Canonical site positions, 15 IDs, permitted footprints and entrances:
  `blender/scripts/world_v2_layout.py` **in this Lab repository**.
  Current game navigation and world-building source stay authoritative.
- Existing **in-game Settlements Hall V3 Lite** sets the final look.
- The prior prompt's *generic web image references are superseded* by the actual
  VorGun PNGs in this document. Do not web-search for imaginary replacement
  buildings.
- Preserve the dark navy/teal, ivory, aged bronze/brass visual DNA. Avoid
  plastic-cartoony, generic Kenney clones or real-world corporate exteriors.

## Batch execution (no added QA project)

Before a single batch build, inspect these existing references once and map
each target to DIRECT/PARTIAL/NEW DERIVATIVE.
Do not generate 2D concept redraws, do not re-audit archives, and do not search
Google Drive if the curated repo PNG is accessible.
**No separate test suite or walkthrough** just for reading artwork.
Reuse the existing single batch Blender generator, smoke check and current
release workflow from the parent task.

Failure to access a relevant direct reference is a blocker *for that asset only*;
do not silently substitute random imagery.
