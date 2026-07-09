# GitHub Copilot Instructions

## Project Overview
- This repository contains static web pages and a browser game.
- Main areas:
  - `home/` for the landing page UI.
  - `games/snake/src/` for Snake Cash Rush (`index.html`, `styles.css`, `app.js`, optional `main.py`).

## Project Context
### Tech Stack
- Frontend: plain HTML5, CSS3, and vanilla JavaScript (no build step).
- Rendering and interaction: browser-native DOM APIs and keyboard event handling.
- Game implementation: client-side JavaScript in `games/snake/src/app.js`.
- Optional local helper script: Python in `games/snake/src/main.py` for simple local workflows.

### Architecture Decisions
- Keep the project lightweight and static-first: no framework required for core pages or gameplay.
- Favor simple, file-based separation:
  - structure in HTML,
  - presentation in CSS,
  - behavior and game state in JavaScript.
- Prioritize deterministic gameplay logic over visual complexity.
- Keep runtime dependencies in the browser minimal to preserve fast load and easy local hosting.
- Prefer incremental enhancements over broad rewrites to maintain stability.

### Preferred Libraries
- Default preference: no additional libraries for standard UI and gameplay work.
- Prefer browser-native APIs first (`querySelector`, `addEventListener`, `requestAnimationFrame`, Canvas/DOM where already used).
- If a library is proposed, it should be:
  - small,
  - well-maintained,
  - justified by clear complexity reduction,
  - explicitly requested or approved.
- Avoid introducing frameworks or heavy utility libraries for small feature updates.

### Dependency Decision Matrix (Approve/Reject)
- Rule: dependency is **APPROVE** only if all checks below are **YES**; otherwise **REJECT**.

| Check | YES = Approve Condition | NO = Reject Condition |
|---|---|---|
| 1. User approval | User explicitly requested or approved adding a dependency. | No explicit user approval. |
| 2. Native alternative | Browser-native APIs cannot solve it cleanly with reasonable complexity. | Native APIs are sufficient. |
| 3. Scope fit | Package is small and directly solves the requested feature. | Package is broad/heavy for the task size. |
| 4. Maintenance quality | Actively maintained and commonly trusted. | Poor maintenance or unclear trust/safety. |
| 5. Change impact | Adds minimal build/runtime complexity and no architecture drift. | Introduces build tooling, framework lock-in, or large refactor pressure. |

- Binary output format for Copilot proposals:
  - `Decision: APPROVE` or `Decision: REJECT`
  - `Reason: <single sentence mapped to first failed check or all checks passed>`

## General Coding Guidelines
- Keep changes focused and minimal to the requested task.
- Preserve existing file structure and naming conventions.
- Prefer readable, maintainable JavaScript and CSS over clever one-liners.
- Do not add new dependencies unless explicitly requested.

## Enforcement Checklist (Must/Should)
### Must
- Follow naming conventions (`camelCase`, `PascalCase`, `UPPER_SNAKE_CASE`, `kebab-case`) for all new code.
- Handle failures explicitly in async and risky logic (`try/catch` or `.catch`).
- Never leave empty `catch` blocks or silent failures.
- Add concise intent-level documentation for non-trivial logic and functions.
- Keep edits scoped to the requested task and avoid unrelated refactors.

### Should
- Use guard clauses to keep control flow simple.
- Provide user-safe UI feedback when an error affects gameplay or interaction.
- Update README content when controls, setup, or behavior changes.
- Prefer short, high-signal comments over verbose inline explanations.
- Validate UI and gameplay behavior quickly after meaningful changes.

## Naming Conventions
- JavaScript variables and functions: `camelCase` (example: `updateScoreDisplay`).
- JavaScript constants: `UPPER_SNAKE_CASE` for fixed values (example: `MAX_SPEED`).
- Constructor functions or classes: `PascalCase` (example: `SnakeGame`).
- CSS classes: `kebab-case` and component-oriented names (example: `score-panel`, `game-canvas`).
- File names:
  - HTML/CSS/JS files in `kebab-case` where new files are needed.
  - Keep existing file names unchanged unless explicitly requested.

## Error Handling Patterns
- Validate external or user-driven input early and return gracefully on invalid states.
- Prefer guard clauses to reduce deeply nested conditionals.
- Wrap risky operations in `try/catch` only when recovery or user feedback is possible.
- In `catch` blocks:
  - log useful debugging context with `console.error`,
  - show a user-safe message in UI when relevant,
  - avoid swallowing errors silently.
- Never use empty `catch` blocks.
- For async logic, always handle rejected promises (`try/catch` with `await` or `.catch`).

## Documentation Expectations
- Keep comments concise and explain intent, not obvious syntax.
- Add comments only for non-obvious logic, edge cases, or gameplay rules.
- For each non-trivial function, include a short header comment that states:
  - purpose,
  - key inputs,
  - side effects (DOM updates, state mutations, timers).
- Update README sections when behavior, controls, or setup steps change.
- When introducing a new config value or constant, document its meaning near the declaration.

## HTML/CSS/JS Conventions
- Use semantic HTML where possible.
- Keep CSS organized by section with short, meaningful comments only when needed.
- Use descriptive variable and function names in JavaScript.
- Avoid inline scripts and inline styles unless there is a clear reason.

## Gameplay and UI Changes
- Preserve core Snake gameplay behavior unless the task explicitly asks to change mechanics.
- Keep keyboard controls responsive and predictable.
- Ensure score/cash display updates correctly and remains visible on common screen sizes.

## Testing and Validation
- For UI updates, verify behavior in a browser at desktop and mobile widths.
- For gameplay changes, validate:
  - movement and collision rules,
  - score progression,
  - game-over and restart behavior.

## File Editing Rules
- Modify only files relevant to the request.
- Do not rewrite unrelated code.
- Keep formatting consistent with surrounding code.
- Add brief comments only for non-obvious logic.
