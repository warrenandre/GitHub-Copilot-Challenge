# Copilot Instructions For This Repository

## Goal
Help contributors complete the GitHub Copilot Challenge by making focused, high-quality improvements to the Snake Cash Rush project.

## Primary Target
Most work should happen in games/snake.

## Project Context

### Tech Stack
- Frontend shell: HTML5 and CSS3.
- Game runtime: Python executed in-browser through PyScript.
- Browser interop: Pyodide FFI via pyodide.ffi.create_proxy and js module bindings.
- Canvas rendering: 2D context on a single HTML canvas element.
- Minimal JavaScript bridge: requestAnimationFrame scheduling and localStorage access.

### Architecture Decisions
- Keep core game rules in Python so challenge tasks can focus on Python quality improvements.
- Use a thin JavaScript bridge only for browser-native concerns (animation timing and persistence).
- Prefer a single game controller class for state transitions, input, simulation ticks, and rendering.
- Use fixed-timestep simulation with an accumulator to keep movement deterministic across frame-rate variance.
- Keep visual presentation in CSS and markup, while logic remains isolated in Python.
- Store best score client-side for zero-backend operation and easy local testing.

### Preferred Libraries
- Python standard library first (dataclasses, typing, json, random).
- PyScript runtime for browser execution.
- pyodide.ffi.create_proxy for safe event and callback bridging.
- Browser APIs through js bindings only where necessary.
- For tests, prefer pytest-style structure and deterministic test data.

### Library Selection Rules
- Do not add new dependencies when the standard library is sufficient.
- If a new dependency is necessary, keep it small, well-maintained, and justified in PR notes.
- Avoid framework-heavy rewrites that conflict with the lightweight challenge setup.

## Challenge Priorities
1. Documentation quality
2. Testing coverage and edge cases
3. CI and automation readiness
4. Exception handling and graceful fallback behavior

## General Coding Guidelines
- Preserve existing behavior unless the task explicitly requests a change.
- Prefer small, reviewable commits.
- Avoid broad refactors that are unrelated to the current challenge.
- Keep naming clear and consistent with the existing code style.
- Add comments only where logic is non-obvious.

## Coding Standards

### Naming Conventions
- Use snake_case for Python variables, functions, and module-level helpers.
- Use PascalCase for Python classes.
- Use UPPER_SNAKE_CASE for module-level constants.
- Use descriptive names that reflect intent, not implementation detail.
- Avoid ambiguous abbreviations unless they are domain-standard (for example: ctx, DOM, HUD).
- Prefer boolean names that read clearly in conditions (for example: is_running, has_collision, can_restart).

### Error Handling Patterns
- Validate external assumptions at boundaries (DOM lookup, browser bridge availability, runtime APIs).
- Fail early for invalid state and return immediately when recovery is not possible.
- Use guard clauses to keep control flow shallow and readable.
- Do not silently swallow exceptions unless there is an explicit fallback path.
- When fallback behavior is used, keep the game in a safe and predictable state.
- Surface actionable failure context for developers (clear messages and state hints).
- Keep user-facing messaging concise and non-technical.

### Documentation Expectations
- Add module/class/function docstrings for all non-trivial Python logic.
- Start docstrings with an imperative one-line summary.
- Document parameters, return values, and side effects when they are not obvious.
- Use inline comments sparingly and only to explain why a decision exists.
- Keep comments synchronized with code changes; update or remove stale comments immediately.
- Update project README content whenever setup, behavior, or architecture changes.

## Python Guidelines For games/snake/src/main.py
- Add clear docstrings for classes, methods, and helper functions.
- Use concise inline comments that explain why, not what.
- Keep game loop timing deterministic and easy to reason about.
- Protect against regressions in movement, collision, and scoring logic.
- Favor readable control flow over clever one-liners.

## Testing Guidelines
- Add tests for game rules and edge cases first.
- Prefer deterministic tests over random-dependent tests.
- Cover at least:
  - wall collision
  - self collision
  - scoring increments
  - speed progression bounds
  - restart and game-over transitions

## CI Expectations
- Ensure tests can run non-interactively.
- Keep commands simple and portable.
- Fail fast on lint or test errors.

## Error Handling Expectations
- Validate assumptions around DOM access and browser bridge calls.
- Provide safe fallback behavior when runtime dependencies are unavailable.
- Surface actionable errors in a user-friendly way.

## Pull Request Readiness Checklist
- Changes match the active challenge scope.
- Documentation is updated when behavior changes.
- Tests cover new or modified logic.
- No unrelated files are changed.
- Local run instructions remain accurate.
