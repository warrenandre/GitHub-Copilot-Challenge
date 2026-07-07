from __future__ import annotations

import json
from dataclasses import dataclass
from random import choice, randint
from typing import Iterable

from js import document, window  # type: ignore[import-not-found]
from pyodide.ffi import create_proxy  # type: ignore[import-not-found]


GRID_SIZE = 20
BOARD_CELLS = 20
BOARD_PIXELS = 560
BASE_TICK_MS = 160
MIN_TICK_MS = 82
SPEED_STEP_MS = 5
SCORE_PER_BILL = 10

# Power-up system defaults (Task 1: finalized gameplay rules and constants).
POWER_UP_TYPES = ("speed_boost", "invincibility", "double_points")
POWER_UP_DURATION_MS = {
    "speed_boost": 6000,
    "invincibility": 5000,
    "double_points": 8000,
}
POWER_UP_SPAWN_INTERVAL_MIN_MS = 5000
POWER_UP_SPAWN_INTERVAL_MAX_MS = 9000
POWER_UP_MAX_ON_BOARD = 1
POWER_UP_RECOLLECT_POLICY = "refresh_duration"
POWER_UP_INVINCIBILITY_POLICY = "ignore_lethal_collision"
POWER_UP_DOUBLE_POINTS_SCOPE = "cash_pickups_only"
SPEED_BOOST_TICK_MULTIPLIER = 0.7
SPEED_BOOST_MIN_TICK_MS = 60


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class PowerUp:
    power_up_type: str
    position: Point
    spawned_at_ms: float
    ttl_ms: int


