# Content wiring plan — SIDHE & STONE v0.2.0

Written by Dross while the three children were still running. This is the
integration decision for the NEW art, and it exists so that the art is not
left sitting in the atlas unused.

## The tension

Amre asked to "greatly improve and polish the game's pixel art while adding
content in a clear, unified visual style".

But the hard constraint on the GUI and art work is: **preserve gameplay
behaviour, economy, RNG, balance constants and state-machine behaviour.**

New dig types, new artefact grades and new reel symbols all change the
simulation:

- A new **dig type** changes `SimCore.DIGS` — new cost, new duration, and a
  new source of finds. It changes what a day is worth.
- A new **artefact grade** changes `GRADE_ORDER`, which changes the find
  tables, the exhibit values and therefore the revenue curve. The whole
  365-day autopilot fixture moves.
- A new **reel symbol** changes `ReelCore.SYMBOLS` — the weights and
  multipliers are the payout distribution. Adding four symbols changes the
  reel's expected value.

All three of those would invalidate `web/tests/fixtures/godot_curve_fixture.json`
and require regenerating the economy parity fixture, plus a balance pass to
prove the new content did not silently break the money curve. That is a
balance task, not a polish task, and it is a separate release.

## The decision

**v0.2.0 integrates the new art as presentation-only content.** Every new
sprite gets a home on screen, and nothing in the simulation changes — no new
digs, no new grades, no new reel symbols, no changed weights, no changed
values, no changed RNG.

The art is therefore split by what it can safely be:

### 1. New artefacts (6) — the curator's reference shelf
`artefact_bone`, `artefact_coin`, `artefact_bronze`, `artefact_amber`,
`artefact_fabric`, `artefact_glass`

These become a decorative **specimen shelf** on the Curator screen: the
curator's own reference collection, drawn as a row of small framed specimens.
It is scenery, not inventory — it is not sold, not exhibited, not stolen, and
it does not appear in any grade table.

This is exactly right thematically. A museum curator absolutely has a shelf of
reference specimens, and it explains why the player knows what a bronze looks
like before they dig one up.

### 2. New visitors (3) — the gallery floor
`visitor_d`, `visitor_e`, `visitor_f`

The gallery already draws a row of visitors beside the display cases
(`visitor_a`, `visitor_b`, `visitor_c`) purely as the people in the room. The
three new visitors join that row. This is the cheapest possible win: the
museum stops looking like three people and starts looking like a room with
visitors in it.

Note the distinctness rule that already holds and must keep holding: the
curator (ACDKNSU) must stay visually distinct from every visitor, and the
visitors stay distinct from each other by their accent key (M / U / X).

### 3. New props (6) — the museum furniture
`prop_desk`, `prop_lamp`, `prop_plaque`, `prop_rope`, `prop_ladder`,
`prop_tarpaulin`

Drawn as furniture and fittings around the museum screens: the desk and the
lamp in the curator's room, the plaque on the exhibit wall, the rope and
ladder and tarpaulin at a dig site. Decoration only.

### 4. New reel motifs (4) — the omens panel
`symbol_key`, `symbol_bell`, `symbol_feather`, `symbol_crystal`

These are drawn as **omen motifs** on the Goals/Omens screen, alongside the
existing luck and omen material. They do NOT join `ReelCore.SYMBOLS` and they
are not in the reel's weight table. They are a visual vocabulary for the
game's omens, not new reel outcomes.

## What is deliberately NOT done in v0.2.0

- No new dig types. `SimCore.DIGS` keeps its five entries.
- No new artefact grades. `GRADE_ORDER` keeps its six entries.
- No new reel symbols in the payout table. `ReelCore.SYMBOLS` keeps its six.
- No changed weights, multipliers, costs, durations, exhibit values or
  theft chances.
- No changed RNG. The seed stream and the draw order are untouched.
- No changed state machine. `src/game_state.gd` and `web/src/sim/game-state.ts`
  are not touched by this release.

This is what makes the economy parity fixture still valid, and it is why the
release can claim "no gameplay change" honestly rather than approximately.

## The follow-up (a real v0.3.0 candidate)

Turning the unused candidates into *playable* content is a genuine feature
and it is worth doing — but it is a balance feature:

1. Add dig types to `SimCore.DIGS` (GDScript) **and** `web/src/sim/sim-core.ts`
   (TypeScript) in the same change, with identical costs and durations.
2. Add artefact grades to `GRADE_ORDER` in both engines.
3. Add reel symbols to `ReelCore.SYMBOLS` and `sim/reel_core.gd` in both.
4. Regenerate `web/tests/fixtures/godot_curve_fixture.json` from the Godot
   run — the parity test compares element for element, so the fixture is
   derived, never hand-edited.
5. Run the balance tools: `sim/run_sim.gd`, `sim/run_player_balance.gd`, and
   the TypeScript equivalents `web/src/sim/run-sim.ts` and
   `web/src/sim/run-player-balance.ts`, and compare the money curve and the
   player path against the previous release.
6. Update the GDD's balance tables to match.

That is a separate release with its own release notes, because it changes the
game rather than the presentation of the game.
