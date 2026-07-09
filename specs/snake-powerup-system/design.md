# Design: Snake Power-Up System

## Overview
The power-up system extends the existing `SnakeCashRush` class in `main.py` with three
collectible power-up types (Speed Boost, Invincibility, Double Points) that spawn periodically
alongside the existing cash bill, persist on the board for a limited number of game ticks, and
apply a temporary effect when collected. All timers are measured in game ticks (consistent with
the existing fixed-timestep accumulator pattern) rather than wall-clock milliseconds. A new HUD
element in `index.html`/`styles.css` surfaces the active effect and its remaining duration to
the player. No new source files are introduced.

## Architecture

```
Browser (PyScript runtime)
│
├── index.html          ← adds <div id="powerupIndicator"> to HUD
├── styles.css          ← adds power-up canvas colours + HUD indicator styles
└── main.py
    └── SnakeCashRush class
        │
        ├── State (new fields)
        │   ├── powerup: PowerUp | None          ← item currently on board
        │   ├── active_effect: str | None        ← effect kind currently running
        │   ├── effect_ticks_remaining: int      ← ticks left on active effect
        │   ├── powerup_despawn_ticks: int       ← ticks before on-board item expires
        │   ├── next_powerup_ticks: int          ← countdown to next spawn attempt
        │   └── pre_boost_tick_ms: float         ← saved tick_ms before Speed Boost
        │
        ├── New methods
        │   ├── spawn_powerup()
        │   ├── apply_effect()
        │   ├── expire_effect()
        │   ├── draw_powerup()
        │   └── update_powerup_hud()
        │
        └── Modified methods
            ├── reset_state()   ← clears all power-up state
            ├── advance()       ← tick-based countdown, collection, despawn
            └── draw()          ← delegates to draw_powerup()
```

## Component Breakdown

### `PowerUp` dataclass (new, frozen)
- **Responsibility**: Immutable value object representing a power-up present on the board.
- **Fields**: `kind: str` (one of the `POWERUP_*` constants), `position: Point`.
- **Interface**: No methods; constructed by `spawn_powerup()`, compared by value.

### Module-level constants (additions to `main.py`)
| Constant | Value | Purpose |
|---|---|---|
| `POWERUP_SPEED` | `"speed"` | Speed Boost kind identifier |
| `POWERUP_INVINCIBILITY` | `"invincibility"` | Invincibility kind identifier |
| `POWERUP_DOUBLE` | `"double"` | Double Points kind identifier |
| `POWERUP_KINDS` | `[POWERUP_SPEED, POWERUP_INVINCIBILITY, POWERUP_DOUBLE]` | Ordered list for random selection |
| `POWERUP_SPAWN_INTERVAL_TICKS` | `30` | Ticks between spawn attempts (~4.8 s at base speed) |
| `POWERUP_DESPAWN_TICKS` | `50` | Ticks before uncollected power-up expires (~8 s at base speed) |
| `SPEED_BOOST_TICKS` | `30` | Duration of Speed Boost in ticks (~5 s at base speed) |
| `SPEED_BOOST_FACTOR` | `0.55` | Multiplier applied to `tick_ms` during boost |
| `INVINCIBILITY_TICKS` | `25` | Duration of Invincibility in ticks (~4 s at base speed) |
| `DOUBLE_POINTS_TICKS` | `50` | Duration of Double Points in ticks (~8 s at base speed) |

### `spawn_powerup(snake, cash)` (new method)
- **Responsibility**: Choose a random unoccupied board cell (not snake, not cash bill) and
  return a `PowerUp` with a randomly selected kind.
- **Interface**: `(self, snake: list[Point], cash: Point) -> PowerUp | None`
- Returns `None` only if the board is entirely full (practically impossible during play).

### `apply_effect(kind)` (new method)
- **Responsibility**: Activate a power-up effect. Replaces any in-progress effect.
- Calls `expire_effect()` first if an effect is already active.
- For `POWERUP_SPEED`: saves `self.tick_ms` → `self.pre_boost_tick_ms`, then sets
  `self.tick_ms = max(MIN_TICK_MS, self.tick_ms * SPEED_BOOST_FACTOR)`.
- Sets `self.active_effect = kind` and the appropriate `effect_ticks_remaining`.
- **Interface**: `(self, kind: str) -> None`

### `expire_effect()` (new method)
- **Responsibility**: Deactivate the current effect and restore any overridden state.
- For `POWERUP_SPEED`: restores `self.tick_ms = self.pre_boost_tick_ms`.
- Clears `self.active_effect = None`, `self.effect_ticks_remaining = 0`.
- **Interface**: `(self) -> None`

### `draw_powerup(ctx)` (new method)
- **Responsibility**: Render the on-board power-up item using a kind-specific colour and
  single-character glyph centred in the cell.
- Kind → colour mapping: Speed `#f59e0b` (amber), Invincibility `#a78bfa` (violet),
  Double Points `#f43f5e` (rose).
