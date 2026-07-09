# Phase 3 — Tasks & Summary

> Derived from: [`specs/intent.md`](./intent.md) · [`specs/design.md`](./design.md)

---

## 3.1 Executive Summary

This feature adds a **pause/resume capability** to Snake Cash Rush, allowing
players to freeze an active run with the **P** key or a HUD button and continue
exactly where they left off. The change is low-risk and architecturally clean:
pause state is owned entirely by Python (`main.py`), the animation loop is
preserved while paused (enabling instant resume), and the existing overlay system
is reused for the paused UI — so no new components, dependencies, or browser APIs
are introduced. The only notable implementation detail is resetting
`last_frame_time` on resume to prevent the fixed-timestep accumulator from spiking
after a long pause. Total estimated effort is **S–M** (2–4 hours).

---

## 3.2 Task List

| # | Task | File(s) | Effort | Depends on |
|---|------|---------|--------|------------|
| 1 | Add `id="pauseButton"` button to HUD panel | `index.html` | XS | — |
| 2 | Add `.action-button[aria-pressed="true"]` CSS style | `styles.css` | XS | 1 |
| 3 | Add `self.paused = False` to `reset_state` | `main.py` | XS | — |
| 4 | Wire `pause_button` DOM ref and click proxy in `__init__` | `main.py` | XS | 1 |
| 5 | Implement `toggle_pause` method | `main.py` | S | 3, 4 |
| 6 | Add `p` key handler and pause guard in `handle_keydown` | `main.py` | XS | 5 |
| 7 | Add pause guard in `game_frame` (skip `advance`, keep rAF) | `main.py` | XS | 5 |
| 8 | Reset `self.paused` in `start_game` | `main.py` | XS | 3 |
| 9 | Manual test: verify all 7 acceptance criteria | browser | S | 1–8 |
| 10 | Update `games/snake/README.md` controls table with P key | `README.md` | XS | 9 |

---

## 3.3 Verification Checklist

Run these checks manually in the browser (`http://localhost:8000/src/`) after
completing all tasks:

- [ ] **AC-1** Press P during an active run → animation stops, "Game Paused" overlay appears, canvas frame is frozen.
- [ ] **AC-2** Press P again while paused → overlay disappears, run resumes with no change to score, snake position, or speed.
- [ ] **AC-3** Press an arrow key or WASD while paused → snake direction does not change (verify after resuming).
- [ ] **AC-4** Press P on the start screen → no visual change.
- [ ] **AC-4b** Press P on the game-over overlay → no visual change.
- [ ] **AC-5** Click Pause button during an active run → same result as AC-1.
- [ ] **AC-6** Click Resume button while paused → same result as AC-2.
- [ ] **AC-7** Press R while paused → pause state clears, a fresh run starts.
- [ ] Pause button label toggles correctly: **"Pause"** ↔ **"Resume"**.
- [ ] `aria-pressed` attribute updates correctly on Pause button.
- [ ] No console errors during pause/resume cycle.
- [ ] A very long pause (> 30 s) then resume does not cause the snake to jump or teleport.

---

## 3.4 Open Questions

1. **Button placement:** Should the Pause button replace the existing Start/Restart
   button label, or should it be a separate, always-visible button? The design
   assumes separate — confirm with stakeholder.

2. **Mobile support:** The current scope excludes touch input. If mobile users are
   expected, a follow-up task for a touch-friendly pause control should be scoped.

3. **Keyboard shortcut conflict:** Does any hosting environment (e.g. the challenge
   website iframe) intercept the P key? If so, an alternative key (e.g. Escape)
   should be considered as a fallback.
