# Design — Power-Up System

> Builds on: [`intent.md`](./intent.md)

## Architecture Overview

The power-up system slots into the existing `SnakeCashRush` class in `main.py` without touching
the fixed-timestep accumulator, the `Point` coordinate type, or the JS bridge.

Three new concerns are introduced:

1. **Spawning** — deciding when and where a power-up appears on the board.
2. **Effect management** — tracking which effect (if any) is active, applying it each tick, and
   expiring it after the configured duration.
3. **Rendering** — drawing the on-board power-up tile and updating the HUD status text.

All state lives in `SnakeCashRush` instance attributes. A `PowerUpKind` enum and a `PowerUp`
frozen dataclass (parallel to the existing `Point` dataclass pattern) carry the data cleanly
without adding module-level mutable variables.

```
advance() tick
  │
  ├─ spawn_power_up_if_due()   ← every POWER_UP_SPAWN_INTERVAL bills, if none on board
  │
  ├─ check power-up expiry     ← decrement board_power_up_ticks; remove if 0
  │
  ├─ handle collection         ← if next_head == power_up.position → activate_power_up()
  │
  ├─ apply active effect       ← invincibility skip, double-points multiplier
  │
  └─ tick active effect down   ← decrement active_power_up_ticks; deactivate if 0

draw()
  │
  ├─ draw_board()
  ├─ draw_cash()
  ├─ draw_power_up()           ← NEW: renders on-board tile with kind-specific colour/symbol
  └─ draw_snake()
```

---

## Component Breakdown

| Component | Responsibility | Location |
|-----------|---------------|----------|
| `PowerUpKind` | `Enum` of `SPEED_BOOST`, `INVINCIBILITY`, `DOUBLE_POINTS` | `main.py` module level |
| `PowerUp` | Frozen dataclass holding `kind: PowerUpKind` and `position: Point` | `main.py` module level |
| `POWER_UP_CONFIG` | `dict[PowerUpKind, dict]` mapping each kind to its `duration_ticks`, `color`, `symbol`, and `label` | `main.py` module level |
| `POWER_UP_SPAWN_INTERVAL` | Constant — bills between spawns (default `3`) | `main.py` module level |
| `POWER_UP_BOARD_LIFE` | Constant — ticks a power-up stays on the board uncollected (default `100`) | `main.py` module level |
| `SnakeCashRush.board_power_up` | `PowerUp \| None` — the item currently on the board (not yet collected) | `SnakeCashRush` instance |
| `SnakeCashRush.board_power_up_ticks` | `int` — ticks remaining before the uncollected item expires | `SnakeCashRush` instance |
| `SnakeCashRush.active_power_up` | `PowerUpKind \| None` — the effect currently applied to the snake | `SnakeCashRush` instance |
| `SnakeCashRush.active_power_up_ticks` | `int` — ticks remaining for the active effect | `SnakeCashRush` instance |
| `SnakeCashRush.pre_boost_tick_ms` | `float \| None` — saved tick speed before a Speed Boost so it can be restored | `SnakeCashRush` instance |
| `SnakeCashRush.bills_since_last_power_up` | `int` — counter to trigger spawning | `SnakeCashRush` instance |
| `spawn_power_up_if_due()` | Checks the bill counter; if due, picks a random `PowerUpKind` and a random empty cell | `SnakeCashRush` method |
| `activate_power_up(kind)` | Applies the immediate effect of the collected power-up and starts the tick countdown | `SnakeCashRush` method |
| `tick_active_power_up()` | Decrements `active_power_up_ticks`; calls `deactivate_power_up()` when it reaches 0 | `SnakeCashRush` method |
| `deactivate_power_up()` | Removes the active effect, restores any saved state (e.g. `pre_boost_tick_ms`) | `SnakeCashRush` method |
| `draw_power_up(ctx)` | Renders the on-board power-up tile using kind-specific colour and symbol from `POWER_UP_CONFIG` | `SnakeCashRush` method |

