# Tasks — Power-Up System

> Builds on: [`intent.md`](./intent.md) · [`design.md`](./design.md)

## Implementation Order

Tasks are ordered by dependency — complete each before starting the next.

---

### Task 1 — Add `PowerUpKind`, `PowerUp`, and `POWER_UP_CONFIG`

**Deliverable:** Three new module-level definitions exist in `main.py` and the file parses without
errors. No runtime behaviour changes yet.

**Files:** `games/snake/src/main.py`

**Acceptance criteria met:** AC 5 (colour/symbol config), AC 10 (data-driven extensibility)

**Steps:**

1. Add `from enum import Enum` to the imports block.
2. Define `PowerUpKind(Enum)` with variants `SPEED_BOOST`, `INVINCIBILITY`, `DOUBLE_POINTS`.
3. Define `PowerUp` as a `@dataclass(frozen=True)` with fields `kind: PowerUpKind` and
   `position: Point`.
4. Define `POWER_UP_SPAWN_INTERVAL: int = 3` and `POWER_UP_BOARD_LIFE: int = 100` constants.
5. Define `POWER_UP_CONFIG: dict[PowerUpKind, dict]` with `duration_ticks`, `color`, `symbol`,
   and `label` entries for each kind (values from design.md).
6. Add Google-style docstrings to all three new types and both constants.

---

### Task 2 — Extend `reset_state` with Power-Up Instance Attributes

**Deliverable:** Every new instance attribute is initialised in `reset_state()`. Restarting the
game (R key or Restart button) clears all power-up state with no errors.

**Files:** `games/snake/src/main.py`

**Acceptance criteria met:** AC 8 (restart clears power-up state)

**Steps:**

1. In `reset_state`, add the following attribute initialisations:
   ```python
   self.board_power_up: PowerUp | None = None
   self.board_power_up_ticks: int = 0
   self.active_power_up: PowerUpKind | None = None
   self.active_power_up_ticks: int = 0
   self.pre_boost_tick_ms: float | None = None
   self.bills_since_last_power_up: int = 0
   ```
2. Update the docstring for `reset_state` to list the new attributes.

---

### Task 3 — Implement `spawn_power_up_if_due` and `wrap_position`

**Deliverable:** Two new methods exist on `SnakeCashRush` and are individually testable via
`snakeCashRushStep()` in DevTools.

**Files:** `games/snake/src/main.py`

**Acceptance criteria met:** AC 1 (spawning schedule), AC 3 (wall wrap for invincibility)

**Steps:**

1. Implement `spawn_power_up_if_due(self) -> None`:
   - If `board_power_up is not None`, return early.
   - If `bills_since_last_power_up < POWER_UP_SPAWN_INTERVAL`, return early.
   - Pick a random `PowerUpKind` with `choice(list(PowerUpKind))`.
   - Find a free cell (reuse `spawn_cash` logic, but also exclude `self.cash` and
     `self.board_power_up.position` if one exists).
   - Set `self.board_power_up = PowerUp(kind, position)` and
     `self.board_power_up_ticks = POWER_UP_BOARD_LIFE`.
   - Reset `self.bills_since_last_power_up = 0`.
2. Implement `wrap_position(self, point: Point) -> Point`:
   - Return `Point(point.x % BOARD_CELLS, point.y % BOARD_CELLS)`.
   - Python's `%` operator handles negative values correctly for toroidal wrap.

---

### Task 4 — Implement `activate_power_up`, `tick_active_power_up`, and `deactivate_power_up`

**Deliverable:** The three effect-lifecycle methods exist and produce correct state transitions.
Verify via `snakeCashRushSnapshot()` before and after calling `snakeCashRushPlaceCashAhead()` with
a power-up in front of the snake.

**Files:** `games/snake/src/main.py`

**Acceptance criteria met:** AC 2 (Speed Boost), AC 3 (Invincibility), AC 4 (Double Points)

**Steps:**

1. Implement `activate_power_up(self, kind: PowerUpKind) -> None`:
   - Set `self.active_power_up = kind` and
     `self.active_power_up_ticks = POWER_UP_CONFIG[kind]["duration_ticks"]`.
   - For `SPEED_BOOST`: save `self.pre_boost_tick_ms = self.tick_ms`, then
     `self.tick_ms = max(MIN_TICK_MS, self.tick_ms - 20)`.
   - For `INVINCIBILITY` and `DOUBLE_POINTS`: no extra state to set.
   - Update `status_text` to show the label and tick count.
2. Implement `tick_active_power_up(self) -> None`:
   - If `active_power_up is None`, return.
   - Decrement `active_power_up_ticks`.
   - Update `status_text` to show remaining ticks.
   - If `active_power_up_ticks <= 0`, call `deactivate_power_up()`.