class SnakeCashRush:
    def __init__(self) -> None:
        """Initialize game state, DOM bindings, event handlers, and debug hooks.

        Parameters:
            None.

        Returns:
            None.
        """
        self.canvas = document.getElementById("gameCanvas")
        self.ctx = self.canvas.getContext("2d")
        self.score_value = document.getElementById("scoreValue")
        self.best_score_value = document.getElementById("bestScoreValue")
        self.power_up_value = document.getElementById("powerUpValue")
        self.status_text = document.getElementById("statusText")
        self.start_button = document.getElementById("startButton")
        self.overlay = document.getElementById("gameOverlay")
        self.overlay_kicker = document.getElementById("overlayKicker")
        self.overlay_title = document.getElementById("overlayTitle")
        self.overlay_message = document.getElementById("overlayMessage")
        self.overlay_button = document.getElementById("overlayButton")
        self.cash_burst = document.getElementById("cashBurst")
        self.score_tile = self.score_value.parentElement
        self.best_score_tile = self.best_score_value.parentElement

        self.best_score = int(window.snakeCashRushBridge.readBestScore())
        self.score_value.textContent = "0"
        self.best_score_value.textContent = str(self.best_score)
        self.power_up_value.textContent = "None"

        self.last_frame_time = 0.0
        self.accumulator = 0.0
        self.animation_handle = None
        self.running = False
        self.game_over = False
        self.pending_restart = False

        self._key_proxy = create_proxy(self.handle_keydown)
        self._frame_proxy = create_proxy(self.game_frame)
        self._start_proxy = create_proxy(lambda _event: self.handle_primary_action())
        self._restart_proxy = create_proxy(lambda _event: self.restart_game())
        self._snapshot_proxy = create_proxy(lambda: self.snapshot_json())
        self._place_cash_proxy = create_proxy(lambda: self.place_cash_ahead())
        self._step_proxy = create_proxy(lambda: self.step_debug())

        document.addEventListener("keydown", self._key_proxy)
        self.start_button.addEventListener("click", self._start_proxy)
        self.overlay_button.addEventListener("click", self._restart_proxy)
        window.snakeCashRushSnapshot = self._snapshot_proxy
        window.snakeCashRushPlaceCashAhead = self._place_cash_proxy
        window.snakeCashRushStep = self._step_proxy

        self.reset_state()
        self.set_overlay(
            kicker="Ready to bank?",
            title="Press Start",
            message="Collect cash bills, dodge the walls, and keep the streak alive.",
            button_text="Play Now",
            visible=True,
        )
        self.draw()

    def reset_state(self) -> None:
        """Reset gameplay variables to a fresh, waiting-to-start run.

        Parameters:
            None.

        Returns:
            None.
        """
        center = BOARD_CELLS // 2
        self.snake = [Point(center, center + 1), Point(center, center), Point(center, center - 1)]
        self.direction = Point(0, -1)
        self.pending_direction = Point(0, -1)
        self.cash = self.spawn_cash(self.snake)
        self.score = 0
        self.tick_ms = BASE_TICK_MS
        self.base_tick_ms = BASE_TICK_MS
        self.initialize_power_up_state()
        self.accumulator = 0.0
        self.last_frame_time = 0.0
        self.running = False
        self.game_over = False
        self.score_value.textContent = str(self.score)
        self.status_text.textContent = "Waiting for your first run."

    def initialize_power_up_state(self) -> None:
        """Initialize power-up state for a fresh game lifecycle.

        Parameters:
            None.

        Returns:
            None.
        """
        self.current_power_up: PowerUp | None = None
        self.active_effects: dict[str, float] = {}
        self.next_power_up_spawn_at_ms: float = -1.0

    def schedule_next_power_up_spawn(self, now_ms: float) -> None:
        """Schedule the next eligible time for power-up spawning.

        Parameters:
            now_ms: Current game time in milliseconds.

        Returns:
            None.
        """
        delay = randint(POWER_UP_SPAWN_INTERVAL_MIN_MS, POWER_UP_SPAWN_INTERVAL_MAX_MS)
        self.next_power_up_spawn_at_ms = now_ms + float(delay)

    def spawn_power_up(self, excluded_cells: Iterable[Point], now_ms: float) -> PowerUp | None:
        """Create a power-up on a random free board cell.

        Parameters:
            excluded_cells: Cells that cannot be used for spawning.
            now_ms: Current game time in milliseconds.

        Returns:
            PowerUp | None: Spawned power-up data or None if no free cells are available.
        """
        occupied = set(excluded_cells)
        available = [
            Point(x, y)
            for y in range(BOARD_CELLS)
            for x in range(BOARD_CELLS)
            if Point(x, y) not in occupied
        ]
        if not available:
            return None

        power_up_type = choice(POWER_UP_TYPES)
        return PowerUp(
            power_up_type=power_up_type,
            position=choice(available),
            spawned_at_ms=now_ms,
            ttl_ms=POWER_UP_DURATION_MS[power_up_type],
        )

    def maybe_spawn_power_up(self, now_ms: float) -> None:
        """Spawn a power-up when spawn timing and board constraints allow.

        Parameters:
            now_ms: Current game time in milliseconds.

        Returns:
            None.
        """
        if POWER_UP_MAX_ON_BOARD < 1:
            return
        if self.current_power_up is not None:
            return

        if self.next_power_up_spawn_at_ms < 0:
            self.schedule_next_power_up_spawn(now_ms)
            return

        if now_ms < self.next_power_up_spawn_at_ms:
            return

        excluded_cells = set(self.snake)
        excluded_cells.add(self.cash)
        self.current_power_up = self.spawn_power_up(excluded_cells, now_ms)
        self.schedule_next_power_up_spawn(now_ms)

    def activate_effect(self, effect_type: str, now_ms: float) -> None:
        """Activate or refresh a timed effect.

        Parameters:
            effect_type: Effect identifier.
            now_ms: Current game time in milliseconds.

        Returns:
            None.
        """
        duration_ms = float(POWER_UP_DURATION_MS[effect_type])
        if POWER_UP_RECOLLECT_POLICY == "refresh_duration" or effect_type not in self.active_effects:
            self.active_effects[effect_type] = now_ms + duration_ms

    def collect_power_up_if_present(self, head: Point, now_ms: float) -> bool:
        """Collect a board power-up when the snake head reaches its position.

        Parameters:
            head: Snake head position after movement.
            now_ms: Current game time in milliseconds.

        Returns:
            bool: True when a power-up was collected, otherwise False.
        """
        if self.current_power_up is None:
            return False
        if head != self.current_power_up.position:
            return False

        self.activate_effect(self.current_power_up.power_up_type, now_ms)
        self.current_power_up = None
        self.schedule_next_power_up_spawn(now_ms)
        return True

    def prune_expired_effects(self, now_ms: float) -> None:
        """Remove effects that have passed their expiration time.

        Parameters:
            now_ms: Current game time in milliseconds.

        Returns:
            None.
        """
        expired = [effect for effect, ends_at in self.active_effects.items() if now_ms >= ends_at]
        for effect in expired:
            del self.active_effects[effect]

    def is_effect_active(self, effect_type: str, now_ms: float) -> bool:
        """Check whether an effect is currently active.

        Parameters:
            effect_type: Effect identifier.
            now_ms: Current game time in milliseconds.

        Returns:
            bool: True when the effect is active, otherwise False.
        """
        ends_at = self.active_effects.get(effect_type)
        return ends_at is not None and now_ms < ends_at

    def current_score_multiplier(self, now_ms: float) -> int:
        """Return the score multiplier from active effects.

        Parameters:
            now_ms: Current game time in milliseconds.

        Returns:
            int: 2 when double-points is active; otherwise 1.
        """
        if POWER_UP_DOUBLE_POINTS_SCOPE == "cash_pickups_only" and self.is_effect_active("double_points", now_ms):
            return 2
        return 1

    def compute_effective_tick_ms(self, now_ms: float) -> int:
        """Compute current tick speed after applying active effects.

        Parameters:
            now_ms: Current game time in milliseconds.

        Returns:
            int: Effective tick interval in milliseconds.
        """
        tick_ms = self.base_tick_ms
        if self.is_effect_active("speed_boost", now_ms):
            boosted = int(self.base_tick_ms * SPEED_BOOST_TICK_MULTIPLIER)
            tick_ms = max(SPEED_BOOST_MIN_TICK_MS, boosted)
        return tick_ms

    def start_game(self) -> None:
        """Start a run if idle, or reset first when currently in game-over state.

        Parameters:
            None.

        Returns:
            None.
        """
        if self.running:
            return
        if self.game_over:
            self.reset_state()
        self.running = True
        self.game_over = False
        self.pending_restart = False
        self.last_frame_time = 0.0
        self.accumulator = 0.0
        self.status_text.textContent = "Live run. Stay sharp and keep stacking."
        self.start_button.textContent = "Restart Run"
        self.set_overlay(visible=False)
        self.ensure_animation()

    def handle_primary_action(self) -> None:
        """Handle primary button behavior by starting or restarting the game.

        Parameters:
            None.

        Returns:
            None.
        """
        if self.running or self.game_over:
            self.restart_game()
            return
        self.start_game()

    def restart_game(self) -> None:
        """Restart the run by stopping animation, resetting state, and starting again.

        Parameters:
            None.

        Returns:
            None.
        """
        self.cancel_animation()
        self.reset_state()
        self.start_game()

    def ensure_animation(self) -> None:
        """Ensure a requestAnimationFrame callback is scheduled when absent.

        Parameters:
            None.

        Returns:
            None.
        """
        if self.animation_handle is None:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def cancel_animation(self) -> None:
        """Cancel the active animation frame callback if one is scheduled.

        Parameters:
            None.

        Returns:
            None.
        """
        if self.animation_handle is not None:
            window.snakeCashRushBridge.cancelRaf(self.animation_handle)
            self.animation_handle = None

    def set_overlay(
        self,
        kicker: str | None = None,
        title: str | None = None,
        message: str | None = None,
        button_text: str | None = None,
        visible: bool | None = None,
    ) -> None:
        """Update overlay text fields and optionally toggle its visibility.

        Parameters:
            kicker: Optional small heading text shown above the overlay title.
            title: Optional overlay title text.
            message: Optional descriptive overlay body text.
            button_text: Optional text for the overlay action button.
            visible: Optional visibility flag; True shows and False hides the overlay.

        Returns:
            None.
        """
        if kicker is not None:
            self.overlay_kicker.textContent = kicker
        if title is not None:
            self.overlay_title.textContent = title
        if message is not None:
            self.overlay_message.textContent = message
        if button_text is not None:
            self.overlay_button.textContent = button_text
        if visible is True:
            self.overlay.classList.add("visible")
        elif visible is False:
            self.overlay.classList.remove("visible")

    def handle_keydown(self, event) -> None:
        """Handle keyboard input for movement and restart actions.

        Parameters:
            event: Browser keyboard event containing the pressed key.

        Returns:
            None.
        """
        key = str(event.key).lower()
        if key == "r":
            self.restart_game()
            return

        next_direction = {
            "arrowup": Point(0, -1),
            "w": Point(0, -1),
            "arrowdown": Point(0, 1),
            "s": Point(0, 1),
            "arrowleft": Point(-1, 0),
            "a": Point(-1, 0),
            "arrowright": Point(1, 0),
            "d": Point(1, 0),
        }.get(key)

        if next_direction is None:
            return

        if not self.running and not self.game_over:
            self.start_game()

        if self.is_reverse(next_direction, self.direction):
            return

        self.pending_direction = next_direction

    def is_reverse(self, next_direction: Point, current_direction: Point) -> bool:
        """Determine whether a candidate direction is the exact reverse of current movement.

        Parameters:
            next_direction: Proposed next direction vector.
            current_direction: Current direction vector.

        Returns:
            bool: True when next_direction directly opposes current_direction, else False.
        """
        return next_direction.x == -current_direction.x and next_direction.y == -current_direction.y

    def game_frame(self, timestamp) -> None:
        """Process one animation frame and advance game ticks based on elapsed time.

        Parameters:
            timestamp: High-resolution frame timestamp from requestAnimationFrame.

        Returns:
            None.
        """
        self.animation_handle = None

        if not self.running:
            self.draw()
            return

        if self.last_frame_time == 0.0:
            self.last_frame_time = float(timestamp)

        frame_delta = float(timestamp) - self.last_frame_time
        self.last_frame_time = float(timestamp)
        self.accumulator += frame_delta
        self.prune_expired_effects(self.last_frame_time)
        self.maybe_spawn_power_up(self.last_frame_time)

        while self.running:
            self.tick_ms = self.compute_effective_tick_ms(self.last_frame_time)
            if self.accumulator < self.tick_ms:
                break
            self.accumulator -= self.tick_ms
            self.advance(self.last_frame_time)

        self.draw()

        if self.running:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def advance(self, now_ms: float | None = None) -> None:
        """Advance the game by one logical tick, including movement and collisions.

        Parameters:
            None.

        Returns:
            None.
        """
        if now_ms is None:
            now_ms = self.last_frame_time

        self.prune_expired_effects(now_ms)
        self.direction = self.pending_direction
        head = self.snake[-1]
        next_head = Point(head.x + self.direction.x, head.y + self.direction.y)
        will_collect = next_head == self.cash
        collision_body = self.snake if will_collect else self.snake[1:]

        if self.hit_wall(next_head) or next_head in collision_body:
            self.end_game()
            return

        self.snake.append(next_head)
        self.collect_power_up_if_present(next_head, now_ms)

        if will_collect:
            self.score += SCORE_PER_BILL * self.current_score_multiplier(now_ms)
            self.base_tick_ms = max(MIN_TICK_MS, BASE_TICK_MS - (self.score // SCORE_PER_BILL) * SPEED_STEP_MS)
            self.tick_ms = self.compute_effective_tick_ms(now_ms)
            self.cash = self.spawn_cash(self.snake)
            self.flash_score()
            self.show_cash_burst()
            self.sync_best_score()
            self.status_text.textContent = f"Banked ${self.score}. Pace is picking up."
        else:
            self.snake.pop(0)

        self.score_value.textContent = str(self.score)

    def hit_wall(self, point: Point) -> bool:
        """Check whether a point lies outside the playable board bounds.

        Parameters:
            point: Board coordinate to test.

        Returns:
            bool: True if the point is out of bounds; otherwise False.
        """
        return point.x < 0 or point.y < 0 or point.x >= BOARD_CELLS or point.y >= BOARD_CELLS

    def spawn_cash(self, snake: Iterable[Point]) -> Point:
        """Spawn a cash pickup on a random unoccupied board cell.

        Parameters:
            snake: Iterable of snake segment positions currently occupying cells.

        Returns:
            Point: Random available cell for cash, or (0, 0) if no cells are free.
        """
        occupied = set(snake)
        available = [
            Point(x, y)
            for y in range(BOARD_CELLS)
            for x in range(BOARD_CELLS)
            if Point(x, y) not in occupied
        ]
        return choice(available) if available else Point(0, 0)

    def sync_best_score(self) -> None:
        """Persist and animate best-score updates when current score exceeds the record.

        Parameters:
            None.

        Returns:
            None.
        """
        if self.score <= self.best_score:
            return
        self.best_score = self.score
        self.best_score_value.textContent = str(self.best_score)
        self.best_score_tile.classList.add("pulse")
        window.snakeCashRushBridge.writeBestScore(self.best_score)
        window.setTimeout(create_proxy(lambda: self.best_score_tile.classList.remove("pulse")), 240)

    def flash_score(self) -> None:
        """Apply a short pulse animation to score tiles after collecting cash.

        Parameters:
            None.

        Returns:
            None.
        """
        self.score_tile.classList.remove("pulse")
        self.best_score_tile.classList.remove("pulse")
        self.score_tile.classList.add("pulse")
        window.setTimeout(create_proxy(lambda: self.score_tile.classList.remove("pulse")), 240)

    def show_cash_burst(self) -> None:
        """Display a brief on-board visual burst to indicate cash collection.

        Parameters:
            None.

        Returns:
            None.
        """
        self.cash_burst.classList.remove("visible")

        def trigger() -> None:
            self.cash_burst.classList.add("visible")

        def cleanup() -> None:
            self.cash_burst.classList.remove("visible")

        window.setTimeout(create_proxy(trigger), 10)
        window.setTimeout(create_proxy(cleanup), 460)

    def end_game(self) -> None:
        """Transition the game into game-over state and show restart overlay messaging.

        Parameters:
            None.

        Returns:
            None.
        """
        self.running = False
        self.game_over = True
        self.status_text.textContent = f"Run over at ${self.score}. Tap restart and chase a higher stack."
        self.set_overlay(
            kicker="Run complete",
            title="Crash Out",
            message=f"You stacked ${self.score}. Reload the board and try to top ${self.best_score}.",
            button_text="Run It Back",
            visible=True,
        )
        self.draw()

    def draw(self) -> None:
        """Render the full frame by drawing board, cash pickup, and snake.

        Parameters:
            None.

        Returns:
            None.
        """
        ctx = self.ctx
        ctx.clearRect(0, 0, BOARD_PIXELS, BOARD_PIXELS)
        self.draw_board(ctx)
        self.draw_cash(ctx)
        self.draw_power_up(ctx)
        self.draw_snake(ctx)
        self.render_power_up_hud(self.last_frame_time)

    def render_power_up_hud(self, now_ms: float) -> None:
        """Render active power-up statuses and remaining durations in the HUD.

        Parameters:
            now_ms: Current game time in milliseconds.

        Returns:
            None.
        """
        if not self.active_effects and self.current_power_up is None:
            self.power_up_value.textContent = "None"
            return

        label_map = {
            "speed_boost": "Speed",
            "invincibility": "Shield",
            "double_points": "2x",
        }

        parts: list[str] = []
        for effect, ends_at in sorted(self.active_effects.items()):
            seconds_left = max(0, int((ends_at - now_ms + 999) // 1000))
            parts.append(f"{label_map.get(effect, effect)} {seconds_left}s")

        if self.current_power_up is not None:
            board_label = label_map.get(self.current_power_up.power_up_type, self.current_power_up.power_up_type)
            parts.append(f"Board: {board_label}")

        self.power_up_value.textContent = " | ".join(parts)

    def draw_power_up(self, ctx) -> None:
        """Draw active board power-up if one is currently spawned.

        Parameters:
            ctx: Canvas 2D rendering context used for drawing operations.

        Returns:
            None.
        """
        if self.current_power_up is None:
            return

        cell = BOARD_PIXELS / BOARD_CELLS
        x = self.current_power_up.position.x * cell + cell / 2
        y = self.current_power_up.position.y * cell + cell / 2
        radius = cell * 0.24
        colors = {
            "speed_boost": "#79d6ff",
            "invincibility": "#ff91b8",
            "double_points": "#ffe08a",
        }
        fill_color = colors.get(self.current_power_up.power_up_type, "#ffffff")

        ctx.save()
        ctx.shadowColor = fill_color
        ctx.shadowBlur = 14
        ctx.fillStyle = fill_color
        ctx.beginPath()
        ctx.arc(x, y, radius, 0, 6.283)
        ctx.fill()
        ctx.restore()

    def draw_board(self, ctx) -> None:
        """Draw the board background and grid lines onto the canvas context.

        Parameters:
            ctx: Canvas 2D rendering context used for drawing operations.

        Returns:
            None.
        """
        ctx.fillStyle = "#07141d"
        ctx.fillRect(0, 0, BOARD_PIXELS, BOARD_PIXELS)

        ctx.strokeStyle = "rgba(151, 183, 163, 0.08)"
        ctx.lineWidth = 1
        for index in range(BOARD_CELLS + 1):
            offset = index * GRID_SIZE + index * (BOARD_PIXELS / BOARD_CELLS - GRID_SIZE)
            position = index * (BOARD_PIXELS / BOARD_CELLS)
            ctx.beginPath()
            ctx.moveTo(position, 0)
            ctx.lineTo(position, BOARD_PIXELS)
            ctx.stroke()
            ctx.beginPath()
            ctx.moveTo(0, position)
            ctx.lineTo(BOARD_PIXELS, position)
            ctx.stroke()

    def draw_cash(self, ctx) -> None:
        """Draw the cash pickup tile with glow and symbol styling.

        Parameters:
            ctx: Canvas 2D rendering context used for drawing operations.

        Returns:
            None.
        """
        px = self.cash.x * GRID_SIZE * 1.4
        py = self.cash.y * GRID_SIZE * 1.4
        cell = BOARD_PIXELS / BOARD_CELLS
        x = self.cash.x * cell + 4
        y = self.cash.y * cell + 7
        width = cell - 8
        height = cell - 14

        ctx.save()
        ctx.shadowColor = "rgba(103, 247, 160, 0.42)"
        ctx.shadowBlur = 16
        ctx.fillStyle = "#66f5a1"
        round_rect(ctx, x, y, width, height, 7)
        ctx.fill()
        ctx.fillStyle = "#0d512f"
        ctx.font = "700 12px Space Grotesk"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.fillText("$", x + width / 2, y + height / 2 + 0.5)
        ctx.restore()

    def draw_snake(self, ctx) -> None:
        """Draw snake segments and head details for the current game state.

        Parameters:
            ctx: Canvas 2D rendering context used for drawing operations.

        Returns:
            None.
        """
        cell = BOARD_PIXELS / BOARD_CELLS
        for index, segment in enumerate(self.snake):
            inset = 3
            x = segment.x * cell + inset
            y = segment.y * cell + inset
            size = cell - inset * 2
            is_head = index == len(self.snake) - 1

            ctx.save()
            ctx.fillStyle = "#1fce74" if not is_head else "#a9ffcb"
            ctx.shadowColor = "rgba(103, 247, 160, 0.35)"
            ctx.shadowBlur = 14 if is_head else 8
            round_rect(ctx, x, y, size, size, 9)
            ctx.fill()

            if is_head:
                eye_y = y + size * 0.38
                ctx.fillStyle = "#063720"
                ctx.beginPath()
                ctx.arc(x + size * 0.34, eye_y, 2.1, 0, 6.283)
                ctx.arc(x + size * 0.66, eye_y, 2.1, 0, 6.283)
                ctx.fill()
            ctx.restore()

    def snapshot_json(self) -> str:
        """Serialize key runtime state into a JSON snapshot for debugging hooks.

        Parameters:
            None.

        Returns:
            str: JSON string describing game state, score, direction, cash, and snake.
        """
        payload = {
            "running": self.running,
            "gameOver": self.game_over,
            "score": self.score,
            "bestScore": self.best_score,
            "tickMs": self.tick_ms,
            "activeEffects": self.active_effects,
            "powerUp": (
                {
                    "type": self.current_power_up.power_up_type,
                    "x": self.current_power_up.position.x,
                    "y": self.current_power_up.position.y,
                    "ttlMs": self.current_power_up.ttl_ms,
                }
                if self.current_power_up is not None
                else None
            ),
            "direction": {"x": self.direction.x, "y": self.direction.y},
            "cash": {"x": self.cash.x, "y": self.cash.y},
            "snake": [{"x": segment.x, "y": segment.y} for segment in self.snake],
        }
        return json.dumps(payload)

    def place_cash_ahead(self) -> None:
        """Move cash to a nearby reachable cell, primarily for debugging and demos.

        Parameters:
            None.

        Returns:
            None.
        """
        head = self.snake[-1]
        candidates = [
            Point(head.x + self.direction.x, head.y + self.direction.y),
            Point(head.x + 1, head.y),
            Point(head.x - 1, head.y),
            Point(head.x, head.y + 1),
            Point(head.x, head.y - 1),
        ]

        for point in candidates:
            if self.hit_wall(point) or point in self.snake:
                continue
            self.cash = point
            self.draw()
            return

    def step_debug(self) -> None:
        """Advance exactly one game tick for deterministic debugging.

        Parameters:
            None.

        Returns:
            None.
        """
        if self.game_over:
            return
        self.running = True
        self.advance(self.last_frame_time)
        self.draw()

    def destroy(self) -> None:
        """Clean up animation and keyboard listeners before teardown.

        Parameters:
            None.

        Returns:
            None.
        """
        self.cancel_animation()
        document.removeEventListener("keydown", self._key_proxy)


def round_rect(ctx, x: float, y: float, width: float, height: float, radius: float) -> None:
    """Create a rounded-rectangle path on a canvas context.

    Parameters:
        ctx: Canvas 2D rendering context used for path commands.
        x: Left coordinate of the rectangle.
        y: Top coordinate of the rectangle.
        width: Rectangle width in pixels.
        height: Rectangle height in pixels.
        radius: Corner radius in pixels.

    Returns:
        None.
    """
    ctx.beginPath()
    ctx.moveTo(x + radius, y)
    ctx.lineTo(x + width - radius, y)
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius)
    ctx.lineTo(x + width, y + height - radius)
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height)
    ctx.lineTo(x + radius, y + height)
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius)
    ctx.lineTo(x, y + radius)
    ctx.quadraticCurveTo(x, y, x + radius, y)
    ctx.closePath()


game = SnakeCashRush()