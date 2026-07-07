# Summary — Power-Up System

## Scope

### Included
- Two power-up types: **Double Points** and **Invincibility**.
- Timer-based spawning (8–15s random intervals) with 10s despawn.
- Fixed 6-second effect duration per collection.
- Visual feedback: snake color change + canvas-rendered timer bar.
- No stacking — new collection replaces active effect.
- Debug snapshot includes power-up state.

### Not Included
- Negative power-ups or penalties.
- Persistent upgrades between runs.
- Speed boost power-up (deferred to future iteration).
- Sound effects or particle animations.
- HTML/CSS changes (all rendering stays on canvas).

## Approach

1. **Data modeling first** — Define enum and dataclass so all subsequent code has clear types.
2. **State management** — Wire up initialization and reset before adding behavior.
3. **Core mechanics** — Spawn → collect → activate → expire pipeline.
4. **Effect logic** — Implement each effect as a targeted conditional in the existing `advance()` flow.
5. **Rendering last** — Visual polish once mechanics are proven correct via `snapshot_json`.

All work happens in a single file (`main.py`) with no new dependencies, making it straightforward to review and test.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Invincibility feels too powerful | Medium | Medium | Walls still kill; 6s is short. Tune duration if needed. |
| Timer drift at very low frame rates | Low | Low | Use cumulative frame delta; same pattern as existing tick accumulator. |
| Power-up spawns on top of cash | Low | Low | Exclude cash position from spawn candidates. |
| Visual clutter on small grid | Low | Medium | Only one power-up on board at a time; distinct shapes per type. |

## Estimated Effort

| Area | Tasks | Size |
|------|-------|------|
| Data models & constants | 1–2 | **S** |
| State management | 3 | **S** |
| Spawn/despawn logic | 4–5 | **M** |
| Collection & effects | 6–10 | **M** |
| Rendering & visuals | 11–12 | **M** |
| Debug integration | 13 | **S** |
| **Overall** | **1–13** | **M** (estimated 2–3 hours) |
