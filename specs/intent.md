# Intent Spec

## User Goal
Add a Daily Challenge mode to Snake Cash Rush that gives players a single, deterministic challenge per day, highlights that challenge in the HUD, stores best daily score locally, and leaves Normal mode behavior unchanged.

## Constraints
- Technical: Use the existing vanilla HTML, CSS, and JavaScript stack.
- Technical: No external services, remote APIs, or backend persistence.
- Technical: Keep startup and gameplay performance fast on low and mid-range mobile devices.
- Technical: Avoid heavy dependencies; prefer existing project patterns and browser-native APIs.
- UX: Daily Challenge must be clearly distinguishable from Normal mode via a visible HUD badge.
- UX: UI must remain mobile-friendly and readable at common phone widths.
- Product: One seeded challenge per local calendar day.
- Product: Board modifiers are fixed for that day and do not change during play sessions.
- Product: Best Daily score must persist locally per day.
- Product: Normal mode must remain unchanged in controls, scoring behavior, and game loop.
- Quality: Feature must be manually testable without special tooling.

## Assumptions
- “Per day” means the device local date, not UTC.
- Challenge determinism is scoped to a single device/browser environment.
- “Best daily score locally” is stored in browser local storage with date-based keys.
- Daily Challenge and Normal mode share the same core movement rules unless an explicit daily modifier changes board conditions only.

## Acceptance Criteria
- A Daily Challenge mode is selectable from the existing game entry flow.
- For the same local date, restarting the app yields the same daily seed and same board modifier set.
- When local date changes, a new daily seed and modifier set is used automatically.
- A visible Daily Challenge badge appears in the HUD only when Daily Challenge mode is active.
- Badge content clearly indicates challenge context, including the active day identity.
- Best Daily score is saved locally and shown in Daily Challenge context.
- Best Daily score is tracked per day and does not overwrite other days.
- If no prior Daily score exists for the day, the first completed score initializes that day’s best.
- Normal mode behavior and Normal-mode score tracking remain unchanged from current behavior.
- Feature works without network connectivity.
- UI remains usable on mobile layouts without overlap, clipping, or hidden critical HUD content.
- Manual verification steps can confirm determinism, score persistence, badge visibility, and mode isolation.
