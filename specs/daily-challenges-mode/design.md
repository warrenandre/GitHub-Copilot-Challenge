# Phase 2 - Design

## Inputs
This design is based on approved intent in specs/daily-challenges-mode/intent.md.

## Proposed Architecture And Boundaries

### Python (game logic) - games/snake/src/main.py
Responsibilities:
- Define daily challenge domain model and evaluators.
- Track per-run progress signals needed by objective types:
  - Score
  - Elapsed survival time
  - Bills collected
- Emit compact challenge state snapshots for rendering/bridge consumption.

Non-responsibilities:
- Direct local storage I/O.
- DOM manipulation.

### JavaScript Bridge/UI - games/snake/src/app.js
Responsibilities:
- Persist/retrieve daily challenge records via existing browser bridge local storage abstraction.
- Compute active day key and challenge selection strategy.
- Hydrate game with active challenge definition at start/restart.
- Render current objective, progress, completion badge, and history.
- Handle graceful fallback when storage access fails.

### HTML/CSS - games/snake/src/index.html, games/snake/src/styles.css
Responsibilities:
- Add a compact Daily Challenge panel and badge strip.
- Keep responsive layout and avoid disrupting current controls.

## Components And Responsibilities

### 1) ChallengeCatalog (Python)
- Static list of challenge templates:
  - SCORE_100
  - SURVIVE_90S
  - COLLECT_15_BILLS
- Fields:
  - id
  - label
  - type
  - target

### 2) ChallengeProgressTracker (Python)
- Inputs each tick: score, elapsed_time_s, bills_collected.
- Computes progress percentage/value for active challenge.
- Detects completion transition once.
- Exposes read-only state snapshot:
  - challenge_id
  - progress_value
  - target_value
  - completed

### 3) DailyChallengeService (JavaScript)
- Determines local day key: YYYY-MM-DD.
- Selects challenge for day via deterministic function:
  - index = hash(dayKey) mod challengeCatalog.length
- Loads/saves badge map in local storage:
  - key: snakeCashRush.dailyChallenges.v1
  - shape:
    {
      completedByDate: {
        "2026-07-09": { challengeId: "SCORE_100", completedAt: 1720502400000 }
      }
    }
- Handles storage exceptions and returns availability state.

### 4) ChallengeUIController (JavaScript)
- Renders:
  - Today objective text.
  - Progress text/bar.
  - Completion badge state.
  - Historical badge list (initially last 7 completed days).
- Non-blocking storage warning when unavailable.

## Data Flow
1. On app initialization, JS computes dayKey and selects active challenge.
2. JS passes active challenge definition into Python game state initialization.
3. During game loop, Python updates challenge progress from gameplay signals.
4. Python exposes progress/completion snapshot to JS each render/update bridge cycle.
5. JS updates UI panel from snapshot.
6. On first completion for active day, JS persists badge record to local storage.
7. On reload, JS restores historical badges and current-day completion state.

## API / Interface Contracts

### Python-side challenge snapshot (conceptual)
- get_daily_challenge_state() -> dict
  - challenge_id: str
  - label: str
  - progress_value: int | float
  - target_value: int | float
  - completed: bool

### JS service methods (conceptual)
- getDayKey(date: Date): string
- getChallengeForDay(dayKey: string): ChallengeDefinition
- loadBadgeStore(): BadgeStore | null
- saveBadgeCompletion(dayKey: string, challengeId: string): void
- getRecentBadges(limit: number): BadgeEntry[]

## Key Design Decisions And Rationale
- Deterministic day-based challenge selection avoids backend dependencies and keeps behavior stable per day.
- Local storage persistence meets browser-only constraint with minimal complexity.
- Keep challenge evaluation in Python to preserve game-logic ownership and avoid duplicated rule logic.
- Keep persistence and UI in JS to preserve browser/platform separation.
- One-completion-per-day rule prevents badge duplication and simplifies UX.

## Error Handling
- If local storage read/write fails:
  - Set storageAvailable=false.
  - Continue gameplay and progress updates.
  - Show non-blocking status in challenge panel.
  - Skip persistence but still allow in-session completion feedback.
- If stored data is malformed:
  - Reset to safe empty structure.
  - Log warning to console.

## Observability Notes
- Add lightweight debug logs (guarded/minimal) for:
  - day key selection
  - storage load/save failures
  - challenge completion events
- No telemetry backend is introduced.

## Security Notes
- Treat local storage as untrusted input; validate schema before use.
- Avoid executing or interpolating untrusted strings as HTML.

## Performance Notes
- Recompute challenge completion only on existing tick/update boundaries.
- Update DOM only when displayed challenge state changes.
- Keep badge history rendering bounded (default limit 7) to avoid layout thrash.

## Alternatives Considered
- Fixed weekly schedule table:
  - Pros: Predictable and simple.
  - Cons: Less variety and easier to optimize away by players.
- Pure random selection each load:
  - Pros: Very simple.
  - Cons: Violates one-objective-per-day consistency.
- Store progress continuously in local storage:
  - Pros: Resume partial progress across reloads.
  - Cons: More writes/complexity; unnecessary for current scope.

## Open Questions
- Confirm whether challenge rotation should avoid repeating same type on consecutive days.
- Confirm desired badge history limit in UI.

## Approval Gate (Simulated)
Approved with no changes.
