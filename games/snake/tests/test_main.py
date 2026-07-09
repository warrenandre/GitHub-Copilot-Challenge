"""Unit tests for Snake Cash Rush gameplay logic.

This test module validates core `SnakeCashRush` behavior without requiring a
real browser runtime. It injects fake `js` and `pyodide.ffi` modules so the
game class can be imported and exercised as pure Python.
"""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


class FakeClassList:
    """Minimal class list implementation for fake DOM elements.

    Attributes:
        values: Current set of applied CSS class names.
    """

    def __init__(self) -> None:
        """Initialize an empty fake class list.

        Args:
            None.

        Returns:
            None.
        """
        self.values: set[str] = set()

    def add(self, value: str) -> None:
        """Add a class name.

        Args:
            value: CSS class name to add.

        Returns:
            None.
        """
        self.values.add(value)

    def remove(self, value: str) -> None:
        """Remove a class name if present.

        Args:
            value: CSS class name to remove.

        Returns:
            None.
        """
        self.values.discard(value)


class FakeContext:
    """No-op canvas 2D context used by render calls during tests."""

    def clearRect(self, *_args) -> None:
        """No-op clear rectangle call.

        Args:
            *_args: Ignored drawing arguments.

        Returns:
            None.
        """

    def fillRect(self, *_args) -> None:
        """No-op fill rectangle call.

        Args:
            *_args: Ignored drawing arguments.

        Returns:
            None.
        """

    def beginPath(self) -> None:
        """No-op begin path call.

        Args:
            None.

        Returns:
            None.
        """

    def moveTo(self, *_args) -> None:
        """No-op move call.

        Args:
            *_args: Ignored drawing arguments.

        Returns:
            None.
        """

    def lineTo(self, *_args) -> None:
        """No-op line call.

        Args:
            *_args: Ignored drawing arguments.

        Returns:
            None.
        """

    def stroke(self) -> None:
        """No-op stroke call.

        Args:
            None.

        Returns:
            None.
        """

    def save(self) -> None:
        """No-op save state call.

        Args:
            None.

        Returns:
            None.
        """

    def restore(self) -> None:
        """No-op restore state call.

        Args:
            None.

        Returns:
            None.
        """

    def fill(self) -> None:
        """No-op fill path call.

        Args:
            None.

        Returns:
            None.
        """

    def arc(self, *_args) -> None:
        """No-op arc call.

        Args:
            *_args: Ignored drawing arguments.

        Returns:
            None.
        """

    def fillText(self, *_args) -> None:
        """No-op text draw call.

        Args:
            *_args: Ignored drawing arguments.

        Returns:
            None.
        """

    def quadraticCurveTo(self, *_args) -> None:
        """No-op curve call.

        Args:
            *_args: Ignored drawing arguments.

        Returns:
            None.
        """

    def closePath(self) -> None:
        """No-op close path call.

        Args:
            None.

        Returns:
            None.
        """


class FakeElement:
    """Simplified DOM element with text, classes, and event listeners."""

    def __init__(self, with_parent: bool = False) -> None:
        """Create a fake element.

        Args:
            with_parent: Whether to include a parent element.

        Returns:
            None.
        """
        self.textContent = ""
        self.classList = FakeClassList()
        self.parentElement = FakeElement() if with_parent else None
        self._listeners: dict[str, list[object]] = {}

    def addEventListener(self, event_name: str, callback: object) -> None:
        """Store an event listener callback.

        Args:
            event_name: Event type name.
            callback: Listener callback object.

        Returns:
            None.
        """
        self._listeners.setdefault(event_name, []).append(callback)


class FakeCanvas(FakeElement):
    """Canvas element that returns a fake 2D context."""

    def __init__(self) -> None:
        """Initialize a fake canvas.

        Args:
            None.

        Returns:
            None.
        """
        super().__init__()
        self._context = FakeContext()

    def getContext(self, _kind: str) -> FakeContext:
        """Return the fake rendering context.

        Args:
            _kind: Requested context kind.

        Returns:
            The fake 2D context.
        """
        return self._context


class FakeDocument:
    """Fake browser document that serves known game elements by ID."""

    def __init__(self) -> None:
        """Build all DOM nodes required by SnakeCashRush.

        Args:
            None.

        Returns:
            None.
        """
        self._elements: dict[str, FakeElement] = {
            "gameCanvas": FakeCanvas(),
            "scoreValue": FakeElement(with_parent=True),
            "bestScoreValue": FakeElement(with_parent=True),
            "statusText": FakeElement(),
            "activePowerValue": FakeElement(),
            "startButton": FakeElement(),
            "gameOverlay": FakeElement(),
            "overlayKicker": FakeElement(),
            "overlayTitle": FakeElement(),
            "overlayMessage": FakeElement(),
            "overlayButton": FakeElement(),
            "cashBurst": FakeElement(),
        }
        self._listeners: dict[str, list[object]] = {}

    def getElementById(self, element_id: str) -> FakeElement:
        """Return a fake DOM element by ID.

        Args:
            element_id: DOM id requested by the game.

        Returns:
            The matching fake element.
        """
        return self._elements[element_id]

    def addEventListener(self, event_name: str, callback: object) -> None:
        """Register document-level event callbacks.

        Args:
            event_name: Event type name.
            callback: Listener callback object.

        Returns:
            None.
        """
        self._listeners.setdefault(event_name, []).append(callback)

    def removeEventListener(self, event_name: str, callback: object) -> None:
        """Remove a previously registered event callback.

        Args:
            event_name: Event type name.
            callback: Listener callback object.

        Returns:
            None.
        """
        listeners = self._listeners.get(event_name, [])
        if callback in listeners:
            listeners.remove(callback)


