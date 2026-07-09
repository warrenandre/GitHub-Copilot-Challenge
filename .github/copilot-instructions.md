# Copilot Instructions For This Repository

## Project Context

This repository contains browser-based mini apps and games.
Current focus areas include:
- `games/snake` (Snake Cash Rush)
- `home` (landing/home experience)

### Tech Stack

- Core frontend: HTML5, CSS3, and vanilla JavaScript
- Snake gameplay runtime: Python in-browser via PyScript/Pyodide
- Rendering: HTML5 Canvas for game visuals
- Persistence: Browser `localStorage` for best-score retention
- Tooling/runtime assumptions: static hosting friendly (no backend required)

### Architecture Decisions

- Keep gameplay domain logic in Python (`games/snake/src/main.py`) to preserve deterministic updates and clearer game-state modeling.
- Keep JavaScript as a thin browser bridge (`games/snake/src/app.js`) for browser APIs only (animation frame + persistence), not gameplay rules.
- Keep HTML/CSS responsible for shell, layout, and visual design; avoid coupling style concerns with gameplay logic.
- Favor fixed-step updates (`accumulator` + `tick_ms`) over frame-dependent movement so behavior remains consistent across machines.
- Prefer progressive enhancement: if optional browser capabilities fail, preserve baseline interactivity where possible.

### Preferred Libraries And Dependencies

- Prefer built-in browser APIs and standard Python features already in use.
- Preferred runtime dependency for Snake: PyScript (`https://pyscript.net/releases/2025.3.1/`).
- Preferred typography assets currently used by Snake UI: Google Fonts (`Space Grotesk`, `Sora`).
- Avoid introducing additional third-party libraries unless there is a clear, user-requested need and documented benefit.

When making changes, preserve the existing architecture:
- UI shell and styling in HTML/CSS
- Python game logic for Snake via PyScript
- Small JavaScript bridge only for browser-specific integration

## General Coding Guidelines

- Keep changes scoped to the user request.
- Do not refactor unrelated files.
- Prefer readability over cleverness.
- Preserve existing naming and file organization unless explicitly asked to change it.
- Add concise comments only where the "why" is non-obvious.
- Avoid introducing new dependencies unless necessary.

## Coding Standards

### Naming Conventions

- Python:
  - Use `snake_case` for functions, methods, variables, and module-level constants where appropriate.
  - Use `PascalCase` for classes (for example, `SnakeCashRush`, `Point`).
  - Use `UPPER_SNAKE_CASE` for true constants (for example, board and scoring constants).
  - Prefer descriptive names over abbreviations unless the abbreviation is widely understood (`ctx`, `id`, `url`).
- JavaScript:
  - Use `camelCase` for functions, methods, and variables.
  - Use `PascalCase` only for constructor/class names when classes are introduced.
  - Keep browser bridge names explicit and domain-specific (for example, `snakeCashRushBridge`).
- HTML/CSS:
  - Use kebab-case for CSS classes and ids when adding new selectors.
  - Keep class names semantic by role or component (for example, `score-tile`, `overlay-card`) rather than presentational names.

### Error Handling Patterns

- Validate external inputs early and return fast on invalid states.
- Prefer guard clauses over deeply nested branching.
- Never silently swallow errors when a user-visible fallback is possible.
- In browser-only flows:
  - Fail gracefully and preserve interactivity where possible.
  - Keep existing UI in a safe state if an operation cannot complete.
- In Python game logic:
  - Preserve deterministic updates even when handling exceptional states.
  - Keep collision/state transitions explicit and side effects localized.
- In JavaScript bridge code:
  - Treat local storage and browser API access as potentially unavailable.
  - Use safe defaults when reads fail or values are missing.

### Documentation Expectations

- Add or update docstrings when method behavior changes, especially in `games/snake/src/main.py`.
- Write docstrings and comments to explain intent and constraints, not obvious syntax.
- Add inline comments only for non-obvious "why" decisions (timing, collision edge cases, state transitions).
- Keep README documentation current when any of the following changes:
  - setup/run steps
  - controls or gameplay rules
  - architecture or file responsibilities
- Keep examples copy-paste ready for Windows PowerShell.
- Keep documentation concise, accurate, and implementation-aligned.

## Python (games/snake/src/main.py)

- Keep game behavior deterministic and frame-rate independent.
- Preserve fixed-step update logic (`accumulator` + `tick_ms`).
- Do not break input safeguards (for example, reverse-direction protection).
- Keep browser interop via `js` and `create_proxy` explicit and minimal.
- Add or update docstrings for public methods when behavior changes.

## JavaScript (games/snake/src/app.js)

- Keep bridge functions minimal and focused.
- Maintain compatibility with current local storage key usage.
- Avoid adding gameplay logic to JavaScript that belongs in Python.

## HTML/CSS

- Preserve accessibility attributes already present (labels, live regions).
- Keep responsive behavior intact for small screens.
- Reuse existing design tokens and style patterns before adding new ones.

## Documentation

- Update relevant README files when behavior, controls, setup, or architecture changes.
- Keep setup steps copy-paste friendly for Windows PowerShell.
- Prefer concise, practical sections over long prose.

## Validation Checklist

Before finalizing changes, Copilot should:
- Run a quick syntax/lint/error check for edited files when tools are available.
- Confirm no unrelated files were modified.
- Summarize what changed and why.

## Git And Commit Guidance

- Stage only files relevant to the task.
- Use clear commit messages with a short scope when possible.
  - Example: `docs(snake): clarify controls and setup`
  - Example: `feat(snake): tune collision handling`

## What To Avoid

- Do not rewrite large sections without a clear need.
- Do not introduce breaking behavior changes without documenting them.
- Do not remove debugging helpers unless explicitly requested.
