# Intent: Snake Power-Up System

## User Request
Add a power-up system to the Snake Cash Rush game where the snake can collect special items
that give temporary abilities: speed boost, invincibility, and double points.

## Problem Statement
The current game loop has a single collectible mechanic — cash bills. While effective, there is
no variety or strategic decision-making beyond avoiding walls and the snake's own body. Players
who master the core loop have no additional challenge or reward layer to engage with. A power-up
system introduces temporary, skill-rewarding abilities that add excitement and depth without
changing the fundamental Snake formula.

## Target Users
Casual browser-based players already familiar with Snake Cash Rush. Players looking for more
engagement beyond the base mechanic — particularly those who have mastered the core loop and
want additional challenge and replayability.

## Inferred Product Intent
- Increase session length and replayability by giving players a reason to chase special items
  beyond cash bills.
- Reward risk/reward decisions: some power-ups may appear in dangerous positions, requiring
  players to weigh the benefit against the collision risk.
- Reinforce the money/finance theme with power-ups that feel thematically consistent (e.g.,
  "Bull Run" for speed, "Hedge Fund" for invincibility, "Bonus Round" for double points).
- Keep the visual style consistent with the existing dark-glass, emerald-accent aesthetic.
- Preserve the single-file Python architecture (`main.py`) with no backend additions.

## Assumptions
- Power-ups are bonus collectibles that appear alongside the existing cash bill — the cash bill
  is never replaced by a power-up.
- Only one power-up is present on the board at any time.
- Power-ups have a finite on-board lifespan: if uncollected within a set window, they despawn.
- Power-up effects are mutually exclusive — collecting a new power-up while one is active
  replaces the previous effect.
- The three initial power-up types are: **Speed Boost**, **Invincibility**, and **Double Points**.
- Speed Boost temporarily reduces the tick interval (faster movement).
- Invincibility temporarily prevents death from wall or self-collision.
- Double Points multiplies the score awarded per cash bill by 2 while active.
- All power-up state is transient and resets fully on game restart.
- Implementation stays within `main.py` and `index.html`/`styles.css`; no new source files.

## Constraints
- **Architecture**: Python-only game logic via PyScript; `js` module for all DOM access;
  `create_proxy` for all Python callbacks passed to JavaScript.
- **Encapsulation**: All new state must live inside the `SnakeCashRush` class.
- **No backend**: Browser-only, no server-side persistence.
- **No new source files**: Feature lives in the existing `main.py`, `index.html`, `styles.css`.
- **Existing tick system**: Speed Boost must work with the existing `tick_ms` / `accumulator`
  pattern, not replace it.
- **Existing score system**: Double Points multiplies `SCORE_PER_BILL`; best-score logic is
  unchanged.
- **PEP 8 + project standards**: Type hints, docstrings, `UPPER_SNAKE_CASE` constants,
  `snake_case` methods, `PascalCase` classes.

## Acceptance Criteria
1. Three power-up types are implemented: Speed Boost, Invincibility, and Double Points.
2. A power-up spawns on the board at a random unoccupied cell not overlapping the cash bill or
   any snake segment.
3. Collecting a power-up activates its effect immediately for a defined duration.
4. Speed Boost reduces `tick_ms` while active, reverting to the pre-boost value on expiry.
5. Invincibility prevents the game-over condition from wall and self-collision while active.
6. Double Points awards `SCORE_PER_BILL * 2` per cash bill while active.
7. Only one power-up is visible on the board at any time.
8. An active power-up effect is clearly communicated in the HUD (type + remaining duration or
   a visual indicator).
9. Power-ups despawn automatically if not collected within their on-board lifespan window.
10. Power-ups spawn periodically (not every tick) so they feel like rare events.
11. All power-up state (`active_powerup`, timers, effect overrides) resets in `reset_state()`.
12. Power-up items are visually distinct from cash bills and from each other.

## Out of Scope
- More than three power-up types in the initial release.
- Stacking or combining simultaneous power-up effects.
- Negative power-ups or hazard items (slowdown, reversed controls).
- Persisting power-up collection counts or history to local storage.
- Mobile touch controls for power-up interactions.
- Sound effects or audio feedback.
- Animated sprite sheets for power-up icons (canvas drawing or emoji glyphs are sufficient).

## Open Questions
1. **Spawn frequency**: Should power-ups spawn on a fixed timer (e.g., every 15 seconds), on
   a random probability each tick, or after a fixed number of cash bills collected?
2. **On-board lifespan**: How long should an uncollected power-up remain before despawning
   (e.g., 8 seconds)?
3. **Effect durations**: What are the target durations for each power-up?
   - Speed Boost: ~5 seconds?
   - Invincibility: ~4 seconds?
   - Double Points: ~8 seconds?
4. **Invincibility behaviour at walls**: Does invincibility allow the snake to pass through
   walls (wrap-around teleport), or simply prevent the death trigger while the snake stays
   at the wall cell?
5. **Speed Boost interaction with progressive difficulty**: The base game already accelerates
   the snake as score rises. Should Speed Boost stack additively with the current `tick_ms`,
   or apply a fixed floor?
