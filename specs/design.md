# Technical Design Spec

## Architecture Decisions And Rationale
1. Add a mode-aware game configuration layer inside the existing client-side game flow.
Reason: isolates Daily Challenge behavior while preserving Normal mode logic and minimizing regression risk.

2. Generate the daily challenge from a deterministic local seed derived from local date plus a stable game salt.
Reason: meets one-challenge-per-day requirement without external services.

3. Use a predefined modifier catalog and deterministic selection rules.
Reason: ensures “fixed board modifiers” are controlled, testable, and bounded for gameplay balance.

4. Extend local score persistence with daily namespacing.
Reason: supports best score per day without affecting existing normal score behavior.

5. Reuse existing HUD surface with a mode-conditional badge and daily best display.
Reason: minimal UI footprint, fast load, and lower implementation complexity.

## Components And Responsibilities
- Mode Selector State
Determines whether session runs in Normal or Daily Challenge mode.

- Daily Seed Resolver
Computes the day key and deterministic seed based on local date and fixed app salt.

- Challenge Definition Builder
Maps seed to one challenge profile from a fixed modifier catalog and returns immutable challenge settings for that day.

- Game Engine Integrator
Applies challenge settings at round initialization in Daily mode only; bypasses this path in Normal mode.

- HUD Presenter
Renders Daily Challenge badge and daily best score when Daily mode is active; hides challenge indicators in Normal mode.

- Local Score Store Adapter
Reads and writes best daily score using day-scoped keys; keeps existing normal score keys untouched.

- Daily Transition Guard
On app load and game start, recalculates day key and refreshes challenge context when date changed.

## Data Flow
1. App initializes and reads mode state.
2. If mode is Normal, current behavior executes with no challenge config attached.
3. If mode is Daily:
4. Resolve local day key.
5. Build deterministic seed from day key and static salt.
6. Select challenge modifiers from fixed catalog.
7. Initialize round with selected modifiers.
8. Render HUD badge and current daily best.
9. During play, scoring updates as usual under applied modifiers.
10. On game over in Daily mode, compare run score to stored daily best.
11. Persist score only if run exceeds existing daily best for that day.
12. Next Daily session on same day reuses same challenge and best score.

## Risks And Mitigations
- Risk: Local clock manipulation can alter day key unexpectedly.
Mitigation: Document behavior as local-date based; handle day-key recalculation safely on each session start.

- Risk: Modifier combinations may create unfair or unplayable rounds.
Mitigation: Limit catalog to vetted modifiers and enforce safe bounds.

- Risk: Regression in Normal mode due to shared initialization paths.
Mitigation: Strict mode guardrails and manual regression checklist focused on Normal mode parity.

- Risk: HUD crowding on small screens.
Mitigation: Use compact badge styling, responsive wrapping, and priority placement for score readability.

- Risk: Local storage conflicts or corruption.
Mitigation: Use versioned key prefixes and defensive parse fallback to defaults.

## Affected Specs Assumptions
- Existing architecture supports introducing a mode flag and conditional initialization without major rewrite.
- Existing score storage mechanism can be extended with additional keys.
- Current HUD has enough structure to add one compact badge and one daily-best field.
