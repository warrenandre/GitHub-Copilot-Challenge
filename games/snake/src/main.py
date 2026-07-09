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
    """Represents a 2D coordinate on the game board.
    
    Attributes:
        x (int): The x-coordinate (column) on the board.
        y (int): The y-coordinate (row) on the board.
    """
    x: int
    y: int


class SnakeCashRush:
    def __init__(self) -> None:
        """Initialize the Snake Cash Rush game.
        
        Sets up the canvas, DOM elements, event listeners, game state, and renders
        the initial overlay. This method is called once when the game module is loaded.
        
        Returns:
            None
        """
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

        # Create proxies to preserve 'self' context when callbacks are invoked from JavaScript.
        # PyScript requires proxies for methods called from the browser's event system.
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
        
        Initializes the snake in the center of the board, resets score and timing,
        places the first cash pickup, and updates the UI. Called at game start and
        when restarting.
        
        Returns:
            None
        """
        center = BOARD_CELLS // 2
        # Initialize snake as a 3-segment vertical line pointing upward. Snake segments are stored
        # from tail to head, with the last element being the head position.
        self.snake = [Point(center, center + 1), Point(center, center), Point(center, center - 1)]
        # Direction (0, -1) means moving up (decreasing y). Initialized to match the snake's orientation.
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
        
        Begins active gameplay if not already running. Resets the game state if
        a previous game ended, updates the UI status, hides the overlay, and
        ensures the animation loop is running.
        
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
        """Handle the start button click or initial game action.
        
        Restarts the game if already running or game over, otherwise starts a new game.
        This method is bound to both the start button click and overlay button click.
        
        Returns:
            None
        """
        if self.running or self.game_over:
            self.restart_game()
            return
        self.start_game()

    def restart_game(self) -> None:
        """Restart the game from scratch.
        
        Stops the current animation frame, resets all game state, and starts a new game.
        This provides a complete reset without preserving any run-specific data.
        
        Returns:
            None
        """
        self.cancel_animation()
        self.reset_state()
        self.start_game()

    def ensure_animation(self) -> None:
        """Ensure the animation loop is running.
        
        Requests an animation frame if one is not already pending. Used to restart
        the game loop after it has been cancelled.
        
        Returns:
            None
        """
        if self.animation_handle is None:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def cancel_animation(self) -> None:
        """Cancel the running animation frame.
        
        Stops the game's render loop by cancelling the pending animation frame request.
        Used when pausing or ending the game.
        
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
        """Update the game overlay display.
        
        Allows selective updates to the overlay text and visibility. Only parameters
        that are not None are updated. Used for initial state, game over, and other
        UI state notifications.
        
        Parameters:
            kicker (str | None): The eyebrow text above the title.
            title (str | None): The main heading of the overlay.
            message (str | None): The descriptive message text.
            button_text (str | None): The text on the action button.
            visible (bool | None): Whether to show or hide the overlay.
        
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
        
        Processes arrow keys (↑↓←→) and WASD for snake movement, 'R' to restart,
        and automatically starts the game on first directional input if not already running.
        Prevents reverse input (moving directly opposite to current direction).
        
        Parameters:
            event: The keyboard event object from the browser.
        
        Returns:
            None
        """
        key = str(event.key).lower()
        if key == "r":
            self.restart_game()
            return

        # Map keyboard keys to movement directions. Both arrow keys and WASD are supported.
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
            # Ignore non-directional keys
            return

        # Auto-start game on first directional input during idle state
        if not self.running and not self.game_over:
            self.start_game()

        # Prevent 180-degree turn input. Without this check, rapid keypresses could cause
        # the snake to instantly collide with itself (e.g., pressing left while moving right).
        if self.is_reverse(next_direction, self.direction):
            return

        # Store pending direction for the next game tick. Using a pending direction prevents
        # input buffering issues where multiple inputs between ticks could be lost.
        self.pending_direction = next_direction

    def is_reverse(self, next_direction: Point, current_direction: Point) -> bool:
        """Check if a direction is the reverse of the current direction.
        
        Used to prevent the snake from moving directly backward into itself.
        
        Parameters:
            next_direction (Point): The requested movement direction.
            current_direction (Point): The current snake movement direction.
        
        Returns:
            bool: True if next_direction is opposite to current_direction, False otherwise.
        """
        return next_direction.x == -current_direction.x and next_direction.y == -current_direction.y

    def game_frame(self, timestamp) -> None:
        """Render a single game frame.
        
        Called by the browser's requestAnimationFrame. Updates game logic based on
        elapsed time, advances the game state as needed, and renders the current frame.
        Uses a fixed timestep to decouple game logic from frame rate.
        
        Parameters:
            timestamp (float): The current time in milliseconds from the browser.
        
        Returns:
            None
        """
        self.animation_handle = None

        if not self.running:
            self.draw()
            return

        # Initialize frame timing on first call to avoid large initial delta jumps
        if self.last_frame_time == 0.0:
            self.last_frame_time = float(timestamp)

        # Calculate elapsed time since last frame (in milliseconds)
        frame_delta = float(timestamp) - self.last_frame_time
        self.last_frame_time = float(timestamp)
        self.accumulator += frame_delta

        # Use fixed timestep to decouple game logic from frame rate. This ensures consistent
        # gameplay regardless of whether the game runs at 30, 60, or higher FPS. The accumulator
        # may execute multiple ticks per frame on slow devices or single tick on fast devices.
        while self.accumulator >= self.tick_ms and self.running:
          self.accumulator -= self.tick_ms
          self.advance()

        self.draw()

        if self.running:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def advance(self) -> None:
        """Advance the game logic by one tick.
        
        Updates the snake's position, checks for collisions with walls and itself,
        handles cash collection, updates score and speed, and ends the game if a
        collision occurs. Called at a fixed timestep frequency.
        
        Returns:
            None
        """
        self.direction = self.pending_direction
        head = self.snake[-1]
        next_head = Point(head.x + self.direction.x, head.y + self.direction.y)
        will_collect = next_head == self.cash
        # If collecting cash, check collision with entire body including current head.
        # Otherwise exclude the tail since the tail will be removed this tick (before any collision).
        collision_body = self.snake if will_collect else self.snake[1:]

        if self.hit_wall(next_head) or next_head in collision_body:
            self.end_game()
            return

        self.snake.append(next_head)

        if will_collect:
            self.score += SCORE_PER_BILL
            # Increase game speed with each cash collected using a linear formula.
            # Score is divided by SCORE_PER_BILL (10) to convert score into number of bills collected.
            # Speed increases by SPEED_STEP_MS (5ms) per bill, capped at MIN_TICK_MS to prevent overplay.
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
        """Check if a point is outside the board boundaries.
        
        Parameters:
            point (Point): The coordinate to check.
        
        Returns:
            bool: True if the point is outside the board, False otherwise.
        """
        return point.x < 0 or point.y < 0 or point.x >= BOARD_CELLS or point.y >= BOARD_CELLS

    def spawn_cash(self, snake: Iterable[Point]) -> Point:
        """Generate a random unoccupied position for the next cash bill.
        
        Selects a random cell on the board that is not occupied by the snake.
        Falls back to (0, 0) if no free cells are available (edge case in very long games).
        
        Parameters:
            snake (Iterable[Point]): The current snake segments to exclude from selection.
        
        Returns:
            Point: A random Point representing the cash location.
        """
        # Convert snake to a set for O(1) lookup time. Checking membership in a list would be O(n).
        occupied = set(snake)
        # Collect all unoccupied cells on the board. Using a list comprehension is efficient
        # even for a 20×20 board (400 cells max), and choice() requires a sequence anyway.
        available = [
            Point(x, y)
            for y in range(BOARD_CELLS)
            for x in range(BOARD_CELLS)
            if Point(x, y) not in occupied
        ]
        # Return a random available cell. The fallback (0, 0) is for edge case when board is full.
        # In practice, a snake on a 20×20 board never fills more than ~80 cells before colliding.
        return choice(available) if available else Point(0, 0)

    def sync_best_score(self) -> None:
        """Update the best score if current score exceeds it.
        
        Compares the current score to the best score, updates the display and
        persistent storage if a new best is achieved, and triggers a visual
        pulse animation on the best score tile.
        
        Returns:
            None
        """
        if self.score <= self.best_score:
            return
        self.best_score = self.score
        self.best_score_value.textContent = str(self.best_score)
        # Add pulse class to trigger CSS animation. The 240ms matches the animation duration.
        self.best_score_tile.classList.add("pulse")
        # Persist best score to browser localStorage for survival across page reloads.
        window.snakeCashRushBridge.writeBestScore(self.best_score)
        # Schedule pulse class removal after animation completes (240ms duration).
        # Using create_proxy ensures the lambda retains proper 'self' context in PyScript.
        window.setTimeout(create_proxy(lambda: self.best_score_tile.classList.remove("pulse")), 240)

    def flash_score(self) -> None:
        """Trigger a visual flash animation on the score tile.
        
        Removes and re-adds the pulse CSS class to create a brief animation
        feedback when the player collects a cash bill.
        
        Returns:
            None
        """
        self.score_tile.classList.remove("pulse")
        self.best_score_tile.classList.remove("pulse")
        self.score_tile.classList.add("pulse")
        window.setTimeout(create_proxy(lambda: self.score_tile.classList.remove("pulse")), 240)

    def show_cash_burst(self) -> None:
        """Display a brief cash burst animation when collecting money.
        
        Triggers a visual effect that appears for about 450ms to provide feedback
        when the player collects a cash bill. Uses deferred DOM updates to ensure
        the animation triggers correctly.
        
        Returns:
            None
        """
        # Remove 'visible' class first to reset animation state, ensuring it plays even if
        # called multiple times in succession (necessary for CSS animation replay).
        self.cash_burst.classList.remove("visible")

        def trigger() -> None:
            self.cash_burst.classList.add("visible")

        def cleanup() -> None:
            self.cash_burst.classList.remove("visible")

        # Schedule animation to start after 10ms. This brief delay allows the browser to process
        # the removal of 'visible' class before re-adding it, ensuring the CSS animation triggers.
        window.setTimeout(create_proxy(trigger), 10)
        # Schedule animation cleanup at 460ms. CSS animation runs for ~450ms, so remove 'visible'
        # shortly after to reset state for the next cash collection.
        window.setTimeout(create_proxy(cleanup), 460)

    def end_game(self) -> None:
        """End the current game run due to collision.
        
        Stops the game, updates the UI with the final score, displays the game-over
        overlay with restart option, and prepares the game for a potential restart.
        
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
        """Render all game elements to the canvas.
        
        Clears the canvas and calls rendering functions for the board background,
        cash pickup, and snake. Called once per frame.
        
        Returns:
            None
        """
        ctx = self.ctx
        ctx.clearRect(0, 0, BOARD_PIXELS, BOARD_PIXELS)
        self.draw_board(ctx)
        self.draw_cash(ctx)
        self.draw_snake(ctx)

    def draw_board(self, ctx) -> None:
        """Draw the game board background and grid lines.
        
        Fills the board with the background color and renders a subtle grid pattern
        to help visualize the playing field.
        
        Parameters:
            ctx: The canvas 2D rendering context.
        
        Returns:
            None
        """
        ctx.fillStyle = "#07141d"
        ctx.fillRect(0, 0, BOARD_PIXELS, BOARD_PIXELS)

        ctx.strokeStyle = "rgba(151, 183, 163, 0.08)"
        ctx.lineWidth = 1
        for index in range(BOARD_CELLS + 1):
            # Calculate grid line position. Each cell is (BOARD_PIXELS / BOARD_CELLS = 28) pixels wide.
            # 'position' determines where the line is drawn in the 560×560 canvas.
            offset = index * GRID_SIZE + index * (BOARD_PIXELS / BOARD_CELLS - GRID_SIZE)
            position = index * (BOARD_PIXELS / BOARD_CELLS)  # e.g., 0, 28, 56, ..., 560
            # Draw vertical lines (columns)
            ctx.beginPath()
            ctx.moveTo(position, 0)
            ctx.lineTo(position, BOARD_PIXELS)
            ctx.stroke()
            # Draw horizontal lines (rows)
            ctx.beginPath()
            ctx.moveTo(0, position)
            ctx.lineTo(BOARD_PIXELS, position)
            ctx.stroke()

    def draw_cash(self, ctx) -> None:
        """Draw the current cash bill on the canvas.
        
        Renders a rounded rectangle with a dollar sign ($) symbol and applies
        a glowing shadow effect. The cash is drawn with bright green color.
        
        Parameters:
            ctx: The canvas 2D rendering context.
        
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
        """Draw the snake segments on the canvas.
        
        Renders each segment of the snake with rounded corners and a glowing shadow.
        The head is rendered brighter with eyes, while body segments are slightly dimmer.
        
        Parameters:
            ctx: The canvas 2D rendering context.
        
        Returns:
            None
        """
        cell = BOARD_PIXELS / BOARD_CELLS
        for index, segment in enumerate(self.snake):
            inset = 3
            x = segment.x * cell + inset
            y = segment.y * cell + inset
            size = cell - inset * 2
            # Head is the last segment in the snake list (stored tail-first)
            is_head = index == len(self.snake) - 1

            ctx.save()
            # Head is brighter (#a9ffcb) for visibility and visual feedback to the player.
            ctx.fillStyle = "#1fce74" if not is_head else "#a9ffcb"
            ctx.shadowColor = "rgba(103, 247, 160, 0.35)"
            # Head has a stronger glow (shadowBlur 14) to distinguish it from body (8)
            ctx.shadowBlur = 14 if is_head else 8
            round_rect(ctx, x, y, size, size, 9)
            ctx.fill()

            if is_head:
                # Draw eyes to give the snake personality and make it face the direction it's moving.
                # Eye Y is positioned at 38% from top for a natural look.
                eye_y = y + size * 0.38
                ctx.fillStyle = "#063720"
                ctx.beginPath()
                # Two eyes positioned at 34% and 66% horizontally for symmetry
                ctx.arc(x + size * 0.34, eye_y, 2.1, 0, 6.283)
                ctx.arc(x + size * 0.66, eye_y, 2.1, 0, 6.283)
                ctx.fill()
            ctx.restore()

    def snapshot_json(self) -> str:
        """Serialize the current game state to JSON format.
        
        Creates a complete snapshot of all relevant game state including snake position,
        direction, cash location, score, and game flags. Used for debugging and testing.
        
        Returns:
            str: A JSON string representing the current game state.
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
        """Place cash at a nearby location for debugging purposes.
        
        Attempts to place the next cash bill in one of five positions:
        directly ahead of the snake's head, or one cell in each cardinal direction.
        If all positions are blocked, no action is taken. Used for testing and development.
        
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
        """Advance the game by a single tick for debugging.
        
        Manually triggers one game logic advance step without running the full
        animation loop. Useful for step-by-step debugging of game behavior.
        Does nothing if the game is already over.
        
        Returns:
            None
        """
        if self.game_over:
            return
        self.running = True
        self.advance()
        self.draw()

    def destroy(self) -> None:
        """Clean up and destroy the game instance.
        
        Removes event listeners and cancels the animation frame to allow the
        game instance to be garbage collected. Called when unloading the page or
        restarting the module.
        
        Returns:
            None
        """
        self.cancel_animation()
        document.removeEventListener("keydown", self._key_proxy)


def round_rect(ctx, x: float, y: float, width: float, height: float, radius: float) -> None:
    """Draw a rounded rectangle path on the canvas.
    
    Creates a path for a rectangle with rounded corners using quadratic curves.
    The path is not automatically filled or stroked; the caller must call
    ctx.fill() or ctx.stroke() after this function.
    
    Parameters:
        ctx: The canvas 2D rendering context.
        x (float): The x-coordinate of the top-left corner.
        y (float): The y-coordinate of the top-left corner.
        width (float): The width of the rectangle.
        height (float): The height of the rectangle.
        radius (float): The radius of the rounded corners.
    
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