3. Implement `deactivate_power_up(self) -> None`:
   - For `SPEED_BOOST`: restore `self.tick_ms = self.pre_boost_tick_ms` and clear
     `self.pre_boost_tick_ms = None`.
   - Set `self.active_power_up = None` and `self.active_power_up_ticks = 0`.
   - Update `status_text` to revert to normal gameplay message.

---

### Task 5 — Wire Power-Up Logic into `advance`

**Deliverable:** Playing the game spawns power-ups, collecting them activates effects, and effects
expire correctly. All three power-up types are functional.

**Files:** `games/snake/src/main.py`

**Acceptance criteria met:** AC 1, AC 2, AC 3, AC 4, AC 8

**Steps:**

1. At the top of `advance`, tick the board power-up expiry:
   ```python
   if self.board_power_up is not None:
       self.board_power_up_ticks -= 1
       if self.board_power_up_ticks <= 0:
           self.board_power_up = None
   ```
2. For `INVINCIBILITY`, replace the wall/body collision block with:
   ```python
   if self.active_power_up == PowerUpKind.INVINCIBILITY:
       next_head = self.wrap_position(next_head)
   elif self.hit_wall(next_head) or next_head in collision_body:
       self.end_game()
       return
   ```
3. After `self.snake.append(next_head)` and inside `if will_collect`, replace the score line:
   ```python
   multiplier = 2 if self.active_power_up == PowerUpKind.DOUBLE_POINTS else 1
   self.score += SCORE_PER_BILL * multiplier
   ```
4. Check if the new head landed on `board_power_up.position` — if so, collect it:
   ```python
   if self.board_power_up is not None and next_head == self.board_power_up.position:
       kind = self.board_power_up.kind
       self.board_power_up = None
       self.activate_power_up(kind)
   ```
5. After cash collection handling, call:
   ```python
   self.spawn_power_up_if_due()
   self.tick_active_power_up()
   ```
6. Increment `self.bills_since_last_power_up += 1` inside `if will_collect`.

---

### Task 6 — Implement `draw_power_up` and Update `draw`

**Deliverable:** The on-board power-up tile renders with the correct kind-specific colour and symbol.
It is visually distinct from the cash bill.

**Files:** `games/snake/src/main.py`

**Acceptance criteria met:** AC 5 (visual distinction)

**Steps:**

1. Implement `draw_power_up(self, ctx) -> None`:
   - If `self.board_power_up is None`, return immediately.
   - Look up `color` and `symbol` from `POWER_UP_CONFIG[self.board_power_up.kind]`.
   - Use the same cell-size / inset arithmetic as `draw_cash`, but with a different inset
     (e.g. 3 px) and a circular rather than rectangular shape to make it visually distinct.
   - Draw a glow shadow using the kind's `color`.
   - Render the `symbol` string centred in the cell.
2. In `draw`, call `self.draw_power_up(ctx)` between `self.draw_cash(ctx)` and
   `self.draw_snake(ctx)` so the tile is visible beneath the snake.

---

### Task 7 — Update `snapshot_json` and Add Dev Hook

**Deliverable:** `snakeCashRushSnapshot()` in DevTools returns the new power-up state fields.

**Files:** `games/snake/src/main.py`

**Acceptance criteria met:** AC 7

**Steps:**

1. In `snapshot_json`, add to the payload dict:
   ```python
   "boardPowerUp": {
       "kind": self.board_power_up.kind.value,
       "position": {"x": self.board_power_up.position.x, "y": self.board_power_up.position.y},
   } if self.board_power_up else None,
   "activePowerUp": self.active_power_up.value if self.active_power_up else None,
   "activePowerUpTicks": self.active_power_up_ticks,
   ```

---

### Task 8 — Manual Playtesting & Edge Case Verification

**Deliverable:** All 10 acceptance criteria are manually verified. Known edge cases documented.

**Files:** None (verification only)

**Acceptance criteria met:** AC 1–10

**Checklist:**

- [ ] Power-up appears every 3 bills and disappears after 100 ticks if not collected.
- [ ] Speed Boost lowers speed for 50 ticks and restores it correctly even if more cash is
      collected during the boost window.
- [ ] Invincibility wraps the snake toroidally for 30 ticks; self-collision is also skipped.
- [ ] Double Points doubles all cash collected for 40 ticks.
- [ ] Each power-up renders with a unique colour and symbol on the canvas.
- [ ] HUD status text shows the active effect name and countdown.
- [ ] `snakeCashRushSnapshot()` includes `boardPowerUp`, `activePowerUp`, `activePowerUpTicks`.
- [ ] Pressing R during an active effect clears it instantly.
- [ ] Best score in localStorage reflects the doubled points.
- [ ] A new `SLOW_DOWN` power-up can be added by editing only `PowerUpKind` and `POWER_UP_CONFIG`.