class FakeBridge:
    """Fake JS bridge for RAF and score persistence hooks."""

    def __init__(self) -> None:
        """Initialize bridge state.

        Args:
            None.

        Returns:
            None.
        """
        self._best_score = 0

    def raf(self, _callback: object) -> int:
        """Return a placeholder animation frame handle.

        Args:
            _callback: Animation callback reference.

        Returns:
            Constant fake handle.
        """
        return 1

    def cancelRaf(self, _handle: int) -> None:
        """No-op cancellation for animation frame handles.

        Args:
            _handle: Animation frame handle.

        Returns:
            None.
        """

    def readBestScore(self) -> int:
        """Return stored best score value.

        Args:
            None.

        Returns:
            Current fake best score.
        """
        return self._best_score

    def writeBestScore(self, score: int) -> None:
        """Store a best score value.

        Args:
            score: New best score to persist.

        Returns:
            None.
        """
        self._best_score = score


class FakeWindow:
    """Fake browser window with bridge and timeout behavior."""

    def __init__(self) -> None:
        """Initialize fake window services.

        Args:
            None.

        Returns:
            None.
        """
        self.snakeCashRushBridge = FakeBridge()

    def setTimeout(self, callback, _delay_ms: int) -> None:
        """Execute callback immediately for deterministic tests.

        Args:
            callback: Callable callback to execute.
            _delay_ms: Delay in milliseconds.

        Returns:
            None.
        """
        callback()


