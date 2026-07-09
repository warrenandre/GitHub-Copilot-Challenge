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
POWER_UP_SPAWN_CHANCE = 0.34
POWER_UP_TYPES = ("speed_boost", "invincibility", "double_points")
POWER_UP_DURATIONS = {
    "speed_boost": 52,
    "invincibility": 44,
    "double_points": 48,
}
POWER_UP_LABELS = {
    "speed_boost": "Speed Boost",
    "invincibility": "Invincibility",
    "double_points": "Double Points",
}
POWER_UP_COLORS = {
    "speed_boost": "#69a9ff",
    "invincibility": "#ffd37d",
    "double_points": "#ff85cf",
}
POWER_UP_GLYPHS = {
    "speed_boost": "S",
    "invincibility": "I",
    "double_points": "2X",
}


@dataclass(frozen=True)
class PowerUp:
    """A spawnable power-up on the board.

    Attributes:
        kind: The power-up type identifier.
        position: Grid location where the item is currently placed.
    """

    kind: str
    position: Point


@dataclass
class ActivePower:
    """A currently active, temporary power-up effect.

    Attributes:
        kind: The active power-up type identifier.
        remaining_ticks: Number of game ticks before expiry.
    """

    kind: str
    remaining_ticks: int


@dataclass(frozen=True)
class Point:
    """Immutable 2-D grid coordinate.

    Frozen so that Point instances can be added to sets and used as dict keys,
    which is required for efficient occupied-cell lookups during cash spawning
    and collision detection.

    Attributes:
        x: Column index (0 = left edge).
        y: Row index (0 = top edge).
    """

    x: int
    y: int


