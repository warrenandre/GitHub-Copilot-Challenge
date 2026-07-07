from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from random import choice, uniform
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

POWERUP_DURATION_MS: float = 6000.0
POWERUP_SPAWN_MIN_MS: float = 8000.0
POWERUP_SPAWN_MAX_MS: float = 15000.0
POWERUP_DESPAWN_MS: float = 10000.0


class PowerUpType(Enum):
    """Types of power-ups available in the game."""

    DOUBLE_POINTS = "double_points"
    INVINCIBILITY = "invincibility"


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class PowerUp:
    """A power-up item on the game board.

    Args:
        position: Grid cell where the power-up is located.
        kind: The type of power-up effect.
    """

    position: Point
    kind: PowerUpType


class SnakeCashRush:
    """Main game controller for Snake Cash Rush.

    Manages game state, rendering, input handling, and the animation loop
    for a browser-based snake game powered by PyScript.
    """

    def __init__(self) -> None:
        """Initialize the game by binding DOM elements, setting up event listeners,
        and preparing the initial game state and overlay."""
        self.canvas = document.getElementById("gameCanvas")
        self.ctx = self.canvas.getContext("2d")
        self.score_value = document.getElementById("scoreValue")
        self.best_score_value = document.getElementById("bestScoreValue")
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
        """Reset all game state to initial values.

        Places the snake in the center of the board facing up, spawns a new
        cash pickup, and resets the score and tick speed.
        """
        center = BOARD_CELLS // 2
        self.snake = [Point(center, center + 1), Point(center, center), Point(center, center - 1)]
        self.direction = Point(0, -1)
        self.pending_direction = Point(0, -1)

        # Power-up state (must be set before spawn_cash which checks self.powerup)
        self.powerup: PowerUp | None = None
        self.powerup_age_ms: float = 0.0
        self.active_effect: PowerUpType | None = None
        self.effect_remaining_ms: float = 0.0
        self.spawn_timer_ms: float = 0.0
        self.next_spawn_delay_ms: float = uniform(POWERUP_SPAWN_MIN_MS, POWERUP_SPAWN_MAX_MS)

        self.cash = self.spawn_cash(self.snake)
        self.score = 0
        self.tick_ms = BASE_TICK_MS
        self.accumulator = 0.0
        self.last_frame_time = 0.0
        self.running = False
        self.game_over = False

        self.score_value.textContent = str(self.score)
        self.status_text.textContent = "Waiting for your first run."

    def start_game(self) -> None:
        """Start the game loop.

        If the game is already running, does nothing. If the previous run ended
        in game-over, resets state before starting.
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
        """Handle the primary UI action (Start/Restart button click).

        Restarts if a game is active or over; otherwise starts a new game.
        """
        if self.running or self.game_over:
            self.restart_game()
            return
        self.start_game()

    def restart_game(self) -> None:
        """Cancel the current animation loop, reset state, and start a fresh game."""
        self.cancel_animation()
        self.reset_state()
        self.start_game()

    def ensure_animation(self) -> None:
        """Request the next animation frame if one is not already scheduled."""
        if self.animation_handle is None:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def cancel_animation(self) -> None:
        """Cancel any pending animation frame request."""
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
        """Update the game overlay card content and visibility.

        Args:
            kicker: Small text above the title (e.g. "Ready to bank?").
            title: Main heading text.
            message: Body paragraph text.
            button_text: Label for the overlay action button.
            visible: If True show the overlay, if False hide it, if None leave unchanged.
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
        """Process keyboard input for direction changes and restart.

        Args:
            event: A DOM KeyboardEvent.
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
        """Check whether a proposed direction is a 180-degree reversal.

        Args:
            next_direction: The candidate direction vector.
            current_direction: The current travel direction vector.

        Returns:
            True if next_direction is the exact opposite of current_direction.
        """
        return next_direction.x == -current_direction.x and next_direction.y == -current_direction.y

    def game_frame(self, timestamp) -> None:
        """Main animation loop callback driven by requestAnimationFrame.

        Accumulates elapsed time and advances the game in fixed tick intervals,
        then redraws the board.

        Args:
            timestamp: High-resolution timestamp in milliseconds from the browser.
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

        # Power-up spawn timer
        self.spawn_timer_ms += frame_delta
        if self.powerup is None and self.spawn_timer_ms >= self.next_spawn_delay_ms:
            self.spawn_powerup()
            self.spawn_timer_ms = 0.0
            self.next_spawn_delay_ms = uniform(POWERUP_SPAWN_MIN_MS, POWERUP_SPAWN_MAX_MS)

        # Power-up despawn
        if self.powerup is not None:
            self.powerup_age_ms += frame_delta
            if self.powerup_age_ms >= POWERUP_DESPAWN_MS:
                self.powerup = None
                self.powerup_age_ms = 0.0

        # Effect countdown
        if self.active_effect is not None:
            self.effect_remaining_ms -= frame_delta
            if self.effect_remaining_ms <= 0.0:
                self.expire_effect()

        while self.accumulator >= self.tick_ms and self.running:
          self.accumulator -= self.tick_ms
          self.advance()

        self.draw()

        if self.running:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def advance(self) -> None:
        """Advance the game by one logical tick.

        Moves the snake one cell in the current direction, checks for collisions,
        handles cash collection (growing the snake and increasing speed), and
        ends the game on collision.
        """
        self.direction = self.pending_direction
        head = self.snake[-1]
        next_head = Point(head.x + self.direction.x, head.y + self.direction.y)
        will_collect = next_head == self.cash
        collision_body = self.snake if will_collect else self.snake[1:]

        # Wall collision is always fatal
        if self.hit_wall(next_head):
            self.end_game()
            return

        # Body collision — skip if invincible
        if next_head in collision_body:
            if self.active_effect != PowerUpType.INVINCIBILITY:
                self.end_game()
                return

        self.snake.append(next_head)

        # Check power-up collection
        if self.powerup is not None and next_head == self.powerup.position:
            self.collect_powerup()

        if will_collect:
            multiplier = 2 if self.active_effect == PowerUpType.DOUBLE_POINTS else 1
            self.score += SCORE_PER_BILL * multiplier
            self.tick_ms = max(MIN_TICK_MS, BASE_TICK_MS - (self.score // SCORE_PER_BILL) * SPEED_STEP_MS)
            self.cash = self.spawn_cash(self.snake)
            self.flash_score()
            self.show_cash_burst()
            self.sync_best_score()
            self.status_text.textContent = f"Banked ${self.score}. Pace is picking up."
        else:
            self.snake.pop(0)

        self.score_value.textContent = str(self.score)

    def hit_wall(self, point: Point) -> bool:
        """Check whether a point is outside the game board boundaries.

        Args:
            point: The grid coordinate to test.

        Returns:
            True if the point is out of bounds.
        """
        return point.x < 0 or point.y < 0 or point.x >= BOARD_CELLS or point.y >= BOARD_CELLS

    def spawn_cash(self, snake: Iterable[Point]) -> Point:
        """Choose a random unoccupied cell for the next cash pickup.

        Args:
            snake: The current snake body segments to exclude.

        Returns:
            A Point representing the chosen grid cell for the cash bill.
        """
        occupied = set(snake)
        if self.powerup is not None:
            occupied.add(self.powerup.position)
        available = [
            Point(x, y)
            for y in range(BOARD_CELLS)
            for x in range(BOARD_CELLS)
            if Point(x, y) not in occupied
        ]
        return choice(available) if available else Point(0, 0)

    def spawn_powerup(self) -> None:
        """Spawn a random power-up on an unoccupied cell."""
        occupied = set(self.snake)
        occupied.add(self.cash)
        kind = choice(list(PowerUpType))
        available = [
            Point(x, y)
            for y in range(BOARD_CELLS)
            for x in range(BOARD_CELLS)
            if Point(x, y) not in occupied
        ]
        if available:
            self.powerup = PowerUp(position=choice(available), kind=kind)
            self.powerup_age_ms = 0.0

    def collect_powerup(self) -> None:
        """Activate the collected power-up's effect and clear it from the board."""
        if self.powerup is None:
            return
        self.active_effect = self.powerup.kind
        self.effect_remaining_ms = POWERUP_DURATION_MS
        self.powerup = None
        self.powerup_age_ms = 0.0
        self.spawn_timer_ms = 0.0
        self.next_spawn_delay_ms = uniform(POWERUP_SPAWN_MIN_MS, POWERUP_SPAWN_MAX_MS)

    def expire_effect(self) -> None:
        """Clear the active power-up effect."""
        self.active_effect = None
        self.effect_remaining_ms = 0.0

    def sync_best_score(self) -> None:
        """Persist the best score to localStorage if the current score exceeds it."""
        if self.score <= self.best_score:
            return
        self.best_score = self.score
        self.best_score_value.textContent = str(self.best_score)
        self.best_score_tile.classList.add("pulse")
        window.snakeCashRushBridge.writeBestScore(self.best_score)
        window.setTimeout(create_proxy(lambda: self.best_score_tile.classList.remove("pulse")), 240)

    def flash_score(self) -> None:
        """Trigger a brief CSS pulse animation on the score tile."""
        self.score_tile.classList.remove("pulse")
        self.best_score_tile.classList.remove("pulse")
        self.score_tile.classList.add("pulse")
        window.setTimeout(create_proxy(lambda: self.score_tile.classList.remove("pulse")), 240)

    def show_cash_burst(self) -> None:
        """Display and auto-dismiss the '+$' burst animation element."""
        self.cash_burst.classList.remove("visible")

        def trigger() -> None:
            self.cash_burst.classList.add("visible")

        def cleanup() -> None:
            self.cash_burst.classList.remove("visible")

        window.setTimeout(create_proxy(trigger), 10)
        window.setTimeout(create_proxy(cleanup), 460)

    def end_game(self) -> None:
        """End the current run, show the game-over overlay with final score."""
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
        """Clear the canvas and redraw the board, cash pickup, power-up, snake, and HUD."""
        ctx = self.ctx
        ctx.clearRect(0, 0, BOARD_PIXELS, BOARD_PIXELS)
        self.draw_board(ctx)
        self.draw_cash(ctx)
        self.draw_powerup(ctx)
        self.draw_snake(ctx)
        self.draw_effect_bar(ctx)

    def draw_board(self, ctx) -> None:
        """Render the dark background and subtle grid lines.

        Args:
            ctx: The 2D canvas rendering context.
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
        """Render the cash bill pickup as a glowing green rectangle with a '$' symbol.

        Args:
            ctx: The 2D canvas rendering context.
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

    def draw_powerup(self, ctx) -> None:
        """Render the power-up item on the board if one exists.

        Args:
            ctx: The 2D canvas rendering context.
        """
        if self.powerup is None:
            return
        cell = BOARD_PIXELS / BOARD_CELLS
        x = self.powerup.position.x * cell + 4
        y = self.powerup.position.y * cell + 4
        size = cell - 8

        if self.powerup.kind == PowerUpType.DOUBLE_POINTS:
            color = "#ffd700"
            shadow = "rgba(255, 215, 0, 0.5)"
            icon = "2x"
        else:
            color = "#00e5ff"
            shadow = "rgba(0, 229, 255, 0.5)"
            icon = "\u26a1"

        ctx.save()
        ctx.shadowColor = shadow
        ctx.shadowBlur = 18
        ctx.fillStyle = color
        round_rect(ctx, x, y, size, size, 10)
        ctx.fill()
        ctx.fillStyle = "#000000"
        ctx.font = "700 11px Space Grotesk"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.fillText(icon, x + size / 2, y + size / 2 + 0.5)
        ctx.restore()

    def draw_effect_bar(self, ctx) -> None:
        """Render a horizontal timer bar showing remaining power-up duration.

        Args:
            ctx: The 2D canvas rendering context.
        """
        if self.active_effect is None:
            return
        bar_width = BOARD_PIXELS - 20
        bar_height = 6
        bar_x = 10
        bar_y = BOARD_PIXELS - 14
        fraction = max(0.0, self.effect_remaining_ms / POWERUP_DURATION_MS)

        if self.active_effect == PowerUpType.DOUBLE_POINTS:
            color = "#ffd700"
        else:
            color = "#00e5ff"

        ctx.save()
        ctx.fillStyle = "rgba(255, 255, 255, 0.1)"
        round_rect(ctx, bar_x, bar_y, bar_width, bar_height, 3)
        ctx.fill()
        ctx.fillStyle = color
        round_rect(ctx, bar_x, bar_y, bar_width * fraction, bar_height, 3)
        ctx.fill()
        ctx.restore()

    def get_snake_color(self, is_head: bool) -> str:
        """Return the snake segment color based on active power-up effect.

        Args:
            is_head: Whether the segment is the head.

        Returns:
            A CSS color string.
        """
        if self.active_effect == PowerUpType.DOUBLE_POINTS:
            return "#ffe566" if not is_head else "#fff2a8"
        if self.active_effect == PowerUpType.INVINCIBILITY:
            return "#00c8e0" if not is_head else "#80f0ff"
        return "#1fce74" if not is_head else "#a9ffcb"

    def get_snake_glow(self) -> str:
        """Return the snake glow color based on active power-up effect.

        Returns:
            A CSS rgba color string.
        """
        if self.active_effect == PowerUpType.DOUBLE_POINTS:
            return "rgba(255, 215, 0, 0.4)"
        if self.active_effect == PowerUpType.INVINCIBILITY:
            return "rgba(0, 229, 255, 0.4)"
        return "rgba(103, 247, 160, 0.35)"

    def draw_snake(self, ctx) -> None:
        """Render all snake segments with glow effects and eyes on the head.

        Args:
            ctx: The 2D canvas rendering context.
        """
        cell = BOARD_PIXELS / BOARD_CELLS
        glow_color = self.get_snake_glow()
        for index, segment in enumerate(self.snake):
            inset = 3
            x = segment.x * cell + inset
            y = segment.y * cell + inset
            size = cell - inset * 2
            is_head = index == len(self.snake) - 1

            ctx.save()
            ctx.fillStyle = self.get_snake_color(is_head)
            ctx.shadowColor = glow_color
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
        """Serialize the current game state to a JSON string.

        Returns:
            A JSON string containing running state, score, direction, cash
            position, and all snake segment coordinates.
        """
        payload = {
            "running": self.running,
            "gameOver": self.game_over,
            "score": self.score,
            "bestScore": self.best_score,
            "tickMs": self.tick_ms,
            "direction": {"x": self.direction.x, "y": self.direction.y},
            "cash": {"x": self.cash.x, "y": self.cash.y},
            "snake": [{"x": segment.x, "y": segment.y} for segment in self.snake],
            "powerup": (
                {"x": self.powerup.position.x, "y": self.powerup.position.y, "kind": self.powerup.kind.value}
                if self.powerup is not None
                else None
            ),
            "activeEffect": self.active_effect.value if self.active_effect is not None else None,
            "effectRemainingMs": self.effect_remaining_ms,
        }
        return json.dumps(payload)

    def place_cash_ahead(self) -> None:
        """Debug helper: place the cash pickup directly ahead of the snake head.

        Tries the cell immediately in front first, then adjacent cells.
        Used for testing collection logic without waiting for random placement.
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
        """Debug helper: advance the game by exactly one tick and redraw.

        Does nothing if the game is already over.
        """
        if self.game_over:
            return
        self.running = True
        self.advance()
        self.draw()

    def destroy(self) -> None:
        """Clean up event listeners and cancel any pending animation frame."""
        self.cancel_animation()
        document.removeEventListener("keydown", self._key_proxy)


def round_rect(ctx, x: float, y: float, width: float, height: float, radius: float) -> None:
    """Draw a rounded rectangle path on the canvas context.

    Args:
        ctx: The 2D canvas rendering context.
        x: The x-coordinate of the top-left corner.
        y: The y-coordinate of the top-left corner.
        width: The rectangle width in pixels.
        height: The rectangle height in pixels.
        radius: The corner radius in pixels.
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