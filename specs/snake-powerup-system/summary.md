# Executive Summary: Snake Power-Up System

## What We Are Building
We are adding a power-up collectible system to the Snake Cash Rush browser game. Players will
encounter three special items — Speed Boost, Invincibility, and Double Points — that appear
periodically on the board and grant temporary abilities when collected. The feature introduces
strategic variety to the existing single-collectible loop without changing the core Snake
formula.

## Why We Are Building It
The current game loop relies entirely on the cash bill mechanic. Players who master the core
loop have no additional layer of engagement, which limits session length and replayability.
Power-ups introduce a risk/reward dynamic (chasing a boost in a dangerous position), rewarding
skilled players and keeping the game compelling beyond the first few runs. This directly
supports the product goal of making Snake Cash Rush feel unique and replayable.

## Scope

**Included:**
- Three power-up types: Speed Boost (faster movement), Invincibility (wall wrapping + self-
  collision immunity), and Double Points (2× score per cash bill).
- Periodic board spawning, on-board lifespan (despawn if ignored), and immediate effect
  activation on collection.
- Visual rendering of each power-up type on the canvas (distinct colour + glyph per kind).
- HUD indicator showing the active effect and remaining duration.
- Full state reset on game restart.

**Excluded:**
- More than three power-up types.
- Stacking or combining simultaneous effects.
- Negative power-ups (slowdown, reversed controls).
- Persistence of power-up stats to local storage.
- Sound effects or mobile touch support.

## Technical Approach
The feature extends the existing `SnakeCashRush` Python class in `main.py` with new state
fields, a `PowerUp` data object, and five new methods. All timing is managed through the
existing tick-based game loop — no new browser timers are introduced. Changes are contained
to the three existing source files (`main.py`, `index.html`, `styles.css`).

## Delivery Plan
8 tasks, sequenced so foundational data model work (Tasks 1–2) unblocks all subsequent tasks.
Tasks 3–6 can proceed in parallel after Task 2. Tasks 7–8 depend on the game logic being
complete.

```
Task 1 (constants + dataclass) ──┐
                                 ├─► Task 3 (spawn_powerup)    ─────┐
Task 2 (reset_state) ────────────┤                                  ├─► Task 5 (advance) ─► Task 7 (HUD) ─► Task 8 (smoke test)
                                 ├─► Task 4 (apply/expire effect) ──┤
                                 └─► Task 6 (draw_powerup) ─────────┘
```

Key milestones:
- **M1** (end Task 2): Data model and state initialisation complete; game still runs unmodified.
- **M2** (end Task 5): Full game logic operational; power-ups spawn, activate, and expire correctly.
- **M3** (end Task 8): Feature complete, HUD polished, all acceptance criteria verified.

## Estimated Effort
**3–4 engineering days** (1 engineer).

| Task | Estimate |
|---|---|
| Task 1 — Constants + dataclass | XS (~1 h) |
| Task 2 — `reset_state()` additions | XS (~30 min) |
| Task 3 — `spawn_powerup()` | S (~1.5 h) |
| Task 4 — `apply_effect()` / `expire_effect()` | S (~2 h) |
| Task 5 — `advance()` integration | M (~4 h) |
| Task 6 — `draw_powerup()` + `draw()` | S (~2 h) |
| Task 7 — HUD element + `update_powerup_hud()` | S (~2 h) |
| Task 8 — Smoke test + polish | S (~2 h) |
| **Total** | **~15 h** |

## Key Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Speed Boost interacts badly with progressive difficulty (tick_ms already near floor) | Medium | `SPEED_BOOST_FACTOR` is applied to the current `tick_ms`, not `BASE_TICK_MS`; the floor `MIN_TICK_MS` is always respected. Pre-boost value is saved and restored. |
| `advance()` changes introduce regression in existing cash collection or collision | Medium | Task 5 includes explicit verification of all existing ACs alongside new ones. The modification is additive — new logic is inserted into defined positions rather than rewriting existing branches. |
| PyScript canvas rendering performance degrades with additional draw calls | Low | One extra `fillRect` + `fillText` per frame is negligible; PyScript's primary overhead is Python parsing at load time, not per-frame operations. |

## Success Metrics
- All 12 acceptance criteria from `intent.md` pass in a Chromium browser before release.
- No JavaScript console errors during normal play or restart.
- Players can observe all three power-up types appearing and activating within a single game
  session (qualitative verification by the feature author).
- Session length metric (time per run) increases vs. baseline after release, indicating the
  new mechanic is engaging players longer — measurable via browser telemetry if added in a
  future analytics task.