class SnakeCashRush:
    def __init__(self) -> None:
        """Initialise the game.

        Looks up every DOM element the game needs, restores the persisted best
        score from localStorage via the JS bridge, registers all event listeners
        and debug hooks, then draws the initial idle board with the start overlay
        visible.
        """
        self.canvas = document.getElementById("gameCanvas")
        self.ctx = self.canvas.getContext("2d")
        self.score_value = document.getElementById("scoreValue")
        self.best_score_value = document.getElementById("bestScoreValue")
        self.status_text = document.getElementById("statusText")
        self.active_power_value = document.getElementById("activePowerValue")
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
        """Reset all mutable game state to its starting values.

        Positions the snake at the centre of the board moving upward, spawns
        the first cash bill, zeros the score and tick accumulator, and updates
        the score display.  Does **not** start the animation loop — call
        ``start_game`` after this to begin a run.
        """
        center = BOARD_CELLS // 2
        self.snake = [Point(center, center + 1), Point(center, center), Point(center, center - 1)]
        self.direction = Point(0, -1)
        self.pending_direction = Point(0, -1)
        self.cash = self.spawn_cash(self.snake)
        self.power_up: PowerUp | None = None
        self.active_power: ActivePower | None = None
        self.score = 0
        self.tick_ms = BASE_TICK_MS
        self.accumulator = 0.0
        self.last_frame_time = 0.0
        self.running = False
        self.game_over = False
        self.score_value.textContent = str(self.score)
        self.status_text.textContent = "Waiting for your first run."
        self.update_power_ui()

    def start_game(self) -> None:
        """Begin or resume a run.

        Guards against double-starting by returning immediately if the game is
        already running.  If the previous run ended in game-over, resets state
        first so the player starts fresh.  Hides the overlay, updates the
        button label, and kicks off the ``requestAnimationFrame`` loop.
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
        """Handle the Start / Restart button click.

        Acts as a context-aware toggle: restarts if a run is in progress or has
        just ended, otherwise starts the first run.  This single handler is
        wired to both the top HUD button and the overlay action button so that
        the player always has a consistent call-to-action regardless of state.
        """
        if self.running or self.game_over:
            self.restart_game()
            return
        self.start_game()

    def restart_game(self) -> None:
        """Abort the current run and immediately start a new one.

        Cancels any in-flight animation frame to avoid a stale callback firing
        after state has been wiped, then resets and restarts in one sequence.
        """
        self.cancel_animation()
        self.reset_state()
        self.start_game()

    def ensure_animation(self) -> None:
        """Schedule the next animation frame if one is not already pending.

        Guarding with ``is None`` prevents accidentally scheduling two
        concurrent ``requestAnimationFrame`` callbacks, which would cause the
        game loop to run at double speed.
        """
        if self.animation_handle is None:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def cancel_animation(self) -> None:
        """Cancel the pending animation frame, if any.

        Sets ``animation_handle`` to ``None`` after cancelling so that
        ``ensure_animation`` can safely reschedule later.
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
        """Update the overlay card's content and/or visibility.

        Only the fields that are not ``None`` are updated, so callers can
        change a single attribute without having to repeat unchanged values.

        Args:
            kicker: Small eyebrow text shown above the title (e.g. "Run complete").
            title: Large heading (e.g. "Press Start", "Crash Out").
            message: Body copy describing the current game state.
            button_text: Label for the overlay's call-to-action button.
            visible: ``True`` to show the overlay, ``False`` to hide it.
                     ``None`` leaves visibility unchanged.
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
        """Respond to ``keydown`` events from the browser.

        Maps directional keys (arrow keys and WASD) to ``pending_direction`` so
        the next game tick picks up the new heading.  Pressing ``R`` restarts
        immediately.  Any directional key also starts the game if it has not
        begun yet.

        The direction change is buffered in ``pending_direction`` rather than
        applied immediately so that two keys pressed within the same tick
        cannot produce a self-collision by reversing direction mid-tick.

        Args:
            event: The browser ``KeyboardEvent`` proxied through Pyodide.
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
        """Return ``True`` if ``next_direction`` is exactly opposite to ``current_direction``.

        Prevents the snake from immediately reversing into itself, which would
        be an instant and unintuitive death.  A 180-degree input is silently
        ignored rather than treated as an error.

        Args:
            next_direction: The direction the player wants to move.
            current_direction: The direction the snake is currently moving.

        Returns:
            ``True`` when the two directions are antiparallel.
        """
        return next_direction.x == -current_direction.x and next_direction.y == -current_direction.y

    def game_frame(self, timestamp) -> None:
        """Primary ``requestAnimationFrame`` callback — drives the game loop.

        Uses a fixed-timestep accumulator so the snake advances at a constant
        speed regardless of monitor refresh rate or frame drops.  Each call
        drains the accumulator in ``tick_ms``-sized chunks, calling ``advance``
        once per chunk, then renders and re-schedules itself.

        Setting ``animation_handle`` to ``None`` at entry is intentional: the
        handle is only valid until the callback fires, after which it must be
        renewed or left as ``None`` to stop the loop.

        Args:
            timestamp: High-resolution timestamp (ms) provided by the browser,
                       same origin as ``performance.now()``.
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

        while self.accumulator >= self.tick_ms and self.running:
          self.accumulator -= self.tick_ms
          self.advance()

        self.draw()

        if self.running:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def advance(self) -> None:
        """Advance the game by exactly one tick.

        Commits the buffered direction, computes the next head position, checks
        for wall and body collisions, and either extends the snake (on
        collection) or shifts it forward (normal move).  Ends the game on any
        collision.  Also handles score updates, speed progression, and UI
        feedback when a cash bill is collected.

        Speed is recalculated as::

            tick_ms = max(MIN_TICK_MS, BASE_TICK_MS - bills_collected * SPEED_STEP_MS)

        so each bill collected reduces the tick interval by ``SPEED_STEP_MS``
        until the floor of ``MIN_TICK_MS`` is reached.
        """
        self.direction = self.pending_direction
        head = self.snake[-1]
        next_head = Point(head.x + self.direction.x, head.y + self.direction.y)
        invincible = self.has_active_power("invincibility")
        if invincible:
            next_head = self.wrap_point(next_head)

        will_collect = next_head == self.cash
        will_collect_power = self.power_up is not None and next_head == self.power_up.position
        collision_body = self.snake if will_collect else self.snake[1:]

        if (not invincible and self.hit_wall(next_head)) or (not invincible and next_head in collision_body):
            self.end_game()
            return

        self.snake.append(next_head)

        if will_collect_power and self.power_up is not None:
            self.activate_power_up(self.power_up.kind)
            self.power_up = None

        if will_collect:
            earned_points = SCORE_PER_BILL * (2 if self.has_active_power("double_points") else 1)
            self.score += earned_points
            self.recalculate_tick_ms()
            self.cash = self.spawn_cash(self.snake)
            if self.power_up is None and random() <= POWER_UP_SPAWN_CHANCE:
                self.power_up = self.spawn_power_up(self.snake, self.cash)
            self.flash_score()
            self.show_cash_burst()
            self.sync_best_score()
            pickup_note = ""
            if self.active_power is not None:
                pickup_note = f" | Active: {POWER_UP_LABELS[self.active_power.kind]}"
            self.status_text.textContent = f"Banked ${earned_points}. Total ${self.score}.{pickup_note}"
        else:
            self.snake.pop(0)

        self.tick_active_power_up()
        self.recalculate_tick_ms()
        self.score_value.textContent = str(self.score)
        self.update_power_ui()

    def hit_wall(self, point: Point) -> bool:
        """Return ``True`` if ``point`` lies outside the playable grid.

        Args:
            point: The grid coordinate to test.

        Returns:
            ``True`` when the point is out of bounds.
        """
        return point.x < 0 or point.y < 0 or point.x >= BOARD_CELLS or point.y >= BOARD_CELLS

    def spawn_cash(self, snake: Iterable[Point]) -> Point:
        """Choose a random unoccupied cell for the next cash bill.

        Builds a set of occupied cells first so the availability check is O(1)
        per candidate rather than O(n).  Falls back to ``Point(0, 0)`` in the
        theoretically impossible scenario where every cell is filled.

        Args:
            snake: Current snake body segments used to determine occupied cells.

        Returns:
            A randomly selected ``Point`` that is not occupied by the snake.
        """
        occupied = set(snake)
        available = [
            Point(x, y)
            for y in range(BOARD_CELLS)
            for x in range(BOARD_CELLS)
            if Point(x, y) not in occupied
        ]
        return choice(available) if available else Point(0, 0)

    def spawn_power_up(self, snake: Iterable[Point], cash: Point) -> PowerUp | None:
        """Create a random power-up in an unoccupied cell.

        Args:
            snake: Current snake segments that cannot be occupied.
            cash: Current cash location that the power-up must avoid.

        Returns:
            A ``PowerUp`` instance if a free cell exists, otherwise ``None``.
        """
        occupied = set(snake)
        occupied.add(cash)
        available = [
            Point(x, y)
            for y in range(BOARD_CELLS)
            for x in range(BOARD_CELLS)
            if Point(x, y) not in occupied
        ]
        if not available:
            return None
        return PowerUp(choice(POWER_UP_TYPES), choice(available))

    def has_active_power(self, kind: str) -> bool:
        """Return whether the given power-up is currently active.

        Args:
            kind: Power-up type to check.

        Returns:
            ``True`` when the requested effect is active.
        """
        return self.active_power is not None and self.active_power.kind == kind

    def activate_power_up(self, kind: str) -> None:
        """Activate a power-up effect and reset its duration.

        Args:
            kind: Power-up type identifier to activate.

        Returns:
            None.
        """
        self.active_power = ActivePower(kind=kind, remaining_ticks=POWER_UP_DURATIONS[kind])
        self.status_text.textContent = f"Power-up active: {POWER_UP_LABELS[kind]}"
        self.recalculate_tick_ms()

    def tick_active_power_up(self) -> None:
        """Advance the active power-up timer by one tick.

        Args:
            None.

        Returns:
            None.
        """
        if self.active_power is None:
            return
        self.active_power.remaining_ticks -= 1
        if self.active_power.remaining_ticks > 0:
            return
        expired = POWER_UP_LABELS[self.active_power.kind]
        self.active_power = None
        self.status_text.textContent = f"{expired} ended. Keep collecting."

    def recalculate_tick_ms(self) -> None:
        """Recompute movement speed from score progression and active effects.

        Args:
            None.

        Returns:
            None.
        """
        score_speed_tick = max(MIN_TICK_MS, BASE_TICK_MS - (self.score // SCORE_PER_BILL) * SPEED_STEP_MS)
        if self.has_active_power("speed_boost"):
            score_speed_tick = max(MIN_TICK_MS, int(score_speed_tick * 0.65))
        self.tick_ms = score_speed_tick

    def update_power_ui(self) -> None:
        """Refresh the HUD text that displays the active power-up state.

        Args:
            None.

        Returns:
            None.
        """
        if self.active_power is None:
            self.active_power_value.textContent = "None"
            return
        label = POWER_UP_LABELS[self.active_power.kind]
        self.active_power_value.textContent = f"{label} ({self.active_power.remaining_ticks})"

    def wrap_point(self, point: Point) -> Point:
        """Wrap a point to the opposite board edge.

        Used while invincibility is active so wall contact does not end the run.

        Args:
            point: The out-of-bounds or in-bounds coordinate.

        Returns:
            The wrapped coordinate constrained to the board range.
        """
        return Point(point.x % BOARD_CELLS, point.y % BOARD_CELLS)

    def sync_best_score(self) -> None:
        """Persist a new best score if the current score exceeds it.

        Updates the in-memory best score, the HUD display, and the
        ``localStorage`` value via the JS bridge.  Also triggers a brief CSS
        pulse animation on the best-score tile to draw the player's attention.
        Does nothing when the current score has not yet surpassed the record.
        """
        if self.score <= self.best_score:
            return
        self.best_score = self.score
        self.best_score_value.textContent = str(self.best_score)
        self.best_score_tile.classList.add("pulse")
        window.snakeCashRushBridge.writeBestScore(self.best_score)
        window.setTimeout(create_proxy(lambda: self.best_score_tile.classList.remove("pulse")), 240)

    def flash_score(self) -> None:
        """Trigger a brief CSS pulse animation on the current-score tile.

        Resets both tiles' pulse state first so that back-to-back collections
        reliably restart the animation rather than leaving it stuck mid-way.
        The class is removed after 240 ms via ``setTimeout`` to keep the
        animation one-shot rather than looping.
        """
        self.score_tile.classList.remove("pulse")
        self.best_score_tile.classList.remove("pulse")
        self.score_tile.classList.add("pulse")
        window.setTimeout(create_proxy(lambda: self.score_tile.classList.remove("pulse")), 240)

    def show_cash_burst(self) -> None:
        """Play the "+$" burst animation overlaid on the canvas.

        The element is first hidden to reset any in-progress animation, then
        shown 10 ms later so the browser has time to register the class removal
        before the re-add.  It is hidden again after 460 ms, matching the CSS
        transition duration.
        """
        self.cash_burst.classList.remove("visible")

        def trigger() -> None:
            self.cash_burst.classList.add("visible")

        def cleanup() -> None:
            self.cash_burst.classList.remove("visible")

        window.setTimeout(create_proxy(trigger), 10)
        window.setTimeout(create_proxy(cleanup), 460)

    def end_game(self) -> None:
        """Halt the run and display the game-over overlay.

        Marks the game as stopped and over, updates the status text, and
        populates the overlay with the player's final score and best score
        before making it visible.  Triggers one final ``draw`` call so the
        canvas shows the snake's position at the moment of collision.
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
        """Render the full game frame onto the canvas.

        Clears the canvas then delegates to the three layer-drawing helpers in
        order: board grid, cash bill, snake.  Keeping rendering split into
        discrete layers makes each helper easier to test and modify in
        isolation.
        """
        ctx = self.ctx
        ctx.clearRect(0, 0, BOARD_PIXELS, BOARD_PIXELS)
        self.draw_board(ctx)
        self.draw_cash(ctx)
        self.draw_power_up(ctx)
        self.draw_snake(ctx)

    def draw_board(self, ctx) -> None:
        """Draw the dark background and faint grid lines.

        Grid lines are drawn at even cell-width intervals across the full
        canvas.  They are intentionally subtle (8 % opacity) to create depth
        without distracting from the snake and cash.

        Args:
            ctx: The canvas 2D rendering context.
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
        """Draw the cash bill pickup at its current grid position.

        Renders a rounded green rectangle with a centred "$" glyph and a soft
        glow shadow to make it visually distinct from the snake body.

        Args:
            ctx: The canvas 2D rendering context.
        """
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

    def draw_power_up(self, ctx) -> None:
        """Draw the current power-up pickup if one is available.

        Args:
            ctx: The canvas 2D rendering context.

        Returns:
            None.
        """
        if self.power_up is None:
            return

        cell = BOARD_PIXELS / BOARD_CELLS
        radius = cell * 0.32
        center_x = self.power_up.position.x * cell + cell / 2
        center_y = self.power_up.position.y * cell + cell / 2
        color = POWER_UP_COLORS[self.power_up.kind]
        glyph = POWER_UP_GLYPHS[self.power_up.kind]

        ctx.save()
        ctx.shadowColor = color
        ctx.shadowBlur = 18
        ctx.fillStyle = color
        ctx.beginPath()
        ctx.arc(center_x, center_y, radius, 0, 6.283)
        ctx.fill()
        ctx.fillStyle = "#102437"
        ctx.font = "700 11px Space Grotesk"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.fillText(glyph, center_x, center_y + 0.5)
        ctx.restore()

    def draw_snake(self, ctx) -> None:
        """Draw every segment of the snake, with the head styled differently.

        Body segments use a darker green; the head uses a brighter tint with a
        stronger glow and two small eye circles so the player can instantly
        read which end is leading.

        Args:
            ctx: The canvas 2D rendering context.
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
        """Return a JSON string snapshot of the current game state.

        Exposed on ``window.snakeCashRushSnapshot`` for browser-console
        debugging.  The payload includes all fields needed to reproduce or
        inspect the game state at any point in time.

        Returns:
            A JSON-encoded string with keys: ``running``, ``gameOver``,
            ``score``, ``bestScore``, ``tickMs``, ``direction``, ``cash``,
            and ``snake``.
        """
        payload = {
            "running": self.running,
            "gameOver": self.game_over,
            "score": self.score,
            "bestScore": self.best_score,
            "tickMs": self.tick_ms,
            "activePower": self.active_power.kind if self.active_power is not None else None,
            "activePowerTicks": self.active_power.remaining_ticks if self.active_power is not None else 0,
            "powerUp": {
                "kind": self.power_up.kind,
                "x": self.power_up.position.x,
                "y": self.power_up.position.y,
            }
            if self.power_up is not None
            else None,
            "direction": {"x": self.direction.x, "y": self.direction.y},
            "cash": {"x": self.cash.x, "y": self.cash.y},
            "snake": [{"x": segment.x, "y": segment.y} for segment in self.snake],
        }
        return json.dumps(payload)

    def place_cash_ahead(self) -> None:
        """Teleport the cash bill to the first valid cell in front of the snake.

        Exposed on ``window.snakeCashRushPlaceCashAhead`` as a debug helper so
        developers can quickly trigger a collection without waiting for the
        snake to wander close to the current bill position.  Tries the cell
        directly ahead first, then the four cardinal neighbours, and skips any
        cell that is out of bounds or already occupied by the snake.
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
        """Advance the game by a single tick without waiting for the animation loop.

        Exposed on ``window.snakeCashRushStep`` so developers can step through
        the game frame-by-frame from the browser console.  Temporarily forces
        ``running`` to ``True`` so ``advance`` does not short-circuit, making
        it usable even when the game is paused.
        """
        if self.game_over:
            return
        self.running = True
        self.advance()
        self.draw()

    def destroy(self) -> None:
        """Tear down the game instance and release browser resources.

        Cancels the animation loop and removes the ``keydown`` event listener.
        Should be called before replacing or discarding a ``SnakeCashRush``
        instance to avoid memory leaks from dangling Pyodide proxies.
        """
        self.cancel_animation()
        document.removeEventListener("keydown", self._key_proxy)


def round_rect(ctx, x: float, y: float, width: float, height: float, radius: float) -> None:
    """Trace a rounded rectangle path on the canvas context.

    Uses quadratic Bézier curves for the corners.  The caller is responsible
    for calling ``ctx.fill()`` or ``ctx.stroke()`` after this function to
    actually paint the shape.

    Args:
        ctx: The canvas 2D rendering context.
        x: Left edge of the rectangle in pixels.
        y: Top edge of the rectangle in pixels.
        width: Width of the rectangle in pixels.
        height: Height of the rectangle in pixels.
        radius: Corner radius in pixels.
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