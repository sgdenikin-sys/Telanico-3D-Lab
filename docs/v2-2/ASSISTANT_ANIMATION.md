# Canonical Assistant animation

Read-only source: VorGun-Godot-Clean-Test, fc5e861f0c899ae5925625ff2191a41d7043d957.
Copied byte-for-byte from `web/rabbit_animation_bridge.js` and
`assets/ui/HUD/RUNTIME/rabbit gif test.gif` to this project's godot/web/.

- GIF SHA-256: d0893612f0e68d73c89793fb22beb0483b7dd073f473700229d4caa602541964
- Bridge SHA-256: 794290e46cc62fb4ef4a44be14e446d206ccb7beb7677b64e3e153d8223d60d0
- Native PNG remains behind browser GIF; reduced-motion/missing GIF uses PNG.
- Browser plays GIF for 4100 ms, wipes to contextual PNG over 115 ms,
  then waits 17000 ms before repeating. Layout sync every 0.18 seconds.
- Modal close/restart hides GIF and cancels timers. No new artwork or decoder.

Patch also removes Diorama HUD action; corrects the clock's round source art;
centres compact Invoice, Assistant and Menu cards; triples courier visual scale
and walking speed, preserving collision footprint, route costs and deadlines.
