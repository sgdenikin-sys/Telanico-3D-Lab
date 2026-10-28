# Painted buildings game integration

Build source: `15a0709c3419d19a29ec46968887f029b9e7dfb3`. Existing Godot 4.6.3 Compatibility/Web export.

- Hall V4: 10,805 triangles; MAIN/ROOF/TRIM 2048px textures; existing placement,
  .63 scale, independent door and wind controllers retained.
- Meridian Palace Lite: 10,990 triangles; embedded 4096px atlas; replaces free
  Trade Finance home_B visual. Scale .52, centre offset (0,.04,1.404), +Z front.
- Original routes, selectable areas, entry coordinates, story and lighting retained.
- Actual Web: three landmark screenshots, one Finance entry, no browser errors.
  No full story regression or physical-device claim.
- Native Hall controller: 100-degree doors, four morph flags, closed loop seam,
  independent playback and transparent glass passed.

Public screenshots: `site/evidence/painted-buildings-15a0709/` in the existing
Telanico-3D-Web publication repository. Original sources stay in Lab artifacts.