---

## Data Flow

### Spawning

```
advance() called
  → bills_since_last_power_up incremented after each cash collection
  → if bills_since_last_power_up >= POWER_UP_SPAWN_INTERVAL and board_power_up is None:
      kind  = random choice from PowerUpKind
      position = spawn_power_up(snake, cash)   # same logic as spawn_cash — finds empty cell
      board_power_up = PowerUp(kind, position)
      board_power_up_ticks = POWER_UP_BOARD_LIFE
      bills_since_last_power_up = 0
```

### Board Expiry

```
each advance() call (while board_power_up is not None):
  board_power_up_ticks -= 1
  if board_power_up_ticks <= 0:
      board_power_up = None   # disappears without being collected
```

### Collection

```
next_head == board_power_up.position
  → board_power_up = None          # remove from board
  → activate_power_up(kind)
      SPEED_BOOST:
          pre_boost_tick_ms = tick_ms
          tick_ms = max(MIN_TICK_MS, tick_ms - 20)
      INVINCIBILITY:
          (no immediate state change; collision checks read active_power_up)
      DOUBLE_POINTS:
          (no immediate state change; scoring reads active_power_up)
      active_power_up = kind
      active_power_up_ticks = POWER_UP_CONFIG[kind]["duration_ticks"]
```

### Effect Application (per tick)

```
SPEED_BOOST:    tick_ms already lowered; no per-tick action needed
INVINCIBILITY:  in advance(), before hit_wall() / body collision check:
                  if active_power_up == INVINCIBILITY:
                      next_head = wrap_position(next_head)   # toroidal wrap
                      skip body-collision check
DOUBLE_POINTS:  in advance(), when will_collect is True:
                  multiplier = 2 if active_power_up == DOUBLE_POINTS else 1
                  score += SCORE_PER_BILL * multiplier
```

### Deactivation

```
each advance() call (while active_power_up is not None):
  active_power_up_ticks -= 1
  if active_power_up_ticks <= 0:
      deactivate_power_up()
          SPEED_BOOST: tick_ms = pre_boost_tick_ms; pre_boost_tick_ms = None
          others:      no state to restore
          active_power_up = None
```

---

## New / Modified Interfaces

### New Constants (module level)

| Name | Type | Value | Purpose |
|------|------|-------|---------|
| `POWER_UP_SPAWN_INTERVAL` | `int` | `3` | Bills collected between power-up spawns |
| `POWER_UP_BOARD_LIFE` | `int` | `100` | Ticks a board power-up survives uncollected |

### New Types (module level)

```python
class PowerUpKind(Enum):
    SPEED_BOOST   = "speed_boost"
    INVINCIBILITY = "invincibility"
    DOUBLE_POINTS = "double_points"

@dataclass(frozen=True)
class PowerUp:
    kind: PowerUpKind
    position: Point

POWER_UP_CONFIG: dict[PowerUpKind, dict] = {
    PowerUpKind.SPEED_BOOST:   {"duration_ticks": 50,  "color": "#ffe08a", "symbol": "⚡", "label": "Speed Boost"},
    PowerUpKind.INVINCIBILITY: {"duration_ticks": 30,  "color": "#a78bfa", "symbol": "🛡", "label": "Invincibility"},
    PowerUpKind.DOUBLE_POINTS: {"duration_ticks": 40,  "color": "#fb923c", "symbol": "×2", "label": "Double Points"},
}
```

### New `SnakeCashRush` Instance Attributes (added in `reset_state`)

| Attribute | Type | Initial Value | Purpose |
|-----------|------|---------------|---------|
| `board_power_up` | `PowerUp \| None` | `None` | Item on the board, not yet collected |
| `board_power_up_ticks` | `int` | `0` | Ticks until the board item expires |
| `active_power_up` | `PowerUpKind \| None` | `None` | Currently active effect |
| `active_power_up_ticks` | `int` | `0` | Ticks remaining for active effect |
| `pre_boost_tick_ms` | `float \| None` | `None` | Saved tick speed before Speed Boost |
| `bills_since_last_power_up` | `int` | `0` | Counter to trigger next spawn |

