from __future__ import annotations

import json
from dataclasses import dataclass
from random import choice
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


@dataclass(frozen=True)
class Point:
    x: int
    y: int


class SnakeCashRush:
    def __init__(self) -> None:
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
        """Reset the game state to initial conditions.
        
        Initializes the snake at the center of the board pointing upward,
        spawns a new cash item, resets score and timing values, and updates
        the UI to reflect the reset state. Called when starting a new game
        or restarting after game over.
        
        Returns:
            None
        """
        center = BOARD_CELLS // 2
        self.snake = [Point(center, center + 1), Point(center, center), Point(center, center - 1)]
        self.direction = Point(0, -1)
        self.pending_direction = Point(0, -1)
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
        """Start or resume the game.
        
        Transitions the game from idle or game-over state to running state.
        Resets timing accumulators, updates the UI to show game is active,
        hides the overlay, and starts the animation loop.
        
        Returns:
            None
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
        """Handle the primary action button click (Start/Restart).
        
        If the game is running or in game-over state, restart the game.
        Otherwise, start a new game.
        
        Returns:
            None
        """
        if self.running or self.game_over:
            self.restart_game()
            return
        self.start_game()

    def restart_game(self) -> None:
        """Completely restart the game from scratch.
        
        Stops the animation loop, resets all game state, and immediately
        starts a fresh game. Used when the player presses R or clicks restart.
        
        Returns:
            None
        """
        self.cancel_animation()
        self.reset_state()
        self.start_game()

    def ensure_animation(self) -> None:
        """Ensure the animation loop is running.
        
        If no animation frame request is currently pending, schedule a new one.
        This is called during game start to kick off the animation loop.
        
        Returns:
            None
        """
        if self.animation_handle is None:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def cancel_animation(self) -> None:
        """Cancel the currently scheduled animation frame.
        
        Stops the animation loop by canceling the pending requestAnimationFrame.
        Called when pausing, restarting, or destroying the game.
        
        Returns:
            None
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
        """Update the game overlay with new content or visibility.
        
        Updates any combination of overlay elements (kicker, title, message,
        button text) and can show or hide the overlay. Only updates elements
        that are provided (non-None values).
        
        Args:
            kicker: Optional subheading text for the overlay.
            title: Optional main title text for the overlay.
            message: Optional message body text for the overlay.
            button_text: Optional text for the action button.
            visible: Optional boolean to show (True) or hide (False) the overlay.
        
        Returns:
            None
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
        """Handle keyboard input events.
        
        Processes arrow keys and WASD for snake direction control, and R for
        restarting. Automatically starts the game on first arrow/WASD press.
        Prevents reversing into the snake's own body.
        
        Args:
            event: The DOM keyboard event object with key property.
        
        Returns:
            None
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
        """Check if a direction is opposite to the current direction.
        
        Used to prevent the snake from reversing 180 degrees into itself,
        which would cause immediate collision.
        
        Args:
            next_direction: The requested movement direction as a Point.
            current_direction: The snake's current movement direction as a Point.
        
        Returns:
            True if next_direction is opposite to current_direction, False otherwise.
        """
        return next_direction.x == -current_direction.x and next_direction.y == -current_direction.y

    def game_frame(self, timestamp) -> None:
        """Main animation frame callback executed every screen refresh.
        
        Implements a fixed-timestep game loop using an accumulator pattern.
        Processes elapsed time, advances the game state for each completed tick,
        and renders the current frame. Automatically schedules the next frame
        if the game is still running.
        
        Args:
            timestamp: High-resolution timestamp from requestAnimationFrame in milliseconds.
        
        Returns:
            None
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
        """Advance game state by one tick.
        
        Moves the snake, checks for collisions with walls and body,
        handles cash collection (growing snake and increasing score),
        and increases difficulty. Called once per game tick from game_frame().
        
        Returns:
            None
        """
        self.direction = self.pending_direction
        head = self.snake[-1]
        next_head = Point(head.x + self.direction.x, head.y + self.direction.y)
        will_collect = next_head == self.cash
        collision_body = self.snake if will_collect else self.snake[1:]

        if self.hit_wall(next_head) or next_head in collision_body:
            self.end_game()
            return

        self.snake.append(next_head)

        if will_collect:
            self.score += SCORE_PER_BILL
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
        """Check if a point is outside the game board boundaries.
        
        Args:
            point: The position to check.
        
        Returns:
            True if the point is outside the board bounds, False otherwise.
        """
        return point.x < 0 or point.y < 0 or point.x >= BOARD_CELLS or point.y >= BOARD_CELLS

    def spawn_cash(self, snake: Iterable[Point]) -> Point:
        """Spawn a cash item at a random unoccupied board location.
        
        Finds all empty cells (not occupied by the snake) and randomly selects
        one for the new cash item. Falls back to (0, 0) if no cells are available
        (should only occur if snake fills entire board).
        
        Args:
            snake: The current snake body as an iterable of Point objects.
        
        Returns:
            A Point object representing the location for the new cash item.
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
        """Update the best score if current score is higher.
        
        When a new high score is achieved, updates the display, triggers
        a pulse animation, persists to browser storage, and schedules
        animation cleanup.
        
        Returns:
            None
        """
        if self.score <= self.best_score:
            return
        self.best_score = self.score
        self.best_score_value.textContent = str(self.best_score)
        self.best_score_tile.classList.add("pulse")
        window.snakeCashRushBridge.writeBestScore(self.best_score)
        window.setTimeout(create_proxy(lambda: self.best_score_tile.classList.remove("pulse")), 240)

    def flash_score(self) -> None:
        """Trigger a pulse animation on the score display.
        
        Called when the player collects cash to provide visual feedback.
        Removes any existing pulse animation first, then adds a new one
        and schedules removal after 240ms.
        
        Returns:
            None
        """
        self.score_tile.classList.remove("pulse")
        self.best_score_tile.classList.remove("pulse")
        self.score_tile.classList.add("pulse")
        window.setTimeout(create_proxy(lambda: self.score_tile.classList.remove("pulse")), 240)

    def show_cash_burst(self) -> None:
        """Show a cash collection burst animation.
        
        Displays a temporary "+$" burst effect when the player collects cash.
        Manages animation lifecycle with two scheduled events: one to show
        the burst (10ms delay) and one to hide it (460ms delay).
        
        Returns:
            None
        """
        self.cash_burst.classList.remove("visible")

        def trigger() -> None:
            self.cash_burst.classList.add("visible")

        def cleanup() -> None:
            self.cash_burst.classList.remove("visible")

        window.setTimeout(create_proxy(trigger), 10)
        window.setTimeout(create_proxy(cleanup), 460)

    def end_game(self) -> None:
        """End the current game due to collision.
        
        Stops the game loop, displays the game-over overlay with final score
        and best score information, and updates status text to encourage replay.
        
        Returns:
            None
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
        """Render the current game state to the canvas.
        
        Clears the canvas and renders the board grid, cash item, and snake.
        Called once per animation frame to display updated game visuals.
        
        Returns:
            None
        """
        ctx = self.ctx
        ctx.clearRect(0, 0, BOARD_PIXELS, BOARD_PIXELS)
        self.draw_board(ctx)
        self.draw_cash(ctx)
        self.draw_snake(ctx)

    def draw_board(self, ctx) -> None:
        """Render the game board with background and grid lines.
        
        Fills the board with the background color and draws a subtle grid
        pattern to delineate individual board cells.
        
        Args:
            ctx: The canvas 2D drawing context.
        
        Returns:
            None
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
        """Render the cash item on the canvas.
        
        Draws a glowing green rounded rectangle with a dollar sign symbol.
        Uses shadow effects for visual depth.
        
        Args:
            ctx: The canvas 2D drawing context.
        
        Returns:
            None
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
        """Render the snake body and head on the canvas.
        
        Draws all snake segments as rounded rectangles with rounded corners.
        The head is lighter and has glowing shadow and eyes. Body segments
        are darker green with less glow.
        
        Args:
            ctx: The canvas 2D drawing context.
        
        Returns:
            None
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
        """Generate a JSON snapshot of the current game state.
        
        Creates a complete serializable representation of all game state,
        useful for debugging or state inspection. Accessible from browser
        console via window.snakeCashRushSnapshot().
        
        Returns:
            A JSON string containing the complete game state.
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
        }
        return json.dumps(payload)

    def place_cash_ahead(self) -> None:
        """Place cash directly ahead of the snake for debugging.
        
        Attempts to place cash at the next position in the snake's movement
        direction, or adjacent cells if that position is blocked. Used for
        testing and debugging via browser console.
        
        Returns:
            None
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
        """Manually advance the game by one tick for debugging.
        
        Allows stepping through the game one tick at a time via browser console
        for inspection and testing. Does nothing if the game is in game-over state.
        
        Returns:
            None
        """
        if self.game_over:
            return
        self.running = True
        self.advance()
        self.draw()

    def destroy(self) -> None:
        """Clean up resources and event listeners.
        
        Stops the animation loop and removes the keyboard event listener.
        Should be called before discarding a SnakeCashRush instance to prevent
        memory leaks and orphaned event handlers.
        
        Returns:
            None
        """
        self.cancel_animation()
        document.removeEventListener("keydown", self._key_proxy)


def round_rect(ctx, x: float, y: float, width: float, height: float, radius: float) -> None:
    """Draw a rounded rectangle on the canvas.
    
    Helper function to draw rectangles with rounded corners using quadratic
    Bezier curves. Used by draw_cash() and draw_snake() for visual assets.
    
    Args:
        ctx: The canvas 2D drawing context.
        x: The x-coordinate of the top-left corner.
        y: The y-coordinate of the top-left corner.
        width: The width of the rectangle.
        height: The height of the rectangle.
        radius: The radius of the rounded corners.
    
    Returns:
        None
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