# V2.2 migration checkpoint — not a playable V2.2 release

## References and preservation

Target base: [V2.1 8319d91](https://github.com/sgdenikin-sys/Telanico-3D-Lab/commit/8319d91c56be7bfbd25535a5a802e5e7de44662c).
Canonical source: [VorGun fc5e861](https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test/commit/fc5e861f0c899ae5925625ff2191a41d7043d957),
its 6,679-line `main.gd`, `scripts/telanico_invoice_document.gd`,
`docs/SCENARIO.md`, `docs/DECISIONS.md`, `docs/ASSETS.md`,
`docs/WEB_MUSIC_SINGLE_OWNER.md`, and `tests/navigation_regression.gd`.

The source checkout was read only. A disposable `/tmp` project copy was used to
execute the unchanged source `main.gd` and capture reference fixtures. No source
repository branch, file, PR or deployment was changed. V2.1 geometry, camera,
viewport, input handlers and playable main scene are unchanged in this checkpoint.
No V2.2 publication is permitted from this checkpoint. Existing public preview
remains V2.1. The user's V2.2 instructions explicitly extend the older
AGENTS/README overworld-only scope; they do not authorise modifying production.

## Feature inventory

| Feature / authority | Reuse / adaptation | Checkpoint status |
| --- | --- | --- |
| Character selection, `_build_character_select`, `_select_cooper` | Actual Cooper/Wolf/Eagle/Riley portraits; only Cooper enabled | Inspected, not ported |
| Assignment introduction, `_build_intro_ui`, `_start_pilot` | Preserve exact original story; opening sequence requires explicit ordering adaptation | Inspected, not ported |
| Draft invoice and renderer, `_refresh_invoice`, `telanico_invoice_document.gd` | Reuse actual paper/markup/signature/stamp PNGs and renderer; state dictionary extracted | Dictionary tested; renderer/assets not yet copied or connected |
| Evidence/prerequisites, `_dialogue_options`, `_choose_dialogue`, `_release_blockers` | Extract pure rules and exact original dialogue, independent of Node3D | Implemented in `story_session.gd`, source parity tested |
| Greetings, repeat visits and lunch, `_office_*` | Exact canonical text/options/schedules; preserve visit counts | Implemented and tested at session level |
| Assistant facts, hints, praise/emotions, `_assistant_*` | Exact evidence-backed facts/hints/praise; approved six PNG reactions | Rules extracted; presentation/reward sequencing not ported |
| Office art, `_office_background_path`, `_office_desk_path`, `_office_portrait_path` | Two original illustrated backgrounds, four desks and nine frontal portraits; retain source layout and four-texture cache | Files verified; visual scene not ported |
| Office entry/return | New 3D arrival confirmation -> explicit Enter -> office -> exact entrance | Session contract tested; world/UI wiring pending |
| HUD/menu/clock, `_build_hud`, `_build_game_menu`, `_update_quest_clock` | Reuse original artwork; adapt placement without changing Safari viewport or world gesture code | Not ported |
| Audio, source browser bridge + native fallback | Single browser music owner; do not start duplicate MP3 on character selection or office entry; retain separate music/SFX controls | Source invariant inspected, not ported |
| Deadline/results/restart | Shared session owns 12:00 start, strict 14:00 deadline; distinct 14:30 payment cutoff | Session win/loss/reset-by-new-instance tested; original result screens/restart UI pending |
| World walking/boat/tube | Preserve V2.1 movement/animation; charge shared session once per confirmed trip | Compatibility specified below; world still uses V2.1 clock |
| Original regression suite | Port scenario assertions; preserve V2.1 native physical journeys and browser navigation checks | 61 session assertions + 1,116 source comparisons; UI/browser story suites pending |
| Production deployment | Private tested artifact -> public import, never private development sources | Intentionally not changed; incomplete integration must not replace V2.1 |

## All fifteen landmark mappings

| V2.1 landmark | Canonical destination / treatment |
| --- | --- |
| `settlements` | `SETTLEMENTS HALL` |
| `operations` | `OPERATIONS` |
| `finance` | `TRADE FINANCE` (separate from LC Desk) |
| `lc` | `LC DESK` |
| `compliance` | `COMPLIANCE` |
| `trader` | `TRADER` |
| `contracts` | `CONTRACTS` |
| `vat` | `VAT` |
| `fx` | `FX TOWER` |
| `coffee`, `archive` | No canonical quest/interior branch found. Keep landmarks; do not invoke the source's default Settlements branch here. |
| `tube_w`, `tube_e` | Transport, not office dialogue |
| `dock_w`, `dock_e` | Harbor launch transport, not office dialogue |

## Canon compatibility decisions

Implementation at the pinned commit is authoritative where historical notes
contradict it. The current source has **fixed price**, with no density escalation
or mandatory fluctuation clause. It does not require the old invoice-date joke
or Compliance as release prerequisites. A chocolate bribe costs exactly 45
minutes; acknowledging training does not charge another minute. The authorised
signed/stamped original comes from the **LC Desk**, after reconciliation and VAT,
not from FX. All these behaviours are retained and tested, not redesigned.

Initially known product: **High Quality Energy (Physical Oil)**. Initially blank
seller/quantity/price/bank/tax remain blank until verified. Final quantity is
8,470 MT, not estimated 8,500; price is USD 612.50, displayed with ten decimals
when verified. Reference 1.0834 has unconfirmed quote direction; do not compute a
numeric total or infer settlement currency from the EUR cutoff. Invoice number,
date and numeric total have no approved values and remain blank.

Current source shows character selection -> assignment briefing -> initial draft;
the V2.2 request specifies intro -> character selection -> overworld. The UI port
must deliberately arrange those existing screens/texts to meet the requested flow,
including initial draft/assistant, without changing the story or treating the
historical order as a new invented story. This checkpoint does not implement it.

### Travel compatibility (not yet wired)

The historical `TRAVEL_MINUTES = 6` constant is not the runtime walking rule.
Original `_walking_minutes` uses ceil(distance / 1.5), with a 0.30-unit negligible
movement threshold. V2.1 uses its existing calibrated map-scale distance / 9.375;
keep that route calculation and visible animation unchanged. Charge the session
its route minutes exactly once at confirmed completion, not real wall-clock
seconds and not both departure and arrival. The slow bridge stays walkable;
original old-map tests forbidding all cross-island walking do not apply to it.

Original boat: west/A departures on :00/:10, east/B on :05/:15, then five minutes
sailing. V2.1 currently charges five minutes without waiting. V2.2 must restore
canonical timetable wait (calculated when actually at the dock) plus five sailing
minutes, and show that cost before boarding. Tube remains three minutes. Existing
V2.1 navigation tests must still test physical motion; story integration tests
must separately assert scheduled waits and exactly-once session charges. No
silent route rebalance is authorised. A successful route through the actual new
geography and lunch windows must be measured before release, not inferred from
the 16-minute dialogue-only winning test.

## Assets and source fidelity

`source-provenance.json` pins the source commit, normalised `main.gd` SHA-256,
19 unchanged extracted method bodies, and 50 existing approved PNGs (HUD,
invoice, office scenes and nine frontal portraits), including sizes and hashes.
It is an availability inventory, not a claim that assets have been ported.
The selected character cards additionally use canonical `assets/mascots/TOP_DOWN`
portraits. No external vegetation pack is required or added.

Run `python tools/verify_story_reference.py /path/to/read-only-source` to verify
these references. Source financial data/dialogue are private development content;
only eventual built Web runtime files may be imported into the public repository.

`story_session.gd` retains rules/text independently from rendering. It emits
state/dialogue/result/office-exit signals; a presenter must handle dialogue line
paging, typewriter/reward ordering, invoice review, modal input isolation and
art. The public `choose` accepts only displayed options; private source methods
remain available for regression parity. `enter_landmark` requires an explicit
caller-confirmed arrival and exact entrance; it does not itself validate or move
the world actor. A world adapter must enforce arrival and disable background
navigation while an office/intro/modal is open. That adapter does not exist yet.

## Validation and exact stopping point

Passed locally in the cloud, Godot 4.6.3:

- `test_story_session.gd`: 61 assertions (canonical success, initial blanks,
  verification failures, assistant persistence, explicit office session/return,
  missing content, lunch, boat timetable, 45-minute training, strict deadline).
- `test_source_parity.gd`: 1,116 state/dialogue/options/blocker comparisons across
  16 fixture cases executed against original unchanged `main.gd`. The canonical
  winning path has the same 16 meaningful choices and result. These fixtures are
  a selected behavioural sample, not the entire 2,167-line source regression suite.
- `verify_story_reference.py`: all 19 method hashes and 50 PNG assets verified.

The original script parses/runs in the target's Godot 4.6.3 despite its 4.7.2
comment. Full original game/UI/Web compatibility is still unproven. First export
attempt omitted writable XDG locations and Godot aborted in this cloud sandbox;
rerun uses `/tmp/telanico-overworld-{data,config,cache}`. Build logs remain under
`/workspace/scratch/v22-*` and normal private build logs under `build/logs`.

**Stopped at the shared-session foundation, before any playable scene wiring.**
The main scene still runs V2.1. No V2.2 intro/HUD/interior is represented as done.
Next recoverable step: implement a world-session adapter and original illustrated
office presenter, test real arrival -> Enter -> original office -> exact return
and single travel charge, then restore opening/HUD/audio and full end-to-end
scenario/browser gates. Do not stamp or deploy V2.2 until those gates pass.
