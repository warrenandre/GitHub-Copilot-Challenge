from __future__ import annotations

import json
from dataclasses import dataclass
from random import choice, random
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
POWER_UP_DURATION_MS = 7000
POWER_UP_SPAWN_CHANCE = 0.09
SPEED_BOOST_MULTIPLIER = 0.72
MIN_SPEED_BOOST_TICK_MS = 58

POWER_UP_SPEED = "speed_boost"
POWER_UP_INVINCIBLE = "invincibility"
POWER_UP_DOUBLE_POINTS = "double_points"
POWER_UP_TYPES = (POWER_UP_SPEED, POWER_UP_INVINCIBLE, POWER_UP_DOUBLE_POINTS)

POWER_UP_LABELS = {
    POWER_UP_SPEED: "Speed",
    POWER_UP_INVINCIBLE: "Shield",
    POWER_UP_DOUBLE_POINTS: "2x Points",
}

POWER_UP_COLORS = {
    POWER_UP_SPEED: ("#7dc2ff", "rgba(125, 194, 255, 0.52)", "#103451", "⚡"),
    POWER_UP_INVINCIBLE: ("#c98aff", "rgba(201, 138, 255, 0.5)", "#33114f", "🛡"),
    POWER_UP_DOUBLE_POINTS: ("#ffe08a", "rgba(255, 224, 138, 0.48)", "#5b4706", "2x"),
}


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class PowerUp:
    kind: str
    position: Point


