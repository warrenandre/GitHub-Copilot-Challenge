# Phase 2 — Design

> Derived from: [`specs/intent.md`](./intent.md)

---

## 2.1 Architecture Overview

Pause state is a game-logic concern, so it lives entirely in `main.py` as a new
boolean attribute `self.paused`. The existing animation loop in `game_frame`
already guards on `self.running`; a second guard on `self.paused` is all that is
needed to freeze the loop without dismantling it.

The HTML layer (`index.html`) gains one new **Pause / Resume** button in the HUD
panel, alongside the existing **Restart Run** button. The CSS layer (`styles.css`)
adds minimal styling for the button's toggled state using an existing pattern
(`.action-button`). The JS bridge (`app.js`) requires **no changes** — animation
frame scheduling is unchanged because `game_frame` simply re-requests a frame
while paused (rendering the frozen canvas) but skips the `advance()` call.

---

## 2.2 Component Breakdown

| Component | File | Change Type | Responsibility |
|-----------|------|-------------|----------------|
| `SnakeCashRush.__init__` | `main.py` | Modify | Wire up pause button DOM reference and click proxy; initialise `self.paused = False` |
| `SnakeCashRush.reset_state` | `main.py` | Modify | Reset `self.paused` to `False` on every new run |
| `SnakeCashRush.toggle_pause` | `main.py` | **New** | Toggle `self.paused`; update overlay and button label |
| `SnakeCashRush.handle_keydown` | `main.py` | Modify | Handle `p` key → call `toggle_pause`; guard movement keys when paused |
| `SnakeCashRush.game_frame` | `main.py` | Modify | Skip `advance()` when paused; still re-queue next frame so resume is instant |
| `SnakeCashRush.start_game` | `main.py` | Modify | Ensure `self.paused = False` when a new run starts |
| Pause / Resume button | `index.html` | Modify | Add `<button id="pauseButton">` to the HUD panel |
| Pause overlay content | `index.html` | Modify | Add paused-state text constants to the existing overlay structure via Python |
| Button active state | `styles.css` | Modify | Add `.action-button[aria-pressed="true"]` style for visual pressed feedback |

---

## 2.3 Data Flow

1. **Player presses P** → browser fires `keydown` event.
2. `handle_keydown` receives the event; detects `key == "p"`.
3. Guard: if `not self.running`, return immediately (no effect outside a run).
4. `toggle_pause()` is called.
5. `self.paused` is flipped (`True` ↔ `False`).
6. If now **paused**:
   - `set_overlay(kicker="Paused", title="Game Paused", message="Press P or click Resume to continue.", button_text="Resume", visible=True)`
   - `pause_button.textContent` → `"Resume"`; `pause_button.setAttribute("aria-pressed", "true")`
7. If now **resumed**:
   - `set_overlay(visible=False)`
   - `pause_button.textContent` → `"Pause"`; `pause_button.setAttribute("aria-pressed", "false")`
   - `self.last_frame_time = 0.0` — reset frame timestamp so the accumulator
     doesn't spike from the paused gap and teleport the snake.
8. `game_frame` continues to be called every rAF tick regardless of pause state.
   While paused, it **draws** (to keep canvas live) but **does not call `advance()`**.
9. No changes propagate to `app.js` or `localStorage`.

---

## 2.4 Key Algorithms or Logic

### toggle_pause

```python
def toggle_pause(self) -> None:
    # Only valid during an active run
    if not self.running:
        return

    self.paused = not self.paused

    if self.paused:
        self.set_overlay(
            kicker="Paused",
            title="Game Paused",
            message="Press P or click Resume to continue.",
            button_text="Resume",
            visible=True,
        )
        self.pause_button.setAttribute("aria-pressed", "true")
        self.pause_button.textContent = "Resume"
    else:
        self.set_overlay(visible=False)
        self.pause_button.setAttribute("aria-pressed", "false")
        self.pause_button.textContent = "Pause"
        # Reset frame timestamp to prevent a large delta spike after a long pause.
        # Without this, the accumulator would fire many advance() ticks at once.
        self.last_frame_time = 0.0
```

### game_frame modification (delta section only)

```python
# Skip game logic while paused; keep the rAF loop alive for instant resume
if self.paused:
    self.draw()
    self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)
    return

# ... existing accumulator and advance() logic unchanged ...
```

### handle_keydown modification

```python
if key == "p":
    self.toggle_pause()
    return

# Guard: swallow directional input while paused to prevent queued direction change
if self.paused:
    return
```

---

## 2.5 Edge Cases & Error Handling

| Edge Case | Guard / Fallback |
|-----------|-----------------|
| Player presses P on start screen | `toggle_pause` returns early if `not self.running` |
| Player presses P on game-over overlay | Same guard as above — `self.running` is `False` |
| Player presses R while paused | `restart_game` calls `reset_state` which sets `self.paused = False`; run proceeds normally |
| Player rapidly toggles P | Each toggle is synchronous; no race condition possible in single-threaded Python/Pyodide |
| Pause button clicked before game starts | `toggle_pause` guard returns immediately; button state unchanged |
| `last_frame_time` reset on resume | Prevents accumulator spike; handled in `toggle_pause` before `game_frame` sees it |

---

## 2.6 Design Assumptions

1. The existing `set_overlay` + overlay card pattern is sufficient for the pause
   UI — no new overlay element is needed.
2. The Pause button sits inside the existing `.hud-panel` alongside the Restart
   button; no layout changes to `.board-panel` are needed.
3. `aria-pressed` is the correct ARIA pattern for a toggle button; no additional
   accessibility work is in scope.
4. Pausing mid-burst animation (cash burst, pulse) is acceptable — CSS animations
   run independently of the Python game loop and will complete naturally.
