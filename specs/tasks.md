# Tasks

> Feature: Pause / Resume for Snake Cash Rush
> Derived from: [`specs/intent.md`](./intent.md) · [`specs/design.md`](./design.md)

---

## Task List

| # | Task | File(s) | Effort | Depends on |
|---|------|---------|--------|------------|
| 1 | Add `id="pauseButton"` button to HUD panel | `index.html` | XS | — |
| 2 | Add `.action-button[aria-pressed="true"]` CSS style for toggle feedback | `styles.css` | XS | 1 |
| 3 | Add `self.paused = False` to `reset_state` | `main.py` | XS | — |
| 4 | Wire `pause_button` DOM reference and click proxy in `__init__` | `main.py` | XS | 1 |
| 5 | Implement `toggle_pause` method with overlay and button label updates | `main.py` | S | 3, 4 |
| 6 | Add `p` key handler and pause guard in `handle_keydown` | `main.py` | XS | 5 |
| 7 | Add pause guard in `game_frame` — skip `advance()`, keep rAF alive | `main.py` | XS | 5 |
| 8 | Reset `self.paused = False` in `start_game` | `main.py` | XS | 3 |
| 9 | Manual browser test: verify all 7 acceptance criteria from `intent.md` | browser | S | 1–8 |
| 10 | Update `games/snake/README.md` controls table to document the P key | `README.md` | XS | 9 |

Effort scale: **XS** < 30 min · **S** < 2 h · **M** < 1 day · **L** > 1 day

---

## Verification Checklist

Run these checks manually in the browser (`http://localhost:8000/src/`) after
completing all tasks:

- [ ] **AC-1** Press P during an active run → animation stops, "Game Paused" overlay appears, canvas frame is frozen.
- [ ] **AC-2** Press P again while paused → overlay disappears, run resumes with no change to score, snake position, or speed.
- [ ] **AC-3** Press an arrow key or WASD while paused → snake direction does not change (verify after resuming).
- [ ] **AC-4** Press P on the start screen → no visible state change.
- [ ] **AC-4b** Press P on the game-over overlay → no visible state change.
- [ ] **AC-5** Click Pause button during an active run → same result as AC-1.
- [ ] **AC-6** Click Resume button while paused → same result as AC-2.
- [ ] **AC-7** Press R while paused → pause state clears, a fresh run starts.
- [ ] Pause button label toggles correctly: **"Pause"** ↔ **"Resume"**.
- [ ] `aria-pressed` attribute updates correctly on Pause button.
- [ ] No console errors during pause/resume cycle.
- [ ] A very long pause (> 30 s) then resume does not cause the snake to jump or teleport.

---

## Open Questions

1. **Button placement:** Should the Pause button be a separate always-visible
   button, or share the Start/Restart button? Design assumes separate — confirm
   with stakeholder before task 1.

2. **Mobile support:** Scope excludes touch input. If mobile users are expected,
   a follow-up task for a touch-friendly pause control should be raised.

3. **Key conflict:** Does any hosting environment (e.g. the challenge website
   iframe) intercept the P key? If so, consider Escape as a fallback.
