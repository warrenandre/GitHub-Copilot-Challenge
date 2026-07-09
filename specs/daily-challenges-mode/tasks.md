# Phase 3 - Tasks

## Inputs
This task plan is based on approved design in specs/daily-challenges-mode/design.md.

## Ordered Implementation Tasks

### T1 - Define Challenge Domain Model In Python
Deliverables:
- Add challenge template constants and typed structures in games/snake/src/main.py.
- Add challenge initialization path tied to new daily challenge input from JS.
Done when:
- Python can represent active challenge id/type/target/label cleanly.

### T2 - Implement Python Progress Tracking And Completion Logic
Deliverables:
- Add tracker logic using existing gameplay signals (score, survival time, bills collected).
- Add one-time completion transition per run.
- Expose challenge snapshot accessor used by bridge.
Done when:
- Snapshot returns correct progress and completion for all challenge types.

### T3 - Add JavaScript Daily Challenge Service
Deliverables:
- Implement day key generation and deterministic challenge selection.
- Implement local storage load/save with schema validation and safe fallback.
- Implement record shape under snakeCashRush.dailyChallenges.v1.
Done when:
- Same day always yields same challenge; completion persists after reload.

### T4 - Wire Python <-> JS Integration
Deliverables:
- Pass selected daily challenge from app.js into game initialization/restart path.
- Consume Python challenge snapshot each update cycle.
- Trigger persistence on completion transition.
Done when:
- Challenge progress and completion reflect live game state and persist once per day.

### T5 - Build Daily Challenge UI Panel
Deliverables:
- Update games/snake/src/index.html with objective/progress/badge placeholders.
- Update games/snake/src/styles.css for responsive panel styling.
- Render recent badges list (limit 7) and storage warning state.
Done when:
- UI is visible, non-intrusive, responsive, and does not alter controls/restart flow.

### T6 - Resilience And Edge Case Hardening
Deliverables:
- Handle unavailable local storage gracefully.
- Handle malformed persisted payload by resetting safely.
- Guard against duplicate completion writes for same day.
Done when:
- Game remains playable with clear non-blocking messaging in failure modes.

### T7 - Performance Verification
Deliverables:
- Ensure DOM updates are conditional on state change.
- Verify no expensive per-frame storage operations.
- Manual playtest on typical laptop browser for smoothness.
Done when:
- No noticeable lag compared to baseline gameplay.

### T8 - Testing And Documentation
Deliverables:
- Add/update focused tests or deterministic test helpers for challenge evaluators.
- Add manual test checklist to games/snake/README.md.
Done when:
- Core challenge scenarios and regressions are documented and reproducible.

## Testing Strategy

### Unit Tests
- Challenge evaluator correctness for each type.
- Deterministic dayKey -> challenge mapping.
- Schema validation of persisted badge store.

### Integration Tests
- Python snapshot -> JS UI rendering path.
- Completion event triggers exactly one save for same day.
- Reload restores completion badge from local storage.

### Manual Tests
- Complete each challenge type and verify badge creation.
- Verify challenge rotates on date change simulation.
- Verify restart flow and controls behave exactly as before.
- Verify behavior when local storage is blocked.
- Verify smooth performance during extended run.

## Rollout Notes
- Feature ships as a non-breaking additive mode integrated into current gameplay UI.
- No migration needed beyond creating default empty local storage structure.

## Rollback Notes
- Disable Daily Challenge panel rendering and service wiring in app.js.
- Keep game loop unchanged; remove challenge hooks if rollback is required.
- Existing local storage keys can remain harmlessly unused.

## Definition Of Done Checklist
- [ ] One deterministic daily objective is shown each day.
- [ ] Progress updates correctly in active gameplay.
- [ ] Completion is awarded once per day with badge visible.
- [ ] Badge data persists across reloads in same browser profile.
- [ ] Local storage failure degrades gracefully without gameplay break.
- [ ] Controls and restart flow remain unchanged.
- [ ] No noticeable performance regression on typical laptop browsers.
- [ ] Tests/checklist updated and passing/manual-verified.

## Approval Gate (Simulated)
Approved with no changes.
