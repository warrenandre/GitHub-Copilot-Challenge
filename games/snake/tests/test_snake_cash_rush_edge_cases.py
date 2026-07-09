from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any, Callable, Generator

import pytest


class FakeClassList:
    def __init__(self) -> None:
        """Initialize a lightweight class list tracker.

        Args:
            None.

        Returns:
            None.
        """
        self._classes: set[str] = set()

    def add(self, class_name: str) -> None:
        """Add a class name.

        Args:
            class_name: CSS class to add.

        Returns:
            None.
        """
        self._classes.add(class_name)

    def remove(self, class_name: str) -> None:
        """Remove a class name when present.

        Args:
            class_name: CSS class to remove.

        Returns:
            None.
        """
        self._classes.discard(class_name)


class FakeCanvasContext:
    def __init__(self) -> None:
        """Initialize a no-op canvas context.

        Args:
            None.

        Returns:
            None.
        """
        self.fillStyle = ""
        self.strokeStyle = ""
        self.lineWidth = 1
        self.shadowColor = ""
        self.shadowBlur = 0
        self.font = ""
        self.textAlign = ""
        self.textBaseline = ""

    def __getattr__(self, _name: str) -> Callable[..., None]:
        """Return a callable no-op for unknown canvas methods.

        Args:
            _name: Requested attribute name.

        Returns:
            A function that ignores all arguments.
        """

        def _noop(*_args: Any, **_kwargs: Any) -> None:
            """Ignore all calls for canvas operations.

            Args:
                *_args: Positional arguments.
                **_kwargs: Keyword arguments.

            Returns:
                None.
            """
            return None

        return _noop


class FakeElement:
    def __init__(self, element_id: str = "") -> None:
        """Initialize a fake DOM element.

        Args:
            element_id: Element identifier.

        Returns:
            None.
        """
        self.element_id = element_id
        self.textContent = ""
        self.classList = FakeClassList()
        self.parentElement = self

    def addEventListener(self, _event: str, _callback: Callable[..., Any]) -> None:
        """Register a no-op event listener.

        Args:
            _event: Event name.
            _callback: Callback function.

        Returns:
            None.
        """
        return None

    def getContext(self, _context_name: str) -> FakeCanvasContext:
        """Return a fake canvas context.

        Args:
            _context_name: Canvas context kind.

        Returns:
            Fake drawing context.
        """
        return FakeCanvasContext()


class FakeSnakeCashRushBridge:
    def __init__(self) -> None:
        """Initialize in-memory bridge storage.

        Args:
            None.

        Returns:
            None.
        """
        self._best_score = 0

    def readBestScore(self) -> int:
        """Read a stored best score.

        Args:
            None.

        Returns:
            The current best score.
        """
        return self._best_score

    def writeBestScore(self, score: int) -> None:
        """Persist a best score value.

        Args:
            score: Best score value.

        Returns:
            None.
        """
        self._best_score = score

    def raf(self, _callback: Callable[..., Any]) -> int:
        """Return a placeholder animation handle.

        Args:
            _callback: Animation callback.

        Returns:
            Placeholder handle.
        """
        return 1

    def cancelRaf(self, _handle: int) -> None:
        """Cancel an animation handle as a no-op.

        Args:
            _handle: Animation handle.

        Returns:
            None.
        """
        return None


class FakeWindow:
    def __init__(self) -> None:
        """Initialize fake window with a bridge.

        Args:
            None.

        Returns:
            None.
        """
        self.snakeCashRushBridge = FakeSnakeCashRushBridge()

    def setTimeout(self, callback: Callable[..., Any], _delay_ms: int) -> int:
        """Run callbacks immediately for deterministic tests.

        Args:
            callback: Callback to execute.
            _delay_ms: Delay in milliseconds.

        Returns:
            Placeholder timeout id.
        """
        callback()
        return 1


class FakeDocument:
    def __init__(self) -> None:
        """Initialize fake document element registry.

        Args:
            None.

        Returns:
            None.
        """
        self._elements: dict[str, FakeElement] = {
            "gameCanvas": FakeElement("gameCanvas"),
            "scoreValue": FakeElement("scoreValue"),
            "bestScoreValue": FakeElement("bestScoreValue"),
            "statusText": FakeElement("statusText"),
            "powerUpStatus": FakeElement("powerUpStatus"),
            "startButton": FakeElement("startButton"),
            "gameOverlay": FakeElement("gameOverlay"),
            "overlayKicker": FakeElement("overlayKicker"),
            "overlayTitle": FakeElement("overlayTitle"),
            "overlayMessage": FakeElement("overlayMessage"),
            "overlayButton": FakeElement("overlayButton"),
            "cashBurst": FakeElement("cashBurst"),
        }

    def getElementById(self, element_id: str) -> FakeElement:
        """Return an element by id, creating one when absent.

        Args:
            element_id: Requested DOM id.

        Returns:
            Fake element instance.
        """
        if element_id not in self._elements:
            self._elements[element_id] = FakeElement(element_id)
        return self._elements[element_id]

    def addEventListener(self, _event: str, _callback: Callable[..., Any]) -> None:
        """Register document event listener as a no-op.

        Args:
            _event: Event name.
            _callback: Callback function.

        Returns:
            None.
        """
        return None

    def removeEventListener(self, _event: str, _callback: Callable[..., Any]) -> None:
        """Remove document listener as a no-op.

        Args:
            _event: Event name.
            _callback: Callback function.

        Returns:
            None.
        """
        return None