class SnakeCashRush:
    def __init__(self) -> None:
        """Initialize the game and wire browser event handlers.

        Args:
            None.

        Returns:
            None.
        """
        self.canvas = document.getElementById("gameCanvas")
        self.ctx = self.canvas.getContext("2d")
        self.score_value = document.getElementById("scoreValue")
        self.best_score_value = document.getElementById("bestScoreValue")
        self.status_text = document.getElementById("statusText")
        self.power_up_status = document.getElementById("powerUpStatus")
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
        """Reset all game state for a new run.

        Args:
            None.

        Returns:
            None.
        """
        center = BOARD_CELLS // 2
        self.snake = [Point(center, center + 1), Point(center, center), Point(center, center - 1)]
        self.direction = Point(0, -1)
        self.pending_direction = Point(0, -1)
        self.cash = self.spawn_cash(self.snake)
        self.power_up: PowerUp | None = None
        self.effect_timers_ms: dict[str, int] = {kind: 0 for kind in POWER_UP_TYPES}
        self.score = 0
        self.tick_ms = BASE_TICK_MS
        self.accumulator = 0.0
        self.last_frame_time = 0.0
        self.running = False
        self.game_over = False
        self.score_value.textContent = str(self.score)
        self.status_text.textContent = "Waiting for your first run."
        if self.power_up_status is not None:
            self.power_up_status.textContent = "No active power-ups"

    def start_game(self) -> None:
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
        if self.running or self.game_over:
            self.restart_game()
            return
        self.start_game()

    def restart_game(self) -> None:
        self.cancel_animation()
        self.reset_state()
        self.start_game()

    def ensure_animation(self) -> None:
        if self.animation_handle is None:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def cancel_animation(self) -> None:
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
        return next_direction.x == -current_direction.x and next_direction.y == -current_direction.y

    def game_frame(self, timestamp) -> None:
        """Run one animation frame and process pending game ticks.

        Args:
            timestamp: Browser RAF timestamp for timing updates.

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
        self.tick_ms = self.compute_tick_ms()

        while self.accumulator >= self.tick_ms and self.running:
            self.accumulator -= self.tick_ms
            self.advance()
            self.tick_ms = self.compute_tick_ms()

        self.draw()

        if self.running:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def advance(self) -> None:
        """Advance the game by one simulation tick.

        Args:
            None.

        Returns:
            None.
        """
        self.update_effect_timers(self.tick_ms)
        self.direction = self.pending_direction
        head = self.snake[-1]
        next_head = self.resolve_next_head(head)
        will_collect = next_head == self.cash
        collision_body = self.snake if will_collect else self.snake[1:]

        has_collision = self.hit_wall(next_head) or next_head in collision_body
        if has_collision and not self.has_effect(POWER_UP_INVINCIBLE):
            self.end_game()
            return

        self.snake.append(next_head)

        if will_collect:
            cash_points = SCORE_PER_BILL * (2 if self.has_effect(POWER_UP_DOUBLE_POINTS) else 1)
            self.score += cash_points
            self.cash = self.spawn_cash(self.snake)
            self.try_spawn_power_up()
            self.flash_score()
            self.show_cash_burst()
            self.sync_best_score()
            self.status_text.textContent = f"Banked ${self.score}. Pace is picking up."
        else:
            self.snake.pop(0)
            self.try_spawn_power_up()

        if self.power_up is not None and next_head == self.power_up.position:
            self.activate_power_up(self.power_up.kind)
            self.power_up = None

        self.score_value.textContent = str(self.score)
        self.tick_ms = self.compute_tick_ms()
        self.update_power_up_status()

    def hit_wall(self, point: Point) -> bool:
        return point.x < 0 or point.y < 0 or point.x >= BOARD_CELLS or point.y >= BOARD_CELLS

    def spawn_cash(self, snake: Iterable[Point]) -> Point:
        """Spawn a cash pickup on a free board cell.

        Args:
            snake: Current snake body positions to avoid.

        Returns:
            A valid board position for cash.
        """
        occupied = set(snake)
        if self.power_up is not None:
            occupied.add(self.power_up.position)
        available = [
            Point(x, y)
            for y in range(BOARD_CELLS)
            for x in range(BOARD_CELLS)
            if Point(x, y) not in occupied
        ]
        return choice(available) if available else Point(0, 0)

    def sync_best_score(self) -> None:
        if self.score <= self.best_score:
            return
        self.best_score = self.score
        self.best_score_value.textContent = str(self.best_score)
        self.best_score_tile.classList.add("pulse")
        window.snakeCashRushBridge.writeBestScore(self.best_score)
        window.setTimeout(create_proxy(lambda: self.best_score_tile.classList.remove("pulse")), 240)

    def flash_score(self) -> None:
        self.score_tile.classList.remove("pulse")
        self.best_score_tile.classList.remove("pulse")
        self.score_tile.classList.add("pulse")
        window.setTimeout(create_proxy(lambda: self.score_tile.classList.remove("pulse")), 240)

    def show_cash_burst(self) -> None:
        self.cash_burst.classList.remove("visible")

        def trigger() -> None:
            self.cash_burst.classList.add("visible")

        def cleanup() -> None:
            self.cash_burst.classList.remove("visible")

        window.setTimeout(create_proxy(trigger), 10)
        window.setTimeout(create_proxy(cleanup), 460)

    def end_game(self) -> None:
        """Stop gameplay and present the game-over overlay.

        Args:
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
        """Render board, items, and snake.

        Args:
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

    def draw_board(self, ctx) -> None:
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
        """Return a JSON snapshot of the current game state.

        Args:
            None.

        Returns:
            Serialized JSON snapshot for debug tooling.
        """
        payload = {
            "running": self.running,
            "gameOver": self.game_over,
            "score": self.score,
            "bestScore": self.best_score,
            "tickMs": self.tick_ms,
            "direction": {"x": self.direction.x, "y": self.direction.y},
            "cash": {"x": self.cash.x, "y": self.cash.y},
            "powerUp": (
                None
                if self.power_up is None
                else {
                    "kind": self.power_up.kind,
                    "position": {"x": self.power_up.position.x, "y": self.power_up.position.y},
                }
            ),
            "activeEffects": self.effect_timers_ms,
            "snake": [{"x": segment.x, "y": segment.y} for segment in self.snake],
        }
        return json.dumps(payload)

    def place_cash_ahead(self) -> None:
        """Place cash in front of the snake for debug workflows.

        Args:
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

    def has_effect(self, effect_name: str) -> bool:
        """Check whether a temporary effect is currently active.

        Args:
            effect_name: Effect key to check.

        Returns:
            True when the effect timer is above zero.
        """
        return self.effect_timers_ms.get(effect_name, 0) > 0

    def compute_tick_ms(self) -> int:
        """Compute active tick speed based on score and effects.

        Args:
            None.

        Returns:
            Tick duration in milliseconds.
        """
        base_tick_ms = max(MIN_TICK_MS, BASE_TICK_MS - (self.score // SCORE_PER_BILL) * SPEED_STEP_MS)
        if self.has_effect(POWER_UP_SPEED):
            boosted_tick_ms = int(base_tick_ms * SPEED_BOOST_MULTIPLIER)
            return max(MIN_SPEED_BOOST_TICK_MS, boosted_tick_ms)
        return base_tick_ms

    def resolve_next_head(self, head: Point) -> Point:
        """Resolve the next head position, applying invincibility wrap behavior.

        Args:
            head: Current snake head location.

        Returns:
            Next head point after movement rules.
        """
        next_x = head.x + self.direction.x
        next_y = head.y + self.direction.y
        if self.has_effect(POWER_UP_INVINCIBLE):
            return Point(next_x % BOARD_CELLS, next_y % BOARD_CELLS)
        return Point(next_x, next_y)

    def update_effect_timers(self, elapsed_ms: int) -> None:
        """Reduce active effect timers by elapsed simulation time.

        Args:
            elapsed_ms: Milliseconds elapsed in the current tick.

        Returns:
            None.
        """
        for effect_name in POWER_UP_TYPES:
            current_value = self.effect_timers_ms.get(effect_name, 0)
            if current_value <= 0:
                continue
            self.effect_timers_ms[effect_name] = max(0, current_value - elapsed_ms)

    def try_spawn_power_up(self) -> None:
        """Spawn a random power-up on an open cell when eligible.

        Args:
            None.

        Returns:
            None.
        """
        if self.power_up is not None:
            return
        if random() > POWER_UP_SPAWN_CHANCE:
            return

        occupied = set(self.snake)
        occupied.add(self.cash)
        available = [
            Point(x, y)
            for y in range(BOARD_CELLS)
            for x in range(BOARD_CELLS)
            if Point(x, y) not in occupied
        ]
        if not available:
            return
        self.power_up = PowerUp(kind=choice(POWER_UP_TYPES), position=choice(available))

    def activate_power_up(self, kind: str) -> None:
        """Activate a collected power-up and refresh its duration.

        Args:
            kind: Power-up type key.

        Returns:
            None.
        """
        if kind not in POWER_UP_TYPES:
            return
        self.effect_timers_ms[kind] = POWER_UP_DURATION_MS
        label = POWER_UP_LABELS.get(kind, "Power")
        self.status_text.textContent = f"{label} activated for 7s. Keep moving."
        self.show_cash_burst()

    def update_power_up_status(self) -> None:
        """Render active power-up timers in the HUD.

        Args:
            None.

        Returns:
            None.
        """
        if self.power_up_status is None:
            return

        active_labels = []
        for effect_name in POWER_UP_TYPES:
            remaining_ms = self.effect_timers_ms.get(effect_name, 0)
            if remaining_ms <= 0:
                continue
            seconds = max(1, (remaining_ms + 999) // 1000)
            label = POWER_UP_LABELS[effect_name]
            active_labels.append(f"{label} {seconds}s")

        if not active_labels:
            self.power_up_status.textContent = "No active power-ups"
            return
        self.power_up_status.textContent = " | ".join(active_labels)

    def draw_power_up(self, ctx) -> None:
        """Draw the currently spawned power-up pickup.

        Args:
            ctx: Canvas rendering context.

        Returns:
            None.
        """
        if self.power_up is None:
            return

        cell = BOARD_PIXELS / BOARD_CELLS
        x = self.power_up.position.x * cell + 5
        y = self.power_up.position.y * cell + 5
        size = cell - 10
        fill_color, glow_color, text_color, marker = POWER_UP_COLORS[self.power_up.kind]

        ctx.save()
        ctx.shadowColor = glow_color
        ctx.shadowBlur = 14
        ctx.fillStyle = fill_color
        round_rect(ctx, x, y, size, size, 8)
        ctx.fill()
        ctx.fillStyle = text_color
        ctx.font = "700 11px Space Grotesk"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.fillText(marker, x + size / 2, y + size / 2 + 0.5)
        ctx.restore()

    def step_debug(self) -> None:
        if self.game_over:
            return
        self.running = True
        self.advance()
        self.draw()

    def destroy(self) -> None:
        self.cancel_animation()
        document.removeEventListener("keydown", self._key_proxy)


def round_rect(ctx, x: float, y: float, width: float, height: float, radius: float) -> None:
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