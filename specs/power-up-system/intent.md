# Intent — Power-Up System

## Goal

Add collectible power-up items to Snake Cash Rush that grant the snake temporary abilities, increasing gameplay variety and replayability.

## Problem Statement

The current game loop is one-dimensional — the only objective is collecting cash bills while avoiding walls and the snake's own body. After a few runs the experience becomes repetitive because there are no mid-run surprises or strategic choices. A power-up system introduces moments of excitement and short-term decision-making.

## Target Users

- Casual browser players looking for more engaging, varied runs.
- Returning players who have already mastered basic cash collection.

## Constraints

- **Technical**: All logic must stay within the `SnakeCashRush` class in `main.py` (PyScript/Pyodide). No new files or external dependencies.
- **Scope (v1)**: Start with 1–2 power-up types (e.g. double points and invincibility). Additional types (speed boost, etc.) will be added in a follow-up.
- **No negative power-ups**: Only beneficial effects.
- **Single-run only**: Power-ups do not persist between game runs.
- **Rendering**: Must work within the existing canvas-based renderer.

## Acceptance Criteria

1. Power-up items spawn on the board at random intervals (approximately every 8–15 seconds).
2. Only one power-up item is present on the board at a time.
3. Collecting a power-up activates its effect for a fixed duration (5–8 seconds).
4. If a new power-up is collected while one is active, the new effect replaces the old.
5. The snake's color changes while a power-up is active to indicate the current effect.
6. A timer bar or countdown is visible in the HUD showing remaining effect duration.
7. When the effect expires, the snake returns to normal appearance and behavior.
8. "Double Points" power-up doubles cash bill value for its duration.
9. "Invincibility" power-up allows the snake to pass through its own body without dying (walls still kill).
10. Power-up items despawn if not collected within a reasonable window (~10 seconds).
11. The `snapshot_json` debug helper includes active power-up state.
12. No regressions to existing cash collection, scoring, or best-score persistence.
