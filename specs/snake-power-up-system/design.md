# Design

## Technical Architecture

### Overview
The power-up system is implemented inside the existing SnakeCashRush runtime in Python (PyScript), with all gameplay state owned by the SnakeCashRush class. The design extends current tick-based logic by introducing:
- Power-up entity state (spawned item on board)
- Active effect state (time-bounded modifiers)
- Effect-aware rule evaluation (movement speed, collision outcome, scoring multiplier)
- HUD feedback for active effects and remaining duration

### Runtime Placement
- Core logic remains in the game loop and tick processing flow in main.py.
- DOM updates continue via js-module-based bindings already used by SnakeCashRush.
- No new global mutable Python state is introduced.

### Assumptions (Pending User Confirmation)
- Only one power-up item can be present on the board at a time.
- If an already-active power-up is collected again, its duration is refreshed (not stacked).
- Invincibility ignores lethal collision checks (wall/body) while active; movement remains normal.
- Default durations:
  - Speed boost: 6 seconds
  - Invincibility: 5 seconds
  - Double points: 8 seconds
- Spawn cadence is time-based with randomized interval windows.
- Double points applies to cash pickup scoring events only.

## Component Breakdown

### 1. PowerUp Model (In-Class Data Structure)
Purpose: represent a collectible temporary ability on the board.

Suggested fields:
- type: one of speed_boost | invincibility | double_points
- position: Point
- spawned_at_ms: float
- ttl_ms: int

Notes:
- This can be a lightweight dataclass or dict maintained within SnakeCashRush.
- Position must be generated from valid free cells, excluding snake body and cash.

### 2. ActiveEffects Registry
Purpose: track currently active timed effects.

Suggested structure:
- active_effects: dict[str, float]
  - key = effect type
  - value = expiration timestamp in milliseconds

Behavior:
- Effect starts by setting expiration timestamp.
- Re-collection of same type updates expiration timestamp.
- Expired effects are removed during tick updates.

### 3. Spawn Controller
Purpose: determine when and where power-ups appear.

Suggested state:
- current_power_up: PowerUp | None
- next_spawn_at_ms: float

Behavior:
- On each tick/frame, evaluate whether current time >= next_spawn_at_ms and no active board item exists.
- Spawn one random power-up type at a valid location.
- After collect or timeout/despawn, schedule next spawn.

### 4. Effect Engine
Purpose: apply effect modifiers to existing gameplay rules.

Rules:
- speed_boost active:
  - effective tick interval decreases (faster snake), bounded by safe minimum.
- invincibility active:
  - lethal collision branch in advance() is bypassed.
- double_points active:
  - score increments on cash pickup are multiplied by 2.

### 5. HUD Feedback Layer
Purpose: provide visibility into active effects and durations.

UI additions:
- Add a status area for active power-ups (label + remaining seconds).
- Optional visual treatment on canvas/HUD tiles while effects are active.

Update policy:
- Refresh display each draw cycle or after effect state mutations.

## Data Flow

## Flow A: Spawn Lifecycle
1. Tick/frame update checks if a board power-up is absent.
2. If spawn time reached, choose type and valid position.
3. Create current_power_up and render it.

## Flow B: Pickup and Activation
1. Snake head advances to new position.
2. If head position equals power-up position:
- Remove board power-up.
- Set/refresh effect expiration in active_effects.
- Schedule next spawn time.

## Flow C: Tick-Time Effect Evaluation
1. Determine active effects by comparing now_ms against expiration timestamps.
2. Remove expired effects.
3. Derive effective gameplay modifiers:
- effective_tick_ms from base tick and speed_boost status
- collision lethality gate from invincibility status
- score multiplier from double_points status

## Flow D: Rendering and HUD
1. Draw board, snake, cash, and power-up item (if present).
2. Draw/update active effect indicators and countdowns.

## API Contracts

These are internal class-level contracts for SnakeCashRush extension.

### Types
- PowerUpType = Literal["speed_boost", "invincibility", "double_points"]

### New/Updated State Fields
- self.current_power_up: PowerUp | None
- self.active_effects: dict[str, float]
- self.next_power_up_spawn_at_ms: float
- self.base_tick_ms: int

### New Methods (Proposed)
- initialize_power_up_state() -> None
  - Initializes power-up state during reset/start.

- maybe_spawn_power_up(now_ms: float) -> None
  - Spawns power-up if due and no active board power-up exists.

- spawn_power_up(excluded_cells: Iterable[Point], now_ms: float) -> PowerUp | None
  - Creates a valid power-up object at a free location.

- collect_power_up_if_present(head: Point, now_ms: float) -> bool
  - Checks pickup collision and activates effect when collected.

- activate_effect(effect_type: str, now_ms: float) -> None
  - Sets or refreshes expiration timestamp.

- prune_expired_effects(now_ms: float) -> None
  - Removes expired entries from active_effects.

- is_effect_active(effect_type: str, now_ms: float) -> bool
  - Returns active status for a specific effect.

- compute_effective_tick_ms(now_ms: float) -> int
  - Returns current tick interval considering speed_boost.

- current_score_multiplier(now_ms: float) -> int
  - Returns 2 when double_points is active, else 1.

- render_power_up_hud(now_ms: float) -> None
  - Updates HUD text for active effects and remaining time.

### Updated Existing Methods (Proposed)
- reset_state()
  - Must reset current_power_up, active_effects, and spawn timers.

- advance()
  - Must:
    - evaluate effect expiry
    - apply invincibility to collision outcome
    - apply score multiplier on cash pickup
    - process power-up pickup

- game_frame(timestamp)
  - Must evaluate spawn timing and effect-aware tick interval.

- draw()
  - Must render board power-up and active effect feedback.

## Key Design Decisions and Rationale

1. Keep all logic in SnakeCashRush
- Rationale: satisfies project requirement to avoid global mutable state and keeps behavior localized.

2. Timestamp-based effect expiration
- Rationale: deterministic timing independent of frame jitter and easier to test.

3. Single board power-up at a time (initial release)
- Rationale: reduces balancing complexity and UI clutter for first iteration.

4. Refresh-over-stack policy for same-type pickups
- Rationale: prevents runaway balance while rewarding pickup skill.

5. Minimal additive API changes
- Rationale: preserves existing game loop structure and lowers regression risk.

6. HUD-first feedback for readability
- Rationale: clear visibility of active effects is required by acceptance criteria.

## Risks and Mitigations

- Risk: speed boost can destabilize movement pacing.
  - Mitigation: enforce minimum tick threshold and clamp speed changes.

- Risk: invincibility logic can accidentally bypass all failure states permanently.
  - Mitigation: centralize expiry checks each tick and keep collision gate explicit.

- Risk: spawn overlap with snake/cash causing unfair pickups.
  - Mitigation: use strict free-cell generation with exclusion sets.

- Risk: UI updates drift from backend effect state.
  - Mitigation: render HUD directly from active_effects each frame.

## Traceability to Intent
- Intent AC1 (spawn/pickup): covered by Spawn Controller + collect_power_up_if_present contract.
- Intent AC2 (three effects): covered by PowerUpType and Effect Engine rules.
- Intent AC3 (timing lifecycle): covered by timestamp expiration and prune_expired_effects.
- Intent AC4 (rules interaction): covered in advance() updates and effect-specific gates.
- Intent AC5 (UI feedback): covered by HUD Feedback Layer and render_power_up_hud.
- Intent AC6 (stability): covered by SnakeCashRush-only state ownership and minimal API changes.