- Kind → glyph mapping: Speed `⚡`, Invincibility `🛡`, Double Points `✕2`.
- **Interface**: `(self, ctx: object) -> None`

### `update_powerup_hud()` (new method)
- **Responsibility**: Refresh the `#powerupIndicator` DOM element.
- If no active effect: hides the element (`classList.remove("visible")`).
- If active: shows label (e.g., `"⚡ Speed Boost — 22 ticks"`) and adds the appropriate
  kind CSS class for colour coding.
- **Interface**: `(self) -> None`

### `reset_state()` (modified)
- Adds initialisation of all new state fields:
  `self.powerup = None`, `self.active_effect = None`, `self.effect_ticks_remaining = 0`,
  `self.powerup_despawn_ticks = 0`, `self.next_powerup_ticks = POWERUP_SPAWN_INTERVAL_TICKS`,
  `self.pre_boost_tick_ms = BASE_TICK_MS`.

### `advance()` (modified)
Additions, in order of execution each tick:

1. **Effect countdown**: if `active_effect` is set, decrement `effect_ticks_remaining`; if it
   reaches 0, call `expire_effect()`.
2. **Collision with invincibility**: if `active_effect == POWERUP_INVINCIBILITY` and the new
   head would hit a wall, wrap it to the opposite edge (Pac-Man style) instead of calling
   `end_game()`. Self-collision is ignored (head enters a body cell without ending the run).
3. **Power-up collection**: after resolving the new head position, check
   `next_head == self.powerup.position`; if so, call `apply_effect(self.powerup.kind)`, clear
   `self.powerup = None`, and reset `self.next_powerup_ticks`.
4. **Score modifier**: when collecting a cash bill, use
   `SCORE_PER_BILL * 2 if self.active_effect == POWERUP_DOUBLE else SCORE_PER_BILL`.
5. **Despawn countdown**: if a power-up is on board, decrement `self.powerup_despawn_ticks`;
   if it reaches 0, set `self.powerup = None`.
6. **Spawn countdown**: decrement `self.next_powerup_ticks`; if it reaches 0 and
   `self.powerup is None`, call `self.powerup = self.spawn_powerup(...)` and reset
   `self.powerup_despawn_ticks = POWERUP_DESPAWN_TICKS`.
7. Call `update_powerup_hud()`.

### `draw()` (modified)
Calls `self.draw_powerup(ctx)` after `draw_cash(ctx)` and before `draw_snake(ctx)` so the
power-up renders beneath the snake head but above the board grid.

## Data Model

```
SnakeCashRush (instance state)
├── powerup: PowerUp | None
│   └── PowerUp
│       ├── kind: str          ("speed" | "invincibility" | "double")
│       └── position: Point    (x: int, y: int)
├── active_effect: str | None
├── effect_ticks_remaining: int
├── powerup_despawn_ticks: int
├── next_powerup_ticks: int
└── pre_boost_tick_ms: float
```

No persistent storage additions — all power-up state is session-only and resets on restart.

## Data Flow

### Happy path — player collects Speed Boost

```
tick N:   next_powerup_ticks reaches 0
          → spawn_powerup() → PowerUp(kind="speed", position=Point(12, 7))
          → powerup_despawn_ticks = 50, next_powerup_ticks = 30

tick N+8: next_head == PowerUp.position
          → apply_effect("speed")
              pre_boost_tick_ms = tick_ms (e.g. 145)
              tick_ms = max(82, 145 × 0.55) = 82 (floor)
              active_effect = "speed"
              effect_ticks_remaining = 30
          → powerup = None
          → update_powerup_hud() → shows "⚡ Speed Boost — 30 ticks"

ticks N+9 … N+37:
          each advance() → effect_ticks_remaining decrements
          → update_powerup_hud() updates remaining count

tick N+38: effect_ticks_remaining reaches 0
          → expire_effect()
              tick_ms = pre_boost_tick_ms (145)
              active_effect = None
          → update_powerup_hud() → hides indicator
```

### Despawn path — player ignores power-up

```
tick N:   power-up spawned, powerup_despawn_ticks = 50
ticks N+1…N+49: powerup_despawn_ticks decrements each tick
tick N+50: powerup_despawn_ticks reaches 0 → powerup = None
```

### Invincibility + wall collision

```
advance():
  next_head = Point(-1, 5)  ← one step past left wall
  active_effect == "invincibility"
  → wrap: next_head = Point(BOARD_CELLS - 1, 5)
  → game continues; snake appears on opposite wall
```

## API Contracts

All interfaces are internal Python methods on `SnakeCashRush`. There is no HTTP or JS API.