### New / Modified Methods

| Method | Signature | Phase | Notes |
|--------|-----------|-------|-------|
| `spawn_power_up_if_due` | `(self) -> None` | advance | Spawns if `bills_since_last_power_up >= POWER_UP_SPAWN_INTERVAL` |
| `activate_power_up` | `(self, kind: PowerUpKind) -> None` | advance | Applies effect, starts countdown |
| `tick_active_power_up` | `(self) -> None` | advance | Decrements counter, calls deactivate |
| `deactivate_power_up` | `(self) -> None` | advance | Restores state, clears active |
| `wrap_position` | `(self, point: Point) -> Point` | advance | Toroidal wrap for invincibility |
| `draw_power_up` | `(self, ctx) -> None` | draw | Draws on-board tile |
| `advance` | modified | — | Call new helpers, handle double-points, invincibility skip |
| `reset_state` | modified | — | Initialise 6 new attributes |
| `snapshot_json` | modified | — | Add `boardPowerUp`, `activePowerUp`, `activePowerUpTicks` keys |
| `draw` | modified | — | Call `draw_power_up(ctx)` between `draw_cash` and `draw_snake` |

### HUD changes (no new DOM elements needed)

`status_text.textContent` will be updated to show the active power-up label and remaining ticks
during the effect window, e.g. `"⚡ Speed Boost — 32 ticks left"`.

---

## Key Design Decisions

| Decision | Options Considered | Chosen Approach | Rationale |
|----------|-------------------|-----------------|-----------|
| Where to store config | Hardcoded constants per type / dict lookup | `POWER_UP_CONFIG` dict keyed by `PowerUpKind` | Satisfies AC 10 — adding a type requires only a new `POWER_UP_CONFIG` entry and `PowerUpKind` variant |
| Duration tracking unit | Wall-clock milliseconds / tick count | Tick count | Consistent with the rest of the game loop; speed changes don't distort duration |
| Invincibility wrap | Hard stop at wall / toroidal wrap | Toroidal wrap | More interesting play pattern; natural consequence of "can't die" |
| Power-up count on board | Multiple simultaneous / at most one | At most one | Keeps the UI legible and the spawn logic simple; listed as out-of-scope for v1 |
| Speed Boost restore | Track delta / save absolute value | Save `pre_boost_tick_ms` | Composing with the normal speed increase is unambiguous when restoring |
| HUD display | New DOM element / reuse `status_text` | Reuse `status_text` | No HTML changes required; matches existing status-text update pattern |

---

## Risks & Open Questions

- **Visual symbol rendering on Canvas**: Emoji glyphs (`⚡`, `🛡`) may render inconsistently across
  browsers. Fallback to ASCII symbols (`+`, `*`, `x2`) should be tested and added to `POWER_UP_CONFIG`
  as an alternative field.
- **Speed Boost + natural speed increase interaction**: If the snake collects cash bills while Speed
  Boost is active, `tick_ms` is recalculated from `BASE_TICK_MS` (natural speed formula), which may
  contradict the expected boost. The `pre_boost_tick_ms` restore must use the _post-natural-increase_
  value at the time of boost activation, not the value at collection time.
- **Invincibility + body wrap**: If the snake wraps through a wall and re-enters a cell occupied by
  its own body, should the invincibility protect against self-collision too? AC 3 says "wall and
  self-collision checks to be skipped", so yes — but this should be confirmed by a playtester before
  shipping.
- **localStorage score integrity**: Double Points may dramatically inflate scores. If a future version
  adds a leaderboard, this should be flagged so the scoring event can carry a metadata flag.
