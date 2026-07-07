"""Unit tests for Snake Cash Rush core gameplay behavior."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from typing import Callable


class FakeClassList:
    """Provide minimal classList behavior used by the game.

    Args:
        None.

    Returns:
        None.
    """

    def __init__(self) -> None:
        """Initialize an empty class set.

        Args:
            None.

        Returns:
            None.
        """
        self._values: set[str] = set()

    def add(self, value: str) -> None:
        """Add a class name to the set.

        Args:
            value: Class name to add.

        Returns:
            None.
        """
        self._values.add(value)

    def remove(self, value: str) -> None:
        """Remove a class name from the set if present.

        Args:
            value: Class name to remove.

        Returns:
            None.
        """
        self._values.discard(value)


class FakeElement:
    """Represent a generic DOM element used by the game.

    Args:
        element_id: Optional identifier for debugging.

    Returns:
        None.
    """

    def __init__(self, element_id: str | None = None) -> None:
        """Create element state with listeners and display properties.

        Args:
            element_id: Optional identifier for the fake element.

        Returns:
            None.
        """
        self.element_id = element_id
        self.textContent = ""
        self.parentElement: FakeElement | None = None
        self.classList = FakeClassList()
        self._listeners: dict[str, list[Callable[..., object]]] = {}

    def addEventListener(self, event: str, callback: Callable[..., object]) -> None:
        """Register an event listener callback.

        Args:
            event: Event name to register.
            callback: Callback callable.

        Returns:
            None.
        """
        self._listeners.setdefault(event, []).append(callback)


class FakeCanvasContext:
    """Implement the subset of 2D canvas API used by main.py.

    Args:
        None.

    Returns:
        None.
    """

    def clearRect(self, x: float, y: float, w: float, h: float) -> None:
        """No-op canvas clear.

        Args:
            x: X coordinate.
            y: Y coordinate.
            w: Width.
            h: Height.

        Returns:
            None.
        """

    def fillRect(self, x: float, y: float, w: float, h: float) -> None:
        """No-op fill rectangle.

        Args:
            x: X coordinate.
            y: Y coordinate.
            w: Width.
            h: Height.

        Returns:
            None.
        """

    def beginPath(self) -> None:
        """No-op path begin.

        Args:
            None.

        Returns:
            None.
        """

    def moveTo(self, x: float, y: float) -> None:
        """No-op move path cursor.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Returns:
            None.
        """

    def lineTo(self, x: float, y: float) -> None:
        """No-op draw line segment.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Returns:
            None.
        """

    def stroke(self) -> None:
        """No-op stroke path.

        Args:
            None.

        Returns:
            None.
        """

    def save(self) -> None:
        """No-op save canvas state.

        Args:
            None.

        Returns:
            None.
        """

    def restore(self) -> None:
        """No-op restore canvas state.

        Args:
            None.

        Returns:
            None.
        """

    def fill(self) -> None:
        """No-op fill path.

        Args:
            None.

        Returns:
            None.
        """

    def arc(self, x: float, y: float, radius: float, start: float, end: float) -> None:
        """No-op arc draw.

        Args:
            x: Center X.
            y: Center Y.
            radius: Arc radius.
            start: Start angle.
            end: End angle.

        Returns:
            None.
        """

    def fillText(self, text: str, x: float, y: float) -> None:
        """No-op text draw.

        Args:
            text: Display text.
            x: X coordinate.
            y: Y coordinate.

        Returns:
            None.
        """

    def quadraticCurveTo(self, cpx: float, cpy: float, x: float, y: float) -> None:
        """No-op quadratic curve draw.

        Args:
            cpx: Control point X.
            cpy: Control point Y.
            x: End point X.
            y: End point Y.

        Returns:
            None.
        """

    def closePath(self) -> None:
        """No-op close path.

        Args:
            None.

        Returns:
            None.
        """


class FakeCanvasElement(FakeElement):
    """Represent a canvas DOM element with context lookup.

    Args:
        element_id: Identifier for the canvas element.

    Returns:
        None.
    """

    def __init__(self, element_id: str) -> None:
        """Initialize a fake canvas with an attached context.

        Args:
            element_id: Canvas element id.

        Returns:
            None.
        """
        super().__init__(element_id=element_id)
        self._context = FakeCanvasContext()

    def getContext(self, context_type: str) -> FakeCanvasContext:
        """Return the fake 2D rendering context.

        Args:
            context_type: Requested context type.

        Returns:
            FakeCanvasContext: Canvas context for drawing methods.
        """
        if context_type != "2d":
            raise ValueError("Only 2d context is supported in tests.")
        return self._context


class FakeDocument:
    """Provide minimal DOM lookup and event registration behavior.

    Args:
        None.

    Returns:
        None.
    """

    def __init__(self) -> None:
        """Create all elements required by SnakeCashRush.__init__.

        Args:
            None.

        Returns:
            None.
        """
        self._elements: dict[str, FakeElement] = {
            "gameCanvas": FakeCanvasElement("gameCanvas"),
            "scoreValue": FakeElement("scoreValue"),
            "bestScoreValue": FakeElement("bestScoreValue"),
            "statusText": FakeElement("statusText"),
            "startButton": FakeElement("startButton"),
            "gameOverlay": FakeElement("gameOverlay"),
            "overlayKicker": FakeElement("overlayKicker"),
            "overlayTitle": FakeElement("overlayTitle"),
            "overlayMessage": FakeElement("overlayMessage"),
            "overlayButton": FakeElement("overlayButton"),
            "cashBurst": FakeElement("cashBurst"),
        }

        self._elements["scoreValue"].parentElement = FakeElement("scoreTile")
        self._elements["bestScoreValue"].parentElement = FakeElement("bestScoreTile")

    def getElementById(self, element_id: str) -> FakeElement:
        """Resolve and return an element by id.

        Args:
            element_id: Element id to retrieve.

        Returns:
            FakeElement: Matching fake element.
        """
        return self._elements[element_id]

    def addEventListener(self, event: str, callback: Callable[..., object]) -> None:
        """No-op document event registration.

        Args:
            event: Event name.
            callback: Callback function.

        Returns:
            None.
        """

    def removeEventListener(self, event: str, callback: Callable[..., object]) -> None:
        """No-op document event unregistration.

        Args:
            event: Event name.
            callback: Callback function.

        Returns:
            None.
        """


class FakeBridge:
    """Mimic the small JavaScript bridge used by main.py.

    Args:
        None.

    Returns:
        None.
    """

    def __init__(self) -> None:
        """Initialize bridge state.

        Args:
            None.

        Returns:
            None.
        """
        self._best_score = 0

    def raf(self, callback: Callable[..., object]) -> int:
        """Return a fake animation frame handle.

        Args:
            callback: Frame callback.

        Returns:
            int: Fake frame handle.
        """
        return 1

    def cancelRaf(self, handle: int) -> None:
        """No-op cancellation of a fake frame handle.

        Args:
            handle: Frame handle identifier.

        Returns:
            None.
        """

    def readBestScore(self) -> int:
        """Return the currently stored best score.

        Args:
            None.

        Returns:
            int: Best score value.
        """
        return self._best_score

    def writeBestScore(self, score: int) -> None:
        """Persist best score value in memory.

        Args:
            score: Best score to persist.

        Returns:
            None.
        """
        self._best_score = score


class FakeWindow:
    """Provide the window object surface used by SnakeCashRush.

    Args:
        None.

    Returns:
        None.
    """

    def __init__(self) -> None:
        """Initialize window bridge and dynamic attributes.

        Args:
            None.

        Returns:
            None.
        """
        self.snakeCashRushBridge = FakeBridge()

    def setTimeout(self, callback: Callable[..., object], timeout_ms: int) -> int:
        """Execute timeout callback immediately for deterministic tests.

        Args:
            callback: Callback function to execute.
            timeout_ms: Requested timeout in milliseconds.

        Returns:
            int: Fake timeout handle.
        """
        callback()
        return 1


def install_browser_stubs() -> None:
    """Install fake js and pyodide modules before importing main.py.

    Args:
        None.

    Returns:
        None.
    """
    js_module = types.ModuleType("js")
    js_module.document = FakeDocument()
    js_module.window = FakeWindow()
    sys.modules["js"] = js_module

    pyodide_module = types.ModuleType("pyodide")
    ffi_module = types.ModuleType("pyodide.ffi")

    def create_proxy(callback: Callable[..., object]) -> Callable[..., object]:
        """Return callback directly to emulate pyodide proxy creation.

        Args:
            callback: Callback to proxy.

        Returns:
            Callable[..., object]: Same callback for test runtime.
        """
        return callback

    ffi_module.create_proxy = create_proxy
    pyodide_module.ffi = ffi_module
    sys.modules["pyodide"] = pyodide_module
    sys.modules["pyodide.ffi"] = ffi_module


def load_main_module() -> types.ModuleType:
    """Load src/main.py as a module using the active stubs.

    Args:
        None.

    Returns:
        types.ModuleType: Imported main module.
    """
    module_path = Path(__file__).resolve().parents[1] / "src" / "main.py"
    spec = importlib.util.spec_from_file_location("snake_cash_rush_main_under_test", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load main.py for tests.")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SnakeCashRushTests(unittest.TestCase):
    """Cover snake movement, collision handling, and score updates.

    Args:
        None.

    Returns:
        None.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """Install stubs and import module once for the test class.

        Args:
            None.

        Returns:
            None.
        """
        install_browser_stubs()
        cls.main_module = load_main_module()

    def setUp(self) -> None:
        """Create a fresh game instance before each test.

        Args:
            None.

        Returns:
            None.
        """
        self.game = self.main_module.SnakeCashRush()

    def test_advance_moves_snake_without_changing_score(self) -> None:
        """Verify movement advances head and keeps score unchanged without pickup.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main_module.Point
        self.game.cash = point(0, 0)

        previous_segments = list(self.game.snake)
        expected_head = point(
            previous_segments[-1].x + self.game.direction.x,
            previous_segments[-1].y + self.game.direction.y,
        )

        self.game.advance()

        self.assertEqual(previous_segments[1:], self.game.snake[:-1])
        self.assertEqual(expected_head, self.game.snake[-1])
        self.assertEqual(0, self.game.score)
        self.assertEqual("0", self.game.score_value.textContent)

    def test_advance_sets_game_over_on_wall_collision(self) -> None:
        """Verify wall collision ends the current run.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main_module.Point
        self.game.snake = [point(5, 0)]
        self.game.direction = point(0, -1)
        self.game.pending_direction = point(0, -1)
        self.game.cash = point(10, 10)

        self.game.advance()

        self.assertTrue(self.game.game_over)
        self.assertFalse(self.game.running)

    def test_advance_sets_game_over_on_self_collision(self) -> None:
        """Verify self-collision ends the run when moving into body segment.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main_module.Point
        self.game.snake = [point(2, 2), point(2, 3), point(3, 3), point(3, 2)]
        self.game.direction = point(0, 1)
        self.game.pending_direction = point(0, 1)
        self.game.cash = point(10, 10)

        self.game.advance()

        self.assertTrue(self.game.game_over)
        self.assertFalse(self.game.running)

    def test_collecting_cash_increases_score_and_grows_snake(self) -> None:
        """Verify cash collection increases score and snake length.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main_module.Point
        self.game.snake = [point(5, 7), point(5, 6), point(5, 5)]
        self.game.direction = point(0, -1)
        self.game.pending_direction = point(0, -1)

        next_head = point(5, 4)
        self.game.cash = next_head
        previous_length = len(self.game.snake)

        self.game.advance()

        self.assertEqual(self.main_module.SCORE_PER_BILL, self.game.score)
        self.assertEqual(previous_length + 1, len(self.game.snake))
        self.assertEqual(str(self.main_module.SCORE_PER_BILL), self.game.score_value.textContent)
        self.assertEqual(self.main_module.SCORE_PER_BILL, self.game.best_score)

    def test_boundary_collisions_trigger_game_over_on_all_edges(self) -> None:
        """Verify collisions at each board edge end the current run.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main_module.Point
        board_last = self.main_module.BOARD_CELLS - 1
        scenarios: list[tuple[str, object, object]] = [
            ("top", point(5, 0), point(0, -1)),
            ("bottom", point(5, board_last), point(0, 1)),
            ("left", point(0, 5), point(-1, 0)),
            ("right", point(board_last, 5), point(1, 0)),
        ]

        for name, head, direction in scenarios:
            with self.subTest(edge=name):
                self.game.reset_state()
                self.game.running = True
                self.game.game_over = False
                self.game.snake = [head]
                self.game.direction = direction
                self.game.pending_direction = direction
                self.game.cash = point(10, 10)

                self.game.advance()

                self.assertTrue(self.game.game_over)
                self.assertFalse(self.game.running)

    def test_moving_into_previous_tail_cell_does_not_count_as_self_collision(self) -> None:
        """Verify moving into the previous tail position remains valid when not collecting.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main_module.Point
        self.game.snake = [point(2, 2), point(3, 2), point(3, 3), point(2, 3)]
        self.game.direction = point(0, -1)
        self.game.pending_direction = point(0, -1)
        self.game.cash = point(10, 10)

        self.game.advance()

        self.assertFalse(self.game.game_over)
        self.assertEqual(point(2, 2), self.game.snake[-1])
        self.assertEqual(4, len(self.game.snake))

    def test_spawn_cash_returns_only_available_cell_when_board_is_almost_full(self) -> None:
        """Verify spawn_cash picks the only valid cell on an almost full board.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main_module.Point
        board_last = self.main_module.BOARD_CELLS - 1
        only_free = point(board_last, board_last)
        occupied = [
            point(x, y)
            for y in range(self.main_module.BOARD_CELLS)
            for x in range(self.main_module.BOARD_CELLS)
            if point(x, y) != only_free
        ]

        spawned = self.game.spawn_cash(occupied)

        self.assertEqual(only_free, spawned)

    def test_spawn_cash_always_stays_in_bounds_and_avoids_snake_segments(self) -> None:
        """Verify repeated cash spawns are valid and never overlap snake cells.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main_module.Point
        snake = [point(x, 0) for x in range(self.main_module.BOARD_CELLS)]

        for _ in range(50):
            spawned = self.game.spawn_cash(snake)
            self.assertNotIn(spawned, snake)
            self.assertGreaterEqual(spawned.x, 0)
            self.assertLess(spawned.x, self.main_module.BOARD_CELLS)
            self.assertGreaterEqual(spawned.y, 0)
            self.assertLess(spawned.y, self.main_module.BOARD_CELLS)

    def test_reset_state_restores_baseline_runtime_state(self) -> None:
        """Verify reset_state clears score, flags, speed, and HUD baseline values.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main_module.Point
        self.game.score = 90
        self.game.tick_ms = self.main_module.MIN_TICK_MS
        self.game.running = True
        self.game.game_over = True
        self.game.snake = [point(1, 1)]
        self.game.direction = point(1, 0)
        self.game.pending_direction = point(1, 0)
        self.game.status_text.textContent = "Changed"
        self.game.score_value.textContent = "90"

        self.game.reset_state()

        self.assertEqual(0, self.game.score)
        self.assertEqual(self.main_module.BASE_TICK_MS, self.game.tick_ms)
        self.assertFalse(self.game.running)
        self.assertFalse(self.game.game_over)
        self.assertEqual("0", self.game.score_value.textContent)
        self.assertEqual("Waiting for your first run.", self.game.status_text.textContent)
        self.assertEqual(3, len(self.game.snake))
        self.assertEqual(point(0, -1), self.game.direction)
        self.assertEqual(point(0, -1), self.game.pending_direction)
        self.assertNotIn(self.game.cash, self.game.snake)

    def test_restart_game_resets_state_then_starts_new_run(self) -> None:
        """Verify restart_game performs a reset and transitions to running state.

        Args:
            None.

        Returns:
            None.
        """
        self.game.score = 50
        self.game.game_over = True
        self.game.running = False
        self.game.animation_handle = 1

        self.game.restart_game()

        self.assertTrue(self.game.running)
        self.assertFalse(self.game.game_over)
        self.assertEqual(0, self.game.score)
        self.assertEqual("Restart Run", self.game.start_button.textContent)
        self.assertEqual("Live run. Stay sharp and keep stacking.", self.game.status_text.textContent)
        self.assertNotIn(self.game.cash, self.game.snake)


if __name__ == "__main__":
    unittest.main()