def load_main_module() -> types.ModuleType:
    """Load the SnakeCashRush module with browser stubs injected.

    Args:
        None.

    Returns:
        Imported module object for `games/snake/src/main.py`.
    """
    fake_js = types.ModuleType("js")
    fake_js.document = FakeDocument()
    fake_js.window = FakeWindow()
    sys.modules["js"] = fake_js

    fake_pyodide = types.ModuleType("pyodide")
    fake_pyodide_ffi = types.ModuleType("pyodide.ffi")

    def create_proxy(callback: Callable[..., Any]) -> Callable[..., Any]:
        """Return the callback directly for test proxies.

        Args:
            callback: Callback function.

        Returns:
            Same callback object.
        """
        return callback

    fake_pyodide_ffi.create_proxy = create_proxy
    sys.modules["pyodide"] = fake_pyodide
    sys.modules["pyodide.ffi"] = fake_pyodide_ffi

    main_path = Path(__file__).resolve().parents[1] / "src" / "main.py"
    spec = importlib.util.spec_from_file_location("snake_main", main_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def snake_module() -> types.ModuleType:
    """Provide a loaded snake module with test-safe browser stubs.

    Args:
        None.

    Returns:
        Imported snake module.
    """
    return load_main_module()


@pytest.fixture
def snake_game(snake_module: types.ModuleType) -> Generator[Any, None, None]:
    """Provide a fresh SnakeCashRush instance for each test.

    Args:
        snake_module: Imported snake game module.

    Returns:
        Generator yielding a game instance.
    """
    game = snake_module.SnakeCashRush()
    game.try_spawn_power_up = lambda: None
    yield game
    game.destroy()


def test_boundary_collision_ends_run(snake_game: Any, snake_module: types.ModuleType) -> None:
    """Ensure moving beyond board bounds ends the current run.

    Args:
        snake_game: Snake game instance.
        snake_module: Imported snake game module.

    Returns:
        None.
    """
    point = snake_module.Point
    snake_game.running = True
    snake_game.game_over = False
    snake_game.direction = point(0, -1)
    snake_game.pending_direction = point(0, -1)
    snake_game.snake = [point(0, 2), point(0, 1), point(0, 0)]
    snake_game.cash = point(10, 10)

    snake_game.advance()

    assert snake_game.game_over is True
    assert snake_game.running is False


def test_self_collision_ends_run(snake_game: Any, snake_module: types.ModuleType) -> None:
    """Ensure entering the snake body triggers game over.

    Args:
        snake_game: Snake game instance.
        snake_module: Imported snake game module.

    Returns:
        None.
    """
    point = snake_module.Point
    snake_game.running = True
    snake_game.game_over = False
    snake_game.direction = point(0, -1)
    snake_game.pending_direction = point(0, -1)
    snake_game.snake = [point(4, 5), point(5, 5), point(6, 5), point(6, 6), point(5, 6)]
    snake_game.cash = point(10, 10)

    snake_game.advance()

    assert snake_game.game_over is True
    assert snake_game.running is False


def test_spawn_cash_avoids_snake_and_power_up(snake_game: Any, snake_module: types.ModuleType) -> None:
    """Ensure cash always spawns within bounds and on free cells.

    Args:
        snake_game: Snake game instance.
        snake_module: Imported snake game module.

    Returns:
        None.
    """
    point = snake_module.Point
    power_up = snake_module.PowerUp
    snake_cells = [point(0, 0), point(1, 0), point(2, 0), point(3, 0)]
    snake_game.power_up = power_up(kind=snake_module.POWER_UP_SPEED, position=point(4, 0))

    spawned_cash = snake_game.spawn_cash(snake_cells)

    assert spawned_cash not in snake_cells
    assert spawned_cash != snake_game.power_up.position
    assert 0 <= spawned_cash.x < snake_module.BOARD_CELLS
    assert 0 <= spawned_cash.y < snake_module.BOARD_CELLS


def test_reset_state_reinitializes_run_state(snake_game: Any, snake_module: types.ModuleType) -> None:
    """Ensure reset restores defaults for a fresh game run.

    Args:
        snake_game: Snake game instance.
        snake_module: Imported snake game module.

    Returns:
        None.
    """
    point = snake_module.Point
    power_up = snake_module.PowerUp
    snake_game.score = 90
    snake_game.running = True
    snake_game.game_over = True
    snake_game.tick_ms = 75
    snake_game.snake = [point(2, 2), point(2, 3), point(2, 4), point(2, 5)]
    snake_game.direction = point(1, 0)
    snake_game.pending_direction = point(1, 0)
    snake_game.power_up = power_up(kind=snake_module.POWER_UP_DOUBLE_POINTS, position=point(10, 10))
    snake_game.effect_timers_ms = {
        snake_module.POWER_UP_SPEED: 1200,
        snake_module.POWER_UP_INVINCIBLE: 800,
        snake_module.POWER_UP_DOUBLE_POINTS: 500,
    }

    snake_game.reset_state()

    center = snake_module.BOARD_CELLS // 2
    assert snake_game.score == 0
    assert snake_game.running is False
    assert snake_game.game_over is False
    assert snake_game.tick_ms == snake_module.BASE_TICK_MS
    assert snake_game.direction == point(0, -1)
    assert snake_game.pending_direction == point(0, -1)
    assert snake_game.power_up is None
    assert snake_game.snake == [point(center, center + 1), point(center, center), point(center, center - 1)]
    assert all(value == 0 for value in snake_game.effect_timers_ms.values())
