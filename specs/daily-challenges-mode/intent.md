# Phase 1 - Intent

## Feature
Daily Challenges mode for Snake Cash Rush.

## User Goal And Business Outcome
- User goal: Players should have one clear daily objective they can attempt in normal gameplay.
- Business outcome: Increase repeat daily engagement through lightweight daily goals and visible completion badges.

## Problem Statement
Snake Cash Rush currently has no time-based progression loop that encourages players to return each day. A daily rotating objective system can create habitual play without requiring backend services.

## Target Users
- Returning players who want short daily goals.
- New players who benefit from guided objectives.
- Casual players on laptop browsers.

## Scope
### In Scope
- One active objective per local calendar day.
- Rotating objective types, including examples:
  - Score target (for example, reach 100 points).
  - Survival target (for example, survive 90 seconds).
  - Collection target (for example, collect 15 bills).
- In-game UI indicator showing the current daily objective and progress.
- Completion badge state persisted in browser local storage.
- Badge history available for prior completed days (local to browser/profile).

### Out Of Scope
- Server-side identity, cloud sync, or cross-device persistence.
- Changes to existing movement controls.
- Changes to existing restart flow semantics.
- Leaderboards, social sharing, or multiplayer.

## Constraints
- Browser-only implementation; no server/database dependencies.
- Preserve architecture boundaries:
  - Python game logic in games/snake/src/main.py.
  - Browser bridge and UI in games/snake/src/app.js and HTML/CSS.
- Keep existing controls and restart flow unchanged.
- Maintain smooth performance on typical laptop browsers.

## Risks And Dependencies
### Risks
- Local date/time tampering can alter daily challenge rotation.
- Local storage may be unavailable or blocked in some browser/privacy modes.
- Poorly scoped UI updates could introduce frame drops.

### Dependencies
- Existing browser bridge APIs for RAF and local storage access.
- Current scoring, time tracking, and bill collection signals from gameplay loop.

## Assumptions
- Daily key uses player local date (YYYY-MM-DD) rather than UTC.
- Only one challenge can be active per day.
- Challenge completion is binary per day (completed or not completed).

## Acceptance Criteria
- AC1: On first load each local day, the game deterministically selects exactly one objective from a defined rotation set and displays it in the UI.
- AC2: Progress toward the active objective updates during gameplay without changing existing controls or restart behavior.
- AC3: When objective conditions are met, completion is marked once for that day and a badge is shown.
- AC4: Completion badges persist in browser local storage and are restored after page reload in the same browser profile.
- AC5: If local storage is unavailable, gameplay still works; daily challenge state degrades gracefully with a visible non-blocking status.
- AC6: Daily challenge tracking and UI updates do not introduce noticeable lag/stutter on typical laptop browsers during normal play.

## Open Questions
- Should the rotation be fixed cyclic order or deterministic pseudo-random per day key?
- How many historical badges should be shown in UI (for example, last 7, 30, or all)?
- Should missed days be visible as gaps or simply absent badges?

## Approval Gate (Simulated)
Approved with no changes.
