# GitHub Copilot Instructions for This Repository

Follow these standards when generating or modifying code in this project.

## Scope and Project Layout

- Keep changes scoped to the challenge project structure.
- Primary game code lives in `games/snake/src/`.
- Challenge website code lives in `home/`.
- Do not move files between `games/snake/` and `home/` unless explicitly requested.

## Architecture Patterns

- Keep game logic and state transitions in Python (`games/snake/src/main.py`).
- Keep browser/platform integration in JavaScript (`games/snake/src/app.js`).
- Keep structure in HTML and visual concerns in CSS.
- Preserve the bridge pattern exposed as `window.snakeCashRushBridge` for browser APIs (RAF and local storage).
- Prefer small, focused methods over large monolithic functions.

## Python Conventions (Snake Game)

- Use Python 3.10+ compatible syntax.
- Follow PEP 8 naming:
- `snake_case` for functions/methods/variables.
- `UPPER_SNAKE_CASE` for module-level constants.
- `PascalCase` for classes and dataclasses.
- Keep and extend type hints for new or changed functions.
- Add or preserve docstrings for public methods and helper functions.
- Keep game update flow explicit: input -> simulation step -> collision/score updates -> render.
- Prefer immutable coordinate objects (`Point`) and avoid ad-hoc dicts for positions unless serialization is required.

## JavaScript Conventions

- Use modern vanilla JavaScript (no framework unless explicitly requested).
- Use `camelCase` for identifiers and `PascalCase` only for constructor-like symbols.
- Prefer `const` by default and `let` only when reassignment is required.
- Keep DOM/query logic minimal and readable.
- Avoid adding third-party dependencies for simple browser behavior.

## HTML/CSS Conventions

- Keep semantic HTML and meaningful IDs/classes used by Python/JS bindings.
- Preserve responsive behavior and avoid fixed layouts that break mobile.
- Reuse existing design language and CSS variable/style patterns where present.
- Avoid inline styles unless there is a strong reason.

## Reliability and Error Handling

- Add defensive checks for user input and browser interactions where failures are possible.
- Fail gracefully with clear status text instead of silent errors.
- Do not swallow exceptions without a reason.

## Testing and Validation Expectations

- For gameplay logic changes, prefer deterministic, testable helper methods.
- Cover edge cases such as wall collisions, self-collisions, score updates, and restart behavior.
- Keep manual test steps easy to run via `python -m http.server 8000` from `games/snake/`.

## Documentation and Comments

- Keep README content and in-code comments aligned with behavior changes.
- Write concise comments that explain intent, not obvious syntax.
- Do not add noisy or redundant comments.

## Change Discipline

- Make minimal, targeted edits.
- Preserve public names and interfaces unless a change is explicitly requested.
- Do not perform broad refactors, formatting-only rewrites, or dependency upgrades unless requested.
