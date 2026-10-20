# Telanico V2.1 — oblique miniature world

Built from `codex/telanico-overworld-v2` / `f3949d6` for TASK2_19OCT.

The camera angle is measured **above horizontal**. Default/Explore/Reset use
40°, with a north-up orthographic overview. Inspect allows 30–60°. Follow now
frames the adult-scale temporary courier at a 30-unit view height, rather than
following an invisible dot at world overview scale. Existing pan, pinch, scroll,
selection and safe-area behavior are retained.

## Visual decisions and evidence

The comparable WebGL angle series uses the same yaw, target, 124-unit view,
lighting and world geometry within each series. The before series is V2 terrain
with camera-only test controls; the after series includes the rebuilt world.
All screenshots are exported Godot WebGL, except the explicitly named Blender
reference. No generated concept images are used as evidence.

| View | Evidence |
| --- | --- |
| V2, 60° above horizontal | [Before](v2-1/before-web-60.png) |
| V2 camera-only comparison | [30°](v2-1/before-web-30.png) · [38°](v2-1/before-web-38.png) · [45°](v2-1/before-web-45.png) · [55°](v2-1/before-web-55.png) |
| V2.1 angle comparison | [30°](v2-1/final-web-30.png) · [38°](v2-1/final-web-38.png) · [45°](v2-1/final-web-45.png) · [55°](v2-1/final-web-55.png) |
| Selected overview | [40° orthographic](v2-1/final-web-40.png) |
| Long-lens comparison | [40°, 32° FOV perspective](v2-1/final-perspective-40.png) |
| Landscape phone | [844×390 CSS](v2-1/final-phone-844.png) |
| Follow, Settlements entrance | [Courier, façade and steps](v2-1/final-follow-settlements.png) |
| East architecture | [Trader and Contracts](v2-1/final-east.png) |
| Channel and bridge | [Waterfront](v2-1/final-waterfront.png) |
| Civic high / dispatch low | [Terraces](v2-1/final-terraces.png) |

30° exposes more façades but compresses the walking network in depth. 55° returns
toward the rejected overhead presentation. 40° balances façade visibility and
route separation. Orthographic preserves equal landmark scale across both
islands and consistent touch navigation; perspective remains a camera-only QA
comparison, with distance derived from view size and the long-lens FOV.

## Physical environment

- Three intentional broad hill districts: western civic high ground, northeastern
  Trader ridge and southeastern FX rise. Civic entrance is over eight units above
  low Operations, rather than a barely perceptible wave.
- A deterministic relaxed heightfield locks all office pads and approach courts
  simultaneously. This prevents a later district's blend from tilting an earlier
  entrance. Both exported geometry and physical route samples use this field.
- Coast has four uneven vertical strata; deeper bridge spandrels and abutments
  expose its curved opening. Harbor stairs and deck edges show the water level.
- Main halls have taller façades, raised stone foundations, entrance steps,
  porticoes and rear pavilions assembled from the existing pinned KayKit meshes.
  Archive remains the broad dome landmark rather than a competing tallest tower.
- Narrower promenades, broader rounded turns, mixed stone/dirt paths and restrained
  meadow color variation leave readable open ground. Sparse existing trees remain.
- Web now receives directional shadows, with restrained opacity and ambient fill.
  Water/lagoon/foam do not cast redundant shadows. No large new texture downloads.

## Preserved contract and reproducibility

15 canonical destinations; Operations west, Trader east; one northern walking
bridge; central harbor ferry (5 minutes); matching diagonal outer tubes (3 minutes).
Story walk costs still derive from physical route length and the original pilot
scale. The original production game is untouched. No interiors or quests added.
The existing CC0 manifest and pinned 33 source files remain in use.

`bash tools/build_web.sh` regenerates editable Blender sources and GLBs, validates
geometry/corridors/entrance levels, imports Godot, tests actual physics journeys,
then exports single-threaded Compatibility Web. `tools/test_v2_browser.py` exercises
1920×1080 and 1440×900 desktop plus 844×390 and 667×375 touch viewports.
`tools/review_v21.py` reproduces camera-only review captures from that Web build.

Source models and Web build are Actions artifacts; generated binaries are not
committed. The public importer allowlists the separate V2.1 preview branch and
retains the previous good release on failed/pending/mismatched candidates. Its
post-deploy check verifies the live commit, 40° camera and orthographic projection.

Cloud Chromium touch emulation is not a physical iPhone Safari performance test.
The temporary KayKit courier remains a human stand-in, not approved Cooper art.
