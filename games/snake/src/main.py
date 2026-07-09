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
    """Immutable (x, y) grid coordinate used for snake segments, direction vectors, and the cash position.

    Attributes:
        x: Column index, 0 is the left edge, BOARD_CELLS-1 is the right edge.
        y: Row index, 0 is the top edge, BOARD_CELLS-1 is the bottom edge.
    """

    x: int
    y: int


class SnakeCashRush:
    def __init__(self) -> None:
        """Initialise the game by wiring up DOM references, reading the persisted best score,
        registering PyScript-safe JS proxies for all event listeners and JS-callable hooks,
        then drawing the initial idle canvas and showing the 'Press Start' overlay.

        DOM elements expected in index.html:
            gameCanvas      — <canvas> element where the board is rendered.
            scoreValue      — <strong> that displays the live score.
            bestScoreValue  — <strong> that displays the all-time best score.
            statusText      — <p> status line below the HUD.
            startButton     — 'Start Run' / 'Restart Run' button in the HUD.
            gameOverlay     — overlay card shown before the game starts and on game-over.
            overlayKicker   — small eyebrow text inside the overlay.
            overlayTitle    — large heading inside the overlay.
            overlayMessage  — body copy inside the overlay.
            overlayButton   — primary action button inside the overlay.
            cashBurst       — off-screen '+$' element animated on each cash pickup.

        JS bridge (window.snakeCashRushBridge) expected from app.js:
            raf(callback)        — calls requestAnimationFrame(callback).
            cancelRaf(handle)   — calls cancelAnimationFrame(handle).
            readBestScore()     — returns the integer best score from localStorage.
            writeBestScore(n)   — persists the best score to localStorage.
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

        # Load best score from localStorage via the JS bridge defined in app.js.
        self.best_score = int(window.snakeCashRushBridge.readBestScore())
        self.score_value.textContent = "0"
        self.best_score_value.textContent = str(self.best_score)

        # last_frame_time=0.0 is the sentinel that triggers first-frame initialisation
        # inside game_frame() so the accumulator does not get a huge initial delta.
        self.last_frame_time = 0.0
        self.accumulator = 0.0   # milliseconds of unprocessed time carried across frames
        self.animation_handle = None  # requestAnimationFrame handle; None means no frame queued
        self.running = False
        self.game_over = False
        self.pending_restart = False

        # PyScript runs Python in a WebWorker/WASM context.  Passing a Python callable
        # directly to a JS API (addEventListener, setTimeout, etc.) would be garbage-collected
        # by the JS engine because JS holds no strong reference to the Python object.
        # create_proxy() wraps the callable in a JS Proxy that keeps it alive for the
        # lifetime of this game instance.
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
        # Expose debug helpers on window so they can be called from the browser DevTools
        # console, e.g.: snakeCashRushSnapshot(), snakeCashRushStep(), snakeCashRushPlaceCashAhead()
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
        """Reset all mutable game state to its starting values without touching DOM event listeners.

        Called at initialisation and at the start of every new run.  Positions the snake
        as three vertical segments in the centre of the board, places a fresh cash bill,
        resets the score and tick speed, and updates the score and status text in the HUD.
        Does *not* start the animation loop — call start_game() afterwards.
        """
        center = BOARD_CELLS // 2
        # Snake starts as three vertical segments: tail one cell below centre, then centre,
        # then head one cell above centre.  Index 0 is always the tail; the last index is
        # always the head.  Initial direction is up (y decreases as rows go down).
        self.snake = [Point(center, center + 1), Point(center, center), Point(center, center - 1)]
        self.direction = Point(0, -1)
        # pending_direction buffers the player's most recent key press and is applied at
        # the start of the next advance() tick.  This prevents two direction changes in
        # a single tick from bypassing the 180-degree reversal guard.
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
        """Transition from idle or game-over state into an active run.

        If the game is already running this call is a no-op.  If a previous run has ended
        (game_over is True) the state is reset via reset_state() before starting.  Sets
        running=True, hides the overlay, updates the HUD button label, and kicks off the
        requestAnimationFrame loop via ensure_animation().
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
        """Handle a click on the 'Start Run' / 'Restart Run' HUD button.

        If a run is currently active or has just ended, delegates to restart_game() so the
        button always acts as a hard reset once play has begun.  On the very first visit
        (not running, not game_over) it calls start_game() instead.
        """
        if self.running or self.game_over:
            self.restart_game()
            return
        self.start_game()

    def restart_game(self) -> None:
        """Immediately cancel any running animation, wipe all game state, and start a fresh run.

        Safe to call at any point — during an active run, after a game-over, or from the
        idle screen.  Triggered by the 'R' key, the overlay 'Run It Back' button, and the
        HUD 'Restart Run' button when a run is in progress.
        """
        self.cancel_animation()
        self.reset_state()
        self.start_game()

    def ensure_animation(self) -> None:
        """Request the next animation frame if one is not already scheduled.

        Stores the integer handle returned by requestAnimationFrame in
        self.animation_handle so it can be cancelled later by cancel_animation().
        This guard prevents double-scheduling, which would cause the game to run
        at twice the intended speed.
        """
        if self.animation_handle is None:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def cancel_animation(self) -> None:
        """Cancel the pending requestAnimationFrame call and clear the stored handle.

        Calls cancelAnimationFrame via the JS bridge and sets self.animation_handle to
        None so ensure_animation() knows it is safe to schedule a new frame.  Safe to
        call when no frame is pending — the guard on self.animation_handle prevents a
        spurious cancelAnimationFrame(None) call.
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
        """Update the overlay card that sits on top of the canvas.

        Only the arguments that are not None are changed, so callers can update a single
        field without knowing or repeating the current values of the others.

        Args:
            kicker:      Small eyebrow label shown above the main title (e.g. 'Run complete').
            title:       Large heading text (e.g. 'Crash Out', 'Press Start').
            message:     Body copy below the heading.
            button_text: Label for the primary action button inside the overlay.
            visible:     True adds the CSS class 'visible' to show the overlay;
                         False removes it to hide the overlay;
                         None leaves visibility unchanged.
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
        """Process a DOM 'keydown' event and update game state accordingly.

        Handles two categories of input:
        - 'R' key: immediately restarts the game regardless of current state.
        - Arrow keys and WASD: queue a direction change in self.pending_direction.
          The new direction is applied at the start of the next advance() tick to
          prevent mid-tick reversals.  A 180-degree reversal (moving directly back
          into the snake body) is silently ignored via is_reverse().
          If the game is idle (not running and no game-over), the first directional
          key also starts the game.

        Args:
            event: A JavaScript KeyboardEvent object.  Only event.key is read.
        """
        key = str(event.key).lower()
        if key == "r":
            self.restart_game()
            return

        # Map every supported key to its direction vector.  Using a dict literal
        # keeps the mapping declarative and avoids a chain of if/elif clauses.
        # .get() returns None for any unrecognised key, which is filtered out below.
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
            return  # ignore keys that are not game controls

        # Allow the first arrow/WASD press to start the game from the idle screen.
        if not self.running and not self.game_over:
            self.start_game()

        # Silently discard any attempt to reverse directly into the snake's own neck.
        if self.is_reverse(next_direction, self.direction):
            return

        self.pending_direction = next_direction

    def is_reverse(self, next_direction: Point, current_direction: Point) -> bool:
        """Return True if next_direction is exactly opposite to current_direction.

        Used in handle_keydown to prevent the snake from instantly reversing into
        its own neck, which would always cause an immediate collision.

        Args:
            next_direction:    The direction the player is trying to move towards.
            current_direction: The direction the snake is currently travelling.

        Returns:
            True if the two directions are antiparallel (e.g. left vs right, up vs down).
        """
        return next_direction.x == -current_direction.x and next_direction.y == -current_direction.y

    def game_frame(self, timestamp) -> None:
        """requestAnimationFrame callback — the main render/update loop entry point.

        Called by the browser once per display refresh (typically 60 fps).  Uses a
        fixed-timestep accumulator so the game tick rate is controlled by self.tick_ms
        regardless of the display refresh rate.  Multiple ticks are consumed per frame
        when the browser falls behind (e.g. tab was hidden), preventing the snake from
        appearing to teleport after focus is restored.

        Workflow per frame:
        1. Clear the pending handle so ensure_animation() can reschedule.
        2. If not running, just redraw and return (shows the idle or game-over frame).
        3. Accumulate the elapsed milliseconds since the last frame.
        4. Drain the accumulator in self.tick_ms-sized chunks, calling advance() each time.
        5. Draw the updated state.
        6. Schedule the next frame via ensure_animation() if the game is still running.

        Args:
            timestamp: High-resolution DOMHighResTimeStamp (float, milliseconds) provided
                       by requestAnimationFrame.  Compared against self.last_frame_time
                       to compute the delta for the accumulator.
        """
        # Clear the handle first so ensure_animation() can safely reschedule
        # even if advance() or draw() trigger an indirect call to it.
        self.animation_handle = None

        if not self.running:
            self.draw()  # render the idle/game-over frame then stop looping
            return

        # On the very first frame, seed last_frame_time instead of computing a delta.
        # Without this guard the first delta would be measured from epoch 0 (~2 million
        # seconds), causing the accumulator to drain thousands of ticks at once.
        if self.last_frame_time == 0.0:
            self.last_frame_time = float(timestamp)

        # Fixed-timestep accumulator pattern: add the real elapsed time, then consume
        # it in discrete game-tick chunks.  This decouples game speed from display
        # refresh rate — a 144 Hz monitor and a 30 Hz monitor both advance the snake
        # at the same number of ticks per second.
        frame_delta = float(timestamp) - self.last_frame_time
        self.last_frame_time = float(timestamp)
        self.accumulator += frame_delta

        # Process as many whole ticks as the accumulator allows.  The `and self.running`
        # guard exits the loop immediately if advance() triggered end_game().
        while self.accumulator >= self.tick_ms and self.running:
          self.accumulator -= self.tick_ms
          self.advance()

        self.draw()

        if self.running:
            self.animation_handle = window.snakeCashRushBridge.raf(self._frame_proxy)

    def advance(self) -> None:
        """Advance the game by exactly one tick: move the snake, check collisions, and handle collection.

        Steps performed each tick:
        1. Commit the queued direction (pending_direction → direction).
        2. Compute the next head position by adding the direction vector to the current head.
        3. Check whether the next head lands on the cash bill (will_collect).
        4. Detect wall collisions (hit_wall) and body collisions.  When will_collect is True,
           the full snake list is used for the body check — the tail will grow, so it remains
           in place and must be treated as occupied.  Otherwise only snake[1:] is checked,
           because snake[0] (the tail) is about to vacate its cell.
        5. On collision: call end_game() and return.
        6. Append the new head to the snake list.
        7. If cash was collected: increment score, tighten the tick speed (capped at MIN_TICK_MS),
           spawn a new cash bill, trigger HUD animations, and update the status text.
           If no cash was collected: pop the tail so the snake moves without growing.
        8. Update the score display in the HUD.
        """
        self.direction = self.pending_direction
        head = self.snake[-1]
        next_head = Point(head.x + self.direction.x, head.y + self.direction.y)
        will_collect = next_head == self.cash

        # Tail-inclusion trick: when the head is about to land on the cash bill the
        # snake will grow — the tail stays in place for this tick.  That means the tail
        # cell counts as occupied and moving into it is a valid collision.  When no
        # collection happens the tail vacates its cell on this same tick, so snake[0]
        # is a safe cell to move through and is excluded from the collision check.
        collision_body = self.snake if will_collect else self.snake[1:]

        if self.hit_wall(next_head) or next_head in collision_body:
            self.end_game()
            return

        self.snake.append(next_head)  # grow the snake by one cell at the new head position

        if will_collect:
            self.score += SCORE_PER_BILL
            # Speed formula: each collected bill reduces the tick interval by SPEED_STEP_MS,
            # floored at MIN_TICK_MS.  Dividing score by SCORE_PER_BILL converts the raw
            # score back into a bill count so the speed depends on bills eaten, not raw points.
            self.tick_ms = max(MIN_TICK_MS, BASE_TICK_MS - (self.score // SCORE_PER_BILL) * SPEED_STEP_MS)
            self.cash = self.spawn_cash(self.snake)
            self.flash_score()
            self.show_cash_burst()
            self.sync_best_score()
            self.status_text.textContent = f"Banked ${self.score}. Pace is picking up."
        else:
            self.snake.pop(0)  # remove the tail so the snake moves without growing

        self.score_value.textContent = str(self.score)

    def hit_wall(self, point: Point) -> bool:
        """Return True if the given grid point lies outside the playable area.

        The board spans columns 0..BOARD_CELLS-1 and rows 0..BOARD_CELLS-1.
        Any point with a negative coordinate or a coordinate equal to or greater
        than BOARD_CELLS is considered a wall hit.

        Args:
            point: The grid coordinate to test (typically the snake's next head position).

        Returns:
            True if the point is out-of-bounds, False if it is inside the board.
        """
        return point.x < 0 or point.y < 0 or point.x >= BOARD_CELLS or point.y >= BOARD_CELLS

    def spawn_cash(self, snake: Iterable[Point]) -> Point:
        """Choose a random empty cell on the board and return it as the new cash position.

        Builds the complete set of occupied cells from the current snake segments, then
        selects uniformly at random from all unoccupied cells.  In the extreme (and
        effectively impossible in normal play) case where the snake fills every cell,
        falls back to Point(0, 0).

        Args:
            snake: An iterable of Point objects representing every snake segment.
                   Passed explicitly rather than reading self.snake so this method can
                   be called before self.snake is assigned (e.g. during reset_state).

        Returns:
            A Point that is not occupied by any snake segment, chosen at random.
        """
        occupied = set(snake)  # O(1) membership tests instead of O(n) list scans
        # Build the full list of free cells with a comprehension rather than filtering
        # in place so spawn_cash() has no side-effects on the snake list itself.
        available = [
            Point(x, y)
            for y in range(BOARD_CELLS)
            for x in range(BOARD_CELLS)
            if Point(x, y) not in occupied
        ]
        # Fallback to (0, 0) is a safety net — in a 20×20 grid this can only happen
        # if the snake occupies all 400 cells, which requires a score of 3990.
        return choice(available) if available else Point(0, 0)

    def sync_best_score(self) -> None:
        """Update the best score if the current score exceeds it, then persist it to localStorage.

        Called after every cash collection.  When a new best is set:
        - Updates self.best_score and the 'Best' HUD tile text.
        - Adds the CSS 'pulse' animation class to the best-score tile.
        - Writes the new value to localStorage via the JS bridge so it survives page reloads.
        - Schedules removal of the pulse class after 240 ms.

        Does nothing if self.score is not strictly greater than self.best_score.
        """
        if self.score <= self.best_score:
            return
        self.best_score = self.score
        self.best_score_value.textContent = str(self.best_score)
        self.best_score_tile.classList.add("pulse")
        window.snakeCashRushBridge.writeBestScore(self.best_score)
        window.setTimeout(create_proxy(lambda: self.best_score_tile.classList.remove("pulse")), 240)

    def flash_score(self) -> None:
        """Trigger a brief CSS pulse animation on the live-score HUD tile.

        Removes the 'pulse' class from both score tiles first to allow the animation
        to retrigger even when consecutive bills are collected in quick succession,
        then adds it to the current-score tile only.  The pulse class is removed after
        240 ms via a JS setTimeout so the animation plays exactly once per collection.
        """
        self.score_tile.classList.remove("pulse")
        self.best_score_tile.classList.remove("pulse")
        self.score_tile.classList.add("pulse")
        window.setTimeout(create_proxy(lambda: self.score_tile.classList.remove("pulse")), 240)

    def show_cash_burst(self) -> None:
        """Play the '+$' burst animation that floats over the canvas on each cash pickup.

        The cashBurst element is hidden by default.  To allow the animation to replay
        even on back-to-back collections:
        1. Remove 'visible' immediately (resets any in-progress animation).
        2. After 10 ms, add 'visible' to start the CSS keyframe animation.
        3. After 460 ms, remove 'visible' to hide the element again.

        The 10 ms delay is necessary because removing and re-adding a class in the same
        synchronous task does not retrigger a CSS animation — the browser needs at least
        one repaint cycle in between.
        """
        # Remove first so the browser registers a genuine class-list change.
        # If we only added 'visible' without removing it first and the previous
        # animation was still running, the CSS @keyframes would not restart.
        self.cash_burst.classList.remove("visible")

        def trigger() -> None:
            """Add the 'visible' CSS class to start the burst keyframe animation."""
            self.cash_burst.classList.add("visible")

        def cleanup() -> None:
            """Remove the 'visible' CSS class to hide the burst element after animation ends."""
            self.cash_burst.classList.remove("visible")

        # 10 ms delay gives the browser one repaint cycle after the remove() call,
        # ensuring the animation restarts cleanly even on back-to-back collections.
        window.setTimeout(create_proxy(trigger), 10)
        window.setTimeout(create_proxy(cleanup), 460)  # 460 ms matches the CSS animation duration

    def end_game(self) -> None:
        """Handle a collision that ends the current run.

        Sets running=False and game_over=True to halt the tick loop, updates the status
        text with the final score, and shows the game-over overlay with a 'Run It Back'
        button.  The overlay message references both the run score and the current best
        score to encourage the player to try again.  Calls draw() once more to render
        the final board state (snake frozen at the point of collision).
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
        """Composite one complete frame onto the canvas.

        Clears the canvas, then delegates to the three layer-drawing helpers in order:
        draw_board (background grid) → draw_cash (pickup bill) → draw_snake (segments).
        Called at the end of every game_frame(), after end_game(), and once at startup
        to show the idle board.
        """
        ctx = self.ctx
        ctx.clearRect(0, 0, BOARD_PIXELS, BOARD_PIXELS)
        self.draw_board(ctx)
        self.draw_cash(ctx)
        self.draw_snake(ctx)

    def draw_board(self, ctx) -> None:
        """Draw the dark background and the faint grid lines onto the canvas.

        Fills the entire canvas with the board background colour (#07141d), then draws
        BOARD_CELLS+1 evenly-spaced horizontal and vertical lines using a very low-opacity
        stroke to create the cell grid.  Line positions are computed so they align with
        the edges of each BOARD_CELLS × BOARD_CELLS grid cell.

        Args:
            ctx: The CanvasRenderingContext2D obtained from the <canvas> element.
        """
        ctx.fillStyle = "#07141d"
        ctx.fillRect(0, 0, BOARD_PIXELS, BOARD_PIXELS)

        ctx.strokeStyle = "rgba(151, 183, 163, 0.08)"
        ctx.lineWidth = 1
        # Draw BOARD_CELLS+1 lines to frame every cell edge (cells + 1 border lines).
        # position = index * cell_size places each line at the exact cell boundary.
        for index in range(BOARD_CELLS + 1):
            offset = index * GRID_SIZE + index * (BOARD_PIXELS / BOARD_CELLS - GRID_SIZE)
            position = index * (BOARD_PIXELS / BOARD_CELLS)  # pixel coordinate of this grid line
            ctx.beginPath()           # vertical line
            ctx.moveTo(position, 0)
            ctx.lineTo(position, BOARD_PIXELS)
            ctx.stroke()
            ctx.beginPath()           # horizontal line at the same offset
            ctx.moveTo(0, position)
            ctx.lineTo(BOARD_PIXELS, position)
            ctx.stroke()

    def draw_cash(self, ctx) -> None:
        """Draw the current cash bill pickup at self.cash's grid position.

        Renders a rounded green rectangle with a glow shadow effect and a centred '$'
        label to represent the collectible.  The rectangle is inset slightly within the
        cell (4 px horizontal, 7 px vertical padding) to leave breathing room between
        the bill and the snake segments.

        Args:
            ctx: The CanvasRenderingContext2D obtained from the <canvas> element.
        """
        px = self.cash.x * GRID_SIZE * 1.4  # unused legacy variable, kept for reference
        py = self.cash.y * GRID_SIZE * 1.4  # unused legacy variable, kept for reference
        cell = BOARD_PIXELS / BOARD_CELLS    # pixel width/height of one grid cell
        # Inset the bill rectangle within its cell so it does not touch the grid lines.
        # Horizontal inset: 4 px each side.  Vertical inset: 7 px top, leaving height-14 total.
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
        """Draw every segment of the snake, with the head rendered distinctly.

        Iterates over self.snake in order (index 0 is the tail, last index is the head).
        Each segment is drawn as a rounded square slightly inset within its grid cell.
        The head segment uses a brighter fill colour (#a9ffcb vs #1fce74 for body segments)
        and a stronger glow shadow.  Two small filled circles are drawn on the head as eyes,
        positioned in the upper-middle of the segment regardless of travel direction.

        Args:
            ctx: The CanvasRenderingContext2D obtained from the <canvas> element.
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
                # Position both eyes at 38 % down from the top of the head cell so
                # they sit in the upper portion of the segment regardless of direction.
                eye_y = y + size * 0.38
                ctx.fillStyle = "#063720"
                ctx.beginPath()
                # 6.283 ≈ 2π — draws a full circle arc for each eye.
                # Left eye at 34 % from the left edge; right eye at 66 %.
                ctx.arc(x + size * 0.34, eye_y, 2.1, 0, 6.283)
                ctx.arc(x + size * 0.66, eye_y, 2.1, 0, 6.283)
                ctx.fill()
            ctx.restore()

    def snapshot_json(self) -> str:
        """Serialise the current game state to a JSON string for external inspection or testing.

        Exposed to JavaScript as window.snakeCashRushSnapshot().  Useful for automated
        tests or browser-console debugging — call snakeCashRushSnapshot() in DevTools to
        inspect the live state without pausing the game.

        Returns:
            A JSON string with the following keys:
                running   (bool)  — whether the game loop is active.
                gameOver  (bool)  — whether the most recent run has ended.
                score     (int)   — current run score.
                bestScore (int)   — all-time best score (from localStorage).
                tickMs    (float) — current tick interval in milliseconds.
                direction (dict)  — {x, y} of the active direction vector.
                cash      (dict)  — {x, y} grid position of the cash bill.
                snake     (list)  — list of {x, y} dicts from tail (index 0) to head (last).
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
        """Teleport the cash bill to the cell directly ahead of the snake's head (debug helper).

        Exposed to JavaScript as window.snakeCashRushPlaceCashAhead().  Tries the cell
        immediately in front of the head first, then falls back to the four orthogonally
        adjacent cells in order (right, left, down, up).  Skips any candidate that would
        be out-of-bounds or already occupied by a snake segment.  Redraws the board after
        moving the cash so the change is visible immediately.

        Intended for use in browser DevTools during development to quickly test collection
        logic without having to steer the snake manually.
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
        """Advance the game by exactly one tick and redraw (debug helper).

        Exposed to JavaScript as window.snakeCashRushStep().  Forces running=True so
        advance() executes even when the game has not been started yet.  Does nothing
        if game_over is True (a finished run must be restarted before stepping).

        Intended for use in browser DevTools during development to step through game
        logic frame-by-frame without the animation loop running.
        """
        if self.game_over:
            return
        self.running = True
        self.advance()
        self.draw()

    def destroy(self) -> None:
        """Tear down the game instance and release all browser resources.

        Cancels any pending animation frame and removes the 'keydown' event listener
        from the document.  Should be called if the game element is removed from the
        DOM (e.g. during single-page-app navigation) to prevent memory leaks and ghost
        key handlers.  Not called automatically — invoke explicitly when needed.
        """
        self.cancel_animation()
        document.removeEventListener("keydown", self._key_proxy)


def round_rect(ctx, x: float, y: float, width: float, height: float, radius: float) -> None:
    """Trace a rounded rectangle path on the given canvas context without filling or stroking it.

    Uses quadratic Bézier curves at each corner to produce the rounding.  The caller is
    responsible for calling ctx.fill() or ctx.stroke() after this function returns.
    This helper exists because CanvasRenderingContext2D.roundRect() is not available in
    all browsers supported by this game.

    Args:
        ctx:    The CanvasRenderingContext2D to draw on.
        x:      Left edge of the rectangle in canvas pixels.
        y:      Top edge of the rectangle in canvas pixels.
        width:  Width of the rectangle in canvas pixels.
        height: Height of the rectangle in canvas pixels.
        radius: Corner radius in canvas pixels.  Should be at most half of the
                smaller of width and height to avoid visual artefacts.
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