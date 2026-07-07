# Design — Power-Up System

## Technical Architecture

The power-up system integrates directly into the existing `SnakeCashRush` game loop in `main.py`. No new files are introduced. The feature adds:

1. **Data models** — A `PowerUpType` enum and a `PowerUp` dataclass to represent items on the board.
2. **Spawn logic** — A timer-driven spawner that places a power-up on an unoccupied cell at random intervals.
3. **Collection & activation** — Detection in the existing `advance()` method; activates the effect and starts a countdown.
4. **Effect application** — Conditional branches in `advance()` (for invincibility) and score calculation (for double points).
5. **Expiry** — A real-time countdown decremented each frame that deactivates the effect when it hits zero.
6. **Rendering** — Snake color override and a HUD timer bar drawn on the canvas.

```
┌─────────────────────────────────────────────────┐
│                SnakeCashRush                     │
│                                                 │
│  Existing:         New:                         │
│  ─────────         ────                         │
│  snake []          powerup_type: enum           │
│  cash: Point       powerup: PowerUp | None      │
│  score: int        active_effect: PowerUpType?   │
│  tick_ms           effect_remaining_ms: float    │
│  advance()    ──►  spawn_powerup_timer: float    │
│  draw()       ──►  POWERUP_DURATION_MS = 6000   │
│  game_frame() ──►  POWERUP_SPAWN_MIN/MAX_MS     │
│                    POWERUP_DESPAWN_MS = 10000    │
└─────────────────────────────────────────────────┘
```

## Component Breakdown

### `PowerUpType` (Enum)
```python
class PowerUpType(Enum):
    DOUBLE_POINTS = "double_points"
    INVINCIBILITY = "invincibility"
```

### `PowerUp` (Dataclass)
```python
@dataclass(frozen=True)
class PowerUp:
    position: Point
    kind: PowerUpType
    age_ms: float = 0.0  # tracks how long it's been on board
```

### Modified methods in `SnakeCashRush`

| Method | Change |
|--------|--------|
| `reset_state()` | Initialize power-up fields (`powerup`, `active_effect`, `effect_remaining_ms`, `spawn_timer_ms`, `next_spawn_delay_ms`) |
| `game_frame(timestamp)` | Decrement `effect_remaining_ms` and `spawn_timer_ms` using frame delta; handle expiry and spawn triggers |
| `advance()` | Check collision with `powerup.position`; activate effect. Apply invincibility (skip body collision). Apply double points on cash collection |
| `draw()` | Call new `draw_powerup()` and `draw_effect_bar()` |
| `snapshot_json()` | Include `activeEffect`, `effectRemainingMs`, `powerup` |

### New methods

| Method | Purpose |
|--------|---------|
| `spawn_powerup()` | Pick a random type and unoccupied position; set `self.powerup` |
| `collect_powerup()` | Activate effect, clear board item, reset spawn timer |
| `expire_effect()` | Clear `active_effect`, reset visual state |
| `draw_powerup(ctx)` | Render the power-up item with a distinct icon/color per type |
| `draw_effect_bar(ctx)` | Render a horizontal timer bar in the HUD area showing remaining duration |
| `get_snake_color()` | Return color based on active effect (gold for double points, cyan for invincibility, default green) |

## Data Flow

```
game_frame(timestamp)
  │
  ├─► Compute frame_delta
  │
  ├─► Decrement spawn_timer_ms by frame_delta
  │     └─► If ≤ 0 and no powerup on board → spawn_powerup()
  │
  ├─► If powerup on board: increment powerup.age_ms
  │     └─► If age_ms > DESPAWN_MS → remove powerup, reset spawn timer
  │
  ├─► Decrement effect_remaining_ms by frame_delta
  │     └─► If ≤ 0 and effect active → expire_effect()
  │
  ├─► advance() [on tick boundaries, as before]
  │     ├─► Move head
  │     ├─► Check wall collision (always fatal)
  │     ├─► Check body collision → skip if INVINCIBILITY active
  │     ├─► Check powerup collision → collect_powerup()
  │     ├─► Check cash collision → score += SCORE_PER_BILL * multiplier
  │     └─► ...
  │
  └─► draw()
        ├─► draw_board()
        ├─► draw_cash()
        ├─► draw_powerup()    ← NEW
        ├─► draw_snake()      ← uses get_snake_color()
        └─► draw_effect_bar() ← NEW
```

## API Contracts

### Constants
```python
POWERUP_DURATION_MS: float = 6000.0       # 6 seconds active
POWERUP_SPAWN_MIN_MS: float = 8000.0      # min delay between spawns
POWERUP_SPAWN_MAX_MS: float = 15000.0     # max delay between spawns
POWERUP_DESPAWN_MS: float = 10000.0       # despawn if uncollected
```

### New instance attributes on `SnakeCashRush`
```python
self.powerup: PowerUp | None              # item currently on board
self.active_effect: PowerUpType | None    # currently active effect
self.effect_remaining_ms: float           # countdown for active effect
self.spawn_timer_ms: float                # countdown to next spawn
self.next_spawn_delay_ms: float           # randomized target for spawn_timer
```

### `snapshot_json()` additions
```json
{
  "powerup": {"x": 5, "y": 12, "kind": "double_points"} | null,
  "activeEffect": "invincibility" | null,
  "effectRemainingMs": 3200.5
}
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Real-time timers (frame delta) for spawn/duration** | Power-ups should feel consistent regardless of game speed. Using tick-based timing would make effects shorter as the game speeds up, which punishes skilled players. |
| **One power-up on board at a time** | Keeps the 20×20 grid uncluttered and makes each spawn a clear event the player notices. |
| **New effect replaces old (no stacking)** | Simplifies implementation and creates a strategic choice: "Do I grab this or keep my current effect?" |
| **Invincibility = body pass-through only** | Walls still kill. Full invincibility would remove all challenge and break the core gameplay tension. |
| **Despawn after 10 seconds** | Creates urgency without being too punishing. Prevents stale items lingering on the board. |
| **Snake color change + timer bar** | Dual visual feedback — color shows *what* is active, bar shows *how long* remains. Both render on canvas (no HTML changes). |
| **Enum-based type system** | Easy to extend with new power-up types in future iterations by adding enum values and corresponding logic branches. |
