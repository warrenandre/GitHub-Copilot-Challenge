# Summary: Snake Cash Rush Power-Up System

## Scope
This feature introduces temporary collectible power-ups to Snake Cash Rush with three initial effect types in scope: speed boost, invincibility, and double points. The implementation is limited to the browser-based game runtime and keeps existing controls, restart flow, and baseline cash scoring behavior intact when no effect is active.

In scope outcomes:
- Spawn power-ups on valid board cells during active runs.
- Activate temporary effects on pickup and auto-expire them.
- Show active effect and remaining duration in HUD/status.
- Clear all power-up state on game over/restart.
- Expose effect state in debug snapshots for verification.

Out of scope for this phase:
- Server-side gameplay logic.
- Long-term persistence/analytics unless explicitly approved.
- New power-up types beyond the initial three.

## Approach
The design uses a single-class, run-local architecture inside `SnakeCashRush`.

Execution strategy:
1. Resolve outstanding balancing and behavior decisions from design placeholders.
2. Extend class state with power-up pickup/effect/timing fields.
3. Implement deadline-based effect engine tied to run clock.
4. Integrate spawn, pickup, collision, score, and movement updates into existing loop.
5. Add rendering + HUD visibility for active effects.
6. Extend snapshot/debug surface and validate AC1-AC5.

This approach minimizes regression risk by layering features onto existing loops and preserving current input and restart semantics.

## Risks
Top delivery risks:
1. Unresolved behavior decisions can block implementation or cause rework.
   - Open items include spawn cadence, stacking policy, same-type recollection behavior, exact durations, and speed model.
2. Balance instability may reduce gameplay clarity.
   - Aggressive speed multipliers or frequent spawns may feel chaotic or unfair.
3. Collision edge cases under invincibility may create unexpected movement outcomes.
   - Especially around wall/self-overlap behavior definitions.
4. UX ambiguity if visual tokens/HUD messaging are not finalized early.
   - Players may not understand which effect is active and for how long.
5. Performance regressions if render/status updates are inefficient in frame loop.
   - Requires lightweight checks and quick validation in target browsers.

## Estimated Effort
Assuming timely decision sign-off and no major architecture changes:
- Decision finalization: 0.5 day
- Core implementation (state, timing, spawn, integration): 1.5 to 2 days
- UI/HUD and debug snapshot updates: 0.5 to 1 day
- Validation, tuning, and bug-fix pass: 0.5 to 1 day

Total estimate: 3 to 4.5 engineer-days.

## Assumptions
The following assumptions are carried from design and must be confirmed:
1. Cash and one board power-up can coexist on different cells.
2. Only one active effect is allowed at a time.
3. Re-collecting the same active type refreshes duration to full.
4. Invincibility suppresses death checks only; it does not alter scoring/progression.
5. Double points applies only to cash pickups.
6. Power-up data is run-local only (no persistent cross-run stats).
7. HUD uses a dedicated `powerUpStatus` line with active effect + remaining time.

If any assumption changes, task sequencing remains valid but implementation details and acceptance tests must be updated before coding starts.