def load_main_module() -> types.ModuleType:
    """Load main.py with fake JS/Pyodide runtime modules.

    Args:
        None.

    Returns:
        Imported main module object.
    """
    fake_js = types.ModuleType("js")
    fake_js.document = FakeDocument()
    fake_js.window = FakeWindow()

    fake_pyodide = types.ModuleType("pyodide")
    fake_ffi = types.ModuleType("pyodide.ffi")
    fake_ffi.create_proxy = lambda value: value
    fake_pyodide.ffi = fake_ffi

    sys.modules["js"] = fake_js
    sys.modules["pyodide"] = fake_pyodide
    sys.modules["pyodide.ffi"] = fake_ffi

    module_name = "snake_main_under_test"
    if module_name in sys.modules:
        del sys.modules[module_name]

    main_path = Path(__file__).resolve().parents[1] / "src" / "main.py"
    spec = importlib.util.spec_from_file_location(module_name, str(main_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load SnakeCashRush module for testing.")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class SnakeCashRushTests(unittest.TestCase):
    """Unit tests for movement, collisions, and scoring."""

    def setUp(self) -> None:
        """Create a fresh game instance for each test.

        Args:
            None.

        Returns:
            None.
        """
        self.main = load_main_module()
        self.game = self.main.SnakeCashRush()

    def test_advance_moves_snake_forward_without_changing_length(self) -> None:
        """Verify one normal tick advances the snake by one cell.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main.Point
        self.game.snake = [point(5, 5), point(6, 5), point(7, 5)]
        self.game.direction = point(1, 0)
        self.game.pending_direction = point(1, 0)
        self.game.cash = point(10, 10)

        self.game.advance()

        self.assertEqual(self.game.snake, [point(6, 5), point(7, 5), point(8, 5)])
        self.assertEqual(self.game.score, 0)
        self.assertFalse(self.game.game_over)

    def test_advance_hits_wall_and_ends_game(self) -> None:
        """Verify wall collisions end the run immediately.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main.Point
        edge_x = self.main.BOARD_CELLS - 1
        self.game.snake = [point(edge_x - 2, 4), point(edge_x - 1, 4), point(edge_x, 4)]
        self.game.direction = point(1, 0)
        self.game.pending_direction = point(1, 0)
        self.game.cash = point(0, 0)
        self.game.running = True

        self.game.advance()

        self.assertTrue(self.game.game_over)
        self.assertFalse(self.game.running)

    def test_advance_hits_body_and_ends_game(self) -> None:
        """Verify self-collision is detected and ends the run.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main.Point
        self.game.snake = [
            point(5, 5),
            point(6, 5),
            point(7, 5),
            point(7, 6),
            point(6, 6),
        ]
        self.game.direction = point(0, -1)
        self.game.pending_direction = point(0, -1)
        self.game.cash = point(0, 0)
        self.game.running = True

        self.game.advance()

        self.assertTrue(self.game.game_over)
        self.assertFalse(self.game.running)

    def test_collecting_cash_increases_score_and_length(self) -> None:
        """Verify collecting cash increments score and grows the snake.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main.Point
        self.main.random = lambda: 1.0
        self.game.snake = [point(5, 5), point(6, 5), point(7, 5)]
        self.game.direction = point(1, 0)
        self.game.pending_direction = point(1, 0)
        self.game.cash = point(8, 5)

        self.game.advance()

        self.assertEqual(self.game.score, self.main.SCORE_PER_BILL)
        self.assertEqual(len(self.game.snake), 4)
        self.assertEqual(self.game.best_score, self.main.SCORE_PER_BILL)

    def test_double_points_power_up_doubles_cash_value(self) -> None:
        """Verify score tracking applies double-points power-up correctly.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main.Point
        self.main.random = lambda: 1.0
        self.game.active_power = self.main.ActivePower(kind="double_points", remaining_ticks=99)
        self.game.snake = [point(9, 8), point(10, 8), point(11, 8)]
        self.game.direction = point(1, 0)
        self.game.pending_direction = point(1, 0)
        self.game.cash = point(12, 8)

        self.game.advance()

        self.assertEqual(self.game.score, self.main.SCORE_PER_BILL * 2)

    def test_advance_ends_game_for_all_boundary_collisions(self) -> None:
        """Verify crossing any board boundary ends the run.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main.Point
        max_index = self.main.BOARD_CELLS - 1
        cases = [
            ([point(2, 3), point(1, 3), point(0, 3)], point(-1, 0)),
            ([point(max_index - 2, 4), point(max_index - 1, 4), point(max_index, 4)], point(1, 0)),
            ([point(3, 2), point(3, 1), point(3, 0)], point(0, -1)),
            ([point(4, max_index - 2), point(4, max_index - 1), point(4, max_index)], point(0, 1)),
        ]

        for snake, direction in cases:
            with self.subTest(snake=snake, direction=direction):
                self.game.reset_state()
                self.game.snake = snake
                self.game.direction = direction
                self.game.pending_direction = direction
                self.game.cash = point(10, 10)
                self.game.running = True

                self.game.advance()

                self.assertTrue(self.game.game_over)
                self.assertFalse(self.game.running)

    def test_moving_into_vacated_tail_cell_does_not_count_as_self_collision(self) -> None:
        """Verify moving into the old tail position is safe on non-collect moves.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main.Point
        self.game.snake = [point(5, 5), point(6, 5), point(6, 4), point(5, 4)]
        self.game.direction = point(0, 1)
        self.game.pending_direction = point(0, 1)
        self.game.cash = point(0, 0)
        self.game.running = True

        self.game.advance()

        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.snake, [point(6, 5), point(6, 4), point(5, 4), point(5, 5)])

    def test_spawn_cash_returns_valid_unoccupied_cell(self) -> None:
        """Verify cash spawning stays in bounds and avoids snake segments.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main.Point
        self.main.choice = lambda values: values[0]
        occupied = [
            point(0, 0),
            point(1, 0),
            point(2, 0),
            point(3, 0),
            point(4, 0),
            point(5, 0),
        ]

        spawned = self.game.spawn_cash(occupied)

        self.assertNotIn(spawned, occupied)
        self.assertGreaterEqual(spawned.x, 0)
        self.assertGreaterEqual(spawned.y, 0)
        self.assertLess(spawned.x, self.main.BOARD_CELLS)
        self.assertLess(spawned.y, self.main.BOARD_CELLS)

    def test_reset_state_restores_initial_runtime_values(self) -> None:
        """Verify reset clears transient game state and restores defaults.

        Args:
            None.

        Returns:
            None.
        """
        point = self.main.Point
        center = self.main.BOARD_CELLS // 2
        self.game.score = 120
        self.game.running = True
        self.game.game_over = True
        self.game.active_power = self.main.ActivePower(kind="speed_boost", remaining_ticks=2)
        self.game.power_up = self.main.PowerUp(kind="double_points", position=point(1, 1))
        self.game.snake = [point(2, 2), point(3, 2), point(4, 2)]
        self.game.direction = point(1, 0)
        self.game.pending_direction = point(1, 0)

        self.game.reset_state()

        self.assertEqual(self.game.score, 0)
        self.assertFalse(self.game.running)
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.tick_ms, self.main.BASE_TICK_MS)
        self.assertIsNone(self.game.active_power)
        self.assertIsNone(self.game.power_up)
        self.assertEqual(
            self.game.snake,
            [point(center, center + 1), point(center, center), point(center, center - 1)],
        )
        self.assertEqual(self.game.direction, point(0, -1))
        self.assertEqual(self.game.pending_direction, point(0, -1))
        self.assertEqual(self.game.score_value.textContent, "0")
        self.assertEqual(self.game.active_power_value.textContent, "None")


if __name__ == "__main__":
    unittest.main()