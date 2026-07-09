# Task Plan Spec

## Implementation Tasks
1. Define Daily Challenge product behavior contract
Owner action: Product/Frontend defines mode entry, challenge identity rules, and score display expectations in a short behavior note.

2. Add mode-state model and routing
Owner action: Frontend implements explicit mode state handling so Daily and Normal startup paths are isolated.

3. Implement deterministic daily seed resolver
Owner action: Frontend implements local-date day key generation and deterministic seed derivation with a fixed in-app salt.

4. Create fixed board modifier catalog
Owner action: Gameplay owner defines vetted modifier profiles and deterministic selection mapping from seed to profile.

5. Integrate challenge config into game initialization
Owner action: Frontend applies challenge modifiers at round start only when Daily mode is active.

6. Extend local persistence for daily best score
Owner action: Frontend adds date-scoped storage read/write logic for Daily best, with fallback-safe parsing.

7. Add Daily Challenge HUD badge and daily-best display
Owner action: UI owner introduces compact challenge indicators and responsive styles for mobile widths.

8. Preserve Normal mode behavior explicitly
Owner action: Frontend verifies normal startup path, controls, and scoring remain untouched by Daily additions.

9. Add day-transition refresh behavior
Owner action: Frontend recalculates day key on new sessions and refreshes challenge context when date changes.

10. Write manual validation checklist
Owner action: QA/Frontend documents reproducible manual test cases for determinism, persistence, HUD state, and mode isolation.

## Task Dependencies
1. Task 1 must complete before Tasks 2 through 7.
2. Task 2 must complete before Tasks 5, 7, and 8.
3. Task 3 and Task 4 must complete before Task 5.
4. Task 6 must complete before Task 7 and Task 10.
5. Tasks 5 through 9 should complete before final validation in Task 10.

## Validation And Test Tasks
1. Verify same local date produces identical challenge modifiers across app reloads.
2. Verify changing local date produces a new daily challenge profile.
3. Verify Daily badge appears only in Daily mode and is absent in Normal mode.
4. Verify Daily best score persists across reloads for the same day.
5. Verify Daily best score is day-scoped and does not overwrite previous day values.
6. Verify Normal mode score behavior and gameplay loop match pre-feature behavior.
7. Verify feature works offline with no network calls.
8. Verify HUD readability and no overlap on representative mobile viewport sizes.
9. Verify invalid or missing storage data falls back gracefully without breaking play.