| Method | Signature | Behaviour |
|---|---|---|
| `spawn_powerup` | `(snake: list[Point], cash: Point) -> PowerUp \| None` | Returns a `PowerUp` at a random free cell with a random kind. Returns `None` if no free cells exist. |
| `apply_effect` | `(kind: str) -> None` | Activates the named effect. Calls `expire_effect()` first if one is already running. |
| `expire_effect` | `() -> None` | Cleans up the current effect and restores any overridden state. Safe to call when no effect is active. |
| `draw_powerup` | `(ctx: object) -> None` | Renders the on-board item. No-op if `self.powerup is None`. |
| `update_powerup_hud` | `() -> None` | Syncs the HUD element with current effect state. |

## Key Design Decisions

### 1 — Tick-based timers (not wall-clock `setTimeout`)
**Decision**: All durations are measured in game ticks, not milliseconds.
**Rationale**: The existing system already has a tick counter via the accumulator. Using ticks
avoids creating additional `create_proxy` closures for `setTimeout`-based expiry, which would
complicate lifecycle management and garbage collection. A side effect is that Speed Boost causes
tick-based timers to expire faster in real time — this is a desirable emergent property (the
boost period feels action-packed).
**Alternative considered**: `window.setTimeout` with ms durations. Rejected because it requires
additional proxy management and couples power-up timing to wall-clock time, making it harder to
reason about interactions with tick speed.

### 2 — Invincibility uses wall wrapping
**Decision**: While invincibility is active, wall collisions wrap the snake to the opposite
edge rather than preventing death in-place or freezing movement.
**Rationale**: Wrap-around is unambiguous (the snake always moves), visually satisfying, and
makes invincibility feel genuinely powerful. Stopping at the wall without dying would be
confusing. Silently ignoring wall collisions without wrap would leave the snake stuck.
**Alternative considered**: Simply skipping the `end_game()` call and keeping the snake at the
wall cell. Rejected because it breaks the invariant that `advance()` always moves the head.

### 3 — Mutually exclusive effects (latest wins)
**Decision**: Collecting a power-up while one is already active immediately replaces it via
`expire_effect()` followed by `apply_effect()`.
**Rationale**: Prevents complex stacking interactions (e.g., double Speed Boost) that would
require multi-level state restoration. Simplest correct behaviour; players can intuitively
predict it.
**Alternative considered**: Queuing effects. Rejected as over-engineered for three effect types.

### 4 — Speed Boost saves and restores `pre_boost_tick_ms`
**Decision**: Before modifying `tick_ms`, save the current value to `pre_boost_tick_ms` and
restore it on expiry.
**Rationale**: The progressive difficulty system already modifies `tick_ms` as score increases.
Storing the pre-boost value ensures that score-based acceleration is preserved correctly when
the boost expires, rather than reverting to `BASE_TICK_MS`.

### 5 — `PowerUp` as a frozen dataclass alongside `Point`
**Decision**: `PowerUp` is a `@dataclass(frozen=True)` with `kind` and `position` fields.
**Rationale**: Consistent with the existing `Point` pattern. Immutability prevents accidental
mutation; value-based equality makes position checks straightforward.

## Security Considerations
- All inputs are keyboard events already sanitised by the existing `handle_keydown()` handler.
- Power-up `kind` values are drawn from a fixed constant list (`POWERUP_KINDS`); no external
  string is ever used as a kind value, eliminating any injection risk.
- No network calls, no `eval()`, no dynamic code execution introduced.
- No new DOM event listeners that could expose attack surface.

## Performance & Scalability Notes
- All new per-tick operations are O(1): integer decrements and comparisons.
- `spawn_powerup()` is O(BOARD_CELLS²) = O(400) — identical to the existing `spawn_cash()`
  and called at most once every 30 ticks, not every frame.
- One additional canvas draw call per frame (`draw_powerup`) adds negligible overhead on any
  device capable of running PyScript.
- The HUD DOM update (`update_powerup_hud`) runs every tick, not every frame, keeping DOM
  writes bounded.

## Open Questions Resolved
| Question (from intent.md) | Resolution |
|---|---|
| Spawn frequency | Fixed tick countdown: every `POWERUP_SPAWN_INTERVAL_TICKS = 30` ticks after the previous power-up was either collected or despawned. |
| On-board lifespan | `POWERUP_DESPAWN_TICKS = 50` ticks (~8 s at base speed). |
| Effect durations | Speed Boost: 30 ticks (~5 s). Invincibility: 25 ticks (~4 s). Double Points: 50 ticks (~8 s). |
| Invincibility at walls | Wall wrapping (Pac-Man style teleport to opposite edge). |
| Speed Boost + progressive difficulty | Boost saves `pre_boost_tick_ms` and restores it on expiry; score-based acceleration is preserved correctly. |

## Remaining Open Questions
- Should the power-up HUD indicator show a visual countdown bar (CSS progress strip) in
  addition to the tick count, for a more glanceable in-game signal?
- Is 30-tick spawn interval the right pacing for higher-score runs where ticks arrive faster?
  A score-based adaptive interval could be considered in a follow-up.
