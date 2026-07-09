# Phase 1 — Intent

> **Feature request (test prompt sent to Spec-Driven-Dev agent):**
> "Add a pause feature to Snake Cash Rush so the player can press P to pause and
> resume the game at any time during an active run."

---

## 1.1 Feature Summary

Allow the player to pause and resume an active Snake Cash Rush run by pressing the
**P** key (or clicking a dedicated Pause button). While paused, the game loop
stops, the canvas retains the last rendered frame, and an overlay communicates
the paused state. Pressing P again (or clicking Resume) returns the run to the
exact state it was in when paused, with no loss of score, speed, or snake position.

---

## 1.2 User Goal

**Player goal:** Take a break mid-run without losing their current score and
progress. The player needs a reliable way to interrupt gameplay for any reason
(distraction, phone call, etc.) and pick up exactly where they left off.

**Developer goal:** A lightweight, low-risk addition that integrates cleanly into
the existing game loop without altering core physics, scoring, or rendering logic.

---

## 1.3 Constraints

- **Runtime:** Python logic runs in the browser via PyScript + Pyodide; no
  server-side changes are permitted.
- **Architecture boundary:** Pause state must be owned by Python (`main.py`).
  The JavaScript bridge (`app.js`) must not gain new game-state awareness.
- **Dependencies:** Python standard library only; no new JS libraries.
- **Naming:** New Python identifiers must follow `snake_case`; new constants
  `UPPER_SNAKE_CASE`; any new DOM IDs must be descriptive and consistent with
  the existing style (e.g. `pauseButton`).
- **Scope:** Pausing is only valid during an active run (`self.running is True`).
  Pressing P on the start screen or game-over overlay has no effect.
- **Persistence:** Pause state is session-only; it must not be written to
  `localStorage`.

---

## 1.4 Acceptance Criteria

1. **Given** the game is in an active run, **when** the player presses **P**,
   **then** the animation loop stops, the canvas frame is preserved, and a
   "Paused" overlay appears within one render cycle.

2. **Given** the game is paused, **when** the player presses **P** again,
   **then** the animation loop resumes, the overlay is hidden, and gameplay
   continues from the exact frame it was paused at (no position, score, or speed
   change).

3. **Given** the game is paused, **when** the player presses any movement key
   (Arrow / WASD), **then** the key input is ignored (the snake does not change
   direction while paused).

4. **Given** the game is on the start screen or game-over overlay,
   **when** the player presses **P**,
   **then** no visible state change occurs.

5. **Given** the game is in an active run, **when** the player clicks the
   Pause button in the HUD,
   **then** the same pause behaviour described in AC-1 occurs.

6. **Given** the game is paused, **when** the player clicks the Resume button,
   **then** the same resume behaviour described in AC-2 occurs.

7. **Given** the game is paused, **when** the player presses **R** to restart,
   **then** the game exits pause state and starts a fresh run (existing restart
   behaviour is unaffected).

---

## 1.5 Out of Scope

- Saving or restoring pause state across page reloads.
- Pause timeout (auto-resume after N seconds).
- Multiplayer or network considerations.
- Pause animations or transition effects beyond showing/hiding the overlay.
- Mobile touch input for pause/resume.
