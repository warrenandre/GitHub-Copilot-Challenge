# Copilot Instructions

## Scope
- Apply these instructions to the entire repository.
- Prioritize minimal, focused changes that match existing code style.

## Project Context
- This repository includes a browser-based Snake game at `games/snake/src/`.
- Core gameplay logic is in Python (`main.py`) and runs in-browser via PyScript.
- UI shell and browser bridge are in `index.html`, `styles.css`, and `app.js`.

## Tech Stack and Architecture
- Frontend: vanilla HTML/CSS/JavaScript.
- Runtime: PyScript + Pyodide to execute Python in the browser.
- Rendering: HTML5 canvas for game drawing and animation.
- Persistence: browser `localStorage` (via `app.js` bridge) for best-score storage.
- Build/Deployment: static files only; serve over a local/static HTTP server.

### Architecture Decisions
- Keep gameplay rules and state transitions in Python (`main.py`).
- Keep browser integration minimal in JavaScript (`app.js`) for animation frame + storage helpers.
- Keep `index.html` as the shell/HUD and `styles.css` for presentation only.
- Favor clear boundaries: game logic in Python, browser APIs in JS bridge, UI in HTML/CSS.

### Preferred Libraries
- Python standard library only unless explicitly required.
- Use PyScript/Pyodide APIs already present in the project.
- Avoid adding frameworks or dependencies for simple UI/gameplay changes.

## Coding Guidelines
- Keep changes small and task-specific.
- Preserve existing naming, structure, and formatting conventions.
- Do not refactor unrelated code.
- Avoid introducing new dependencies unless clearly required.
- Use clear docstrings for Python methods when adding/modifying behavior.
- Add inline comments only for non-obvious logic, focusing on the reason ("why").

## Coding Standards

### Naming Conventions
- Python variables/functions/methods: `snake_case`.
- Python classes/dataclasses: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE`.
- JavaScript functions/variables: `camelCase`.
- DOM IDs and CSS classes: descriptive, consistent with existing style.

### Error Handling Patterns
- Validate preconditions early and return fast for invalid states.
- Prefer explicit guards over broad exception handling.
- Catch exceptions only when a meaningful fallback/recovery exists.
- Keep user-facing messages concise and actionable.
- Never silence exceptions without reason; if handling is required, keep behavior deterministic.

### Documentation Expectations
- Every modified/added Python method should include a docstring describing:
  - purpose/behavior,
  - parameters,
  - return value.
- Add inline comments only for non-obvious logic and explain *why* the logic exists.
- Update related README sections when user-visible behavior, setup, or controls change.
- Keep examples and command snippets accurate for Windows PowerShell.

## Documentation
- When behavior changes, update relevant README sections.
- Keep instructions accurate for Windows PowerShell commands where applicable.

## Testing & Validation
- Run the smallest relevant checks first.
- For Snake game changes, verify game startup and controls manually via local server:
  - `python -m http.server 8000`
  - Open `http://localhost:8000/games/snake/src/` (or `http://localhost:8000/src/` when run inside `games/snake`).
- Do not fix unrelated failing tests or issues.

### Copilot Output Verification
- When requesting generated code, verify it against this checklist before accepting:
  - Naming follows conventions in this file.
  - Error handling uses guards and avoids unnecessary broad `except` blocks.
  - Method docstrings include behavior, parameters, and return values.
  - Inline comments explain non-obvious *why* decisions only.
  - Changes remain minimal and aligned to existing architecture boundaries.

## Safety and Quality
- Do not commit secrets, tokens, or credentials.
- Prefer root-cause fixes over temporary patches.
- Keep user-facing text concise and consistent with the game tone.
