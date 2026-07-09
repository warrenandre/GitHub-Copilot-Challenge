from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


class _FakeClassList:
    def __init__(self) -> None:
        self.classes: set[str] = set()

    def add(self, name: str) -> None:
        self.classes.add(name)

    def remove(self, name: str) -> None:
        self.classes.discard(name)


class _FakeElement:
    def __init__(self) -> None:
        self.textContent = ""
        self.parentElement = self
        self.classList = _FakeClassList()

    def addEventListener(self, _event: str, _handler) -> None:
        return None


class _FakeCanvas(_FakeElement):
    def __init__(self) -> None:
        super().__init__()
        self._ctx = _FakeCanvasContext()

    def getContext(self, _context_name: str):
        return self._ctx


class _FakeCanvasContext:
    def clearRect(self, *_args) -> None:
        return None

    def fillRect(self, *_args) -> None:
        return None

    def beginPath(self) -> None:
        return None

    def moveTo(self, *_args) -> None:
        return None

    def lineTo(self, *_args) -> None:
        return None

    def stroke(self) -> None:
        return None

    def save(self) -> None:
        return None

    def restore(self) -> None:
        return None

    def fill(self) -> None:
        return None

    def arc(self, *_args) -> None:
        return None

    def fillText(self, *_args) -> None:
        return None

    def quadraticCurveTo(self, *_args) -> None:
        return None

    def closePath(self) -> None:
        return None


class _FakeDocument:
    def __init__(self) -> None:
        self._elements = {
            "gameCanvas": _FakeCanvas(),
            "scoreValue": _FakeElement(),
            "bestScoreValue": _FakeElement(),
            "statusText": _FakeElement(),
            "startButton": _FakeElement(),
            "gameOverlay": _FakeElement(),
            "overlayKicker": _FakeElement(),
            "overlayTitle": _FakeElement(),
            "overlayMessage": _FakeElement(),
            "overlayButton": _FakeElement(),
            "cashBurst": _FakeElement(),
        }

    def getElementById(self, element_id: str):
        return self._elements[element_id]

    def addEventListener(self, _event: str, _handler) -> None:
        return None

    def removeEventListener(self, _event: str, _handler) -> None:
        return None


class _FakeBridge:
    def __init__(self) -> None:
        self.best_score = 0

    def raf(self, _callback) -> int:
        return 1

    def cancelRaf(self, _handle: int) -> None:
        return None

    def readBestScore(self) -> int:
        return self.best_score

    def writeBestScore(self, score: int) -> None:
        self.best_score = score


class _FakeWindow:
    def __init__(self) -> None:
        self.snakeCashRushBridge = _FakeBridge()

    def setTimeout(self, callback, _ms: int):
        callback()
        return 1


@pytest.fixture(scope="module")
def snake_module():
    module_path = Path(__file__).resolve().parents[1] / "src" / "main.py"

    js_module = types.ModuleType("js")
    js_module.document = _FakeDocument()
    js_module.window = _FakeWindow()

    pyodide_module = types.ModuleType("pyodide")
    ffi_module = types.ModuleType("pyodide.ffi")
    ffi_module.create_proxy = lambda fn: fn

    sys.modules["js"] = js_module
    sys.modules["pyodide"] = pyodide_module
    sys.modules["pyodide.ffi"] = ffi_module

    spec = importlib.util.spec_from_file_location("snake_main_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_game(module):
    game = module.SnakeCashRush.__new__(module.SnakeCashRush)

    game.direction = module.Point(1, 0)
    game.pending_direction = module.Point(1, 0)
    game.snake = [module.Point(3, 5), module.Point(4, 5), module.Point(5, 5)]
    game.cash = module.Point(9, 9)
    game.score = 0
    game.best_score = 0
    game.tick_ms = module.BASE_TICK_MS
    game.score_value = SimpleNamespace(textContent="0")
    game.status_text = SimpleNamespace(textContent="")

    calls = {
        "end_game": 0,
        "flash_score": 0,
        "show_cash_burst": 0,
        "sync_best_score": 0,
    }

    def _end_game() -> None:
        calls["end_game"] += 1

    def _flash_score() -> None:
        calls["flash_score"] += 1

    def _show_cash_burst() -> None:
        calls["show_cash_burst"] += 1

    def _sync_best_score() -> None:
        calls["sync_best_score"] += 1

    game.end_game = _end_game
    game.flash_score = _flash_score
    game.show_cash_burst = _show_cash_burst
    game.sync_best_score = _sync_best_score
    game.spawn_cash = lambda _snake: module.Point(1, 1)

    return game, calls


def test_move_uses_pending_direction_and_keeps_length(snake_module):
    game, calls = _make_game(snake_module)

    game.pending_direction = snake_module.Point(0, 1)
    snake_module.SnakeCashRush.advance(game)

    assert game.direction == snake_module.Point(0, 1)
    assert len(game.snake) == 3
    assert game.snake[-1] == snake_module.Point(5, 6)
    assert game.score == 0
    assert game.score_value.textContent == "0"
    assert calls["end_game"] == 0


def test_collecting_cash_increases_score_grows_snake_and_speeds_up(snake_module):
    game, calls = _make_game(snake_module)

    game.cash = snake_module.Point(6, 5)
    snake_module.SnakeCashRush.advance(game)

    assert len(game.snake) == 4
    assert game.score == snake_module.SCORE_PER_BILL
    assert game.score_value.textContent == str(snake_module.SCORE_PER_BILL)
    assert game.tick_ms == snake_module.BASE_TICK_MS - snake_module.SPEED_STEP_MS
    assert game.cash == snake_module.Point(1, 1)
    assert calls["flash_score"] == 1
    assert calls["show_cash_burst"] == 1
    assert calls["sync_best_score"] == 1
    assert calls["end_game"] == 0


def test_advance_ends_game_on_wall_collision(snake_module):
    game, calls = _make_game(snake_module)

    edge = snake_module.BOARD_CELLS - 1
    game.snake = [snake_module.Point(edge - 2, 3), snake_module.Point(edge - 1, 3), snake_module.Point(edge, 3)]
    game.direction = snake_module.Point(1, 0)
    game.pending_direction = snake_module.Point(1, 0)

    snake_module.SnakeCashRush.advance(game)

    assert calls["end_game"] == 1


def test_advance_ends_game_on_self_collision(snake_module):
    game, calls = _make_game(snake_module)

    game.snake = [snake_module.Point(2, 2), snake_module.Point(3, 2), snake_module.Point(3, 3)]
    game.direction = snake_module.Point(0, -1)
    game.pending_direction = snake_module.Point(0, -1)

    snake_module.SnakeCashRush.advance(game)

    assert calls["end_game"] == 1


def test_hit_wall_detects_in_and_out_of_bounds_points(snake_module):
    game, _ = _make_game(snake_module)

    assert snake_module.SnakeCashRush.hit_wall(game, snake_module.Point(-1, 0)) is True
    assert snake_module.SnakeCashRush.hit_wall(game, snake_module.Point(0, -1)) is True
    assert snake_module.SnakeCashRush.hit_wall(
        game, snake_module.Point(snake_module.BOARD_CELLS, 0)
    ) is True
    assert snake_module.SnakeCashRush.hit_wall(
        game, snake_module.Point(0, snake_module.BOARD_CELLS)
    ) is True
    assert snake_module.SnakeCashRush.hit_wall(
        game, snake_module.Point(snake_module.BOARD_CELLS - 1, snake_module.BOARD_CELLS - 1)
    ) is False


def test_spawn_cash_returns_origin_when_board_is_full(snake_module):
    game, _ = _make_game(snake_module)

    full_board_snake = [
        snake_module.Point(x, y)
        for y in range(snake_module.BOARD_CELLS)
        for x in range(snake_module.BOARD_CELLS)
    ]

    spawn = snake_module.SnakeCashRush.spawn_cash(game, full_board_snake)

    assert spawn == snake_module.Point(0, 0)


def test_is_reverse_identifies_opposite_direction(snake_module):
    game, _ = _make_game(snake_module)

    assert (
        snake_module.SnakeCashRush.is_reverse(
            game,
            snake_module.Point(-1, 0),
            snake_module.Point(1, 0),
        )
        is True
    )
    assert (
        snake_module.SnakeCashRush.is_reverse(
            game,
            snake_module.Point(0, 1),
            snake_module.Point(1, 0),
        )
        is False
    )


def test_restart_game_calls_cancel_reset_and_start_in_order(snake_module):
    game = snake_module.SnakeCashRush.__new__(snake_module.SnakeCashRush)
    calls: list[str] = []

    game.cancel_animation = lambda: calls.append("cancel")
    game.reset_state = lambda: calls.append("reset")
    game.start_game = lambda: calls.append("start")

    snake_module.SnakeCashRush.restart_game(game)

    assert calls == ["cancel", "reset", "start"]


def test_handle_primary_action_starts_game_when_idle(snake_module):
    game = snake_module.SnakeCashRush.__new__(snake_module.SnakeCashRush)
    calls = {"start": 0, "restart": 0}

    game.running = False
    game.game_over = False
    game.start_game = lambda: calls.__setitem__("start", calls["start"] + 1)
    game.restart_game = lambda: calls.__setitem__("restart", calls["restart"] + 1)

    snake_module.SnakeCashRush.handle_primary_action(game)

    assert calls["start"] == 1
    assert calls["restart"] == 0


def test_handle_primary_action_restarts_when_running_or_game_over(snake_module):
    game = snake_module.SnakeCashRush.__new__(snake_module.SnakeCashRush)
    calls = {"start": 0, "restart": 0}

    game.running = True
    game.game_over = False
    game.start_game = lambda: calls.__setitem__("start", calls["start"] + 1)
    game.restart_game = lambda: calls.__setitem__("restart", calls["restart"] + 1)

    snake_module.SnakeCashRush.handle_primary_action(game)

    assert calls["start"] == 0
    assert calls["restart"] == 1


def test_handle_keydown_restart_shortcut_calls_restart(snake_module):
    game = snake_module.SnakeCashRush.__new__(snake_module.SnakeCashRush)
    calls = {"restart": 0}

    game.restart_game = lambda: calls.__setitem__("restart", calls["restart"] + 1)
    game.running = True
    game.game_over = False
    game.direction = snake_module.Point(1, 0)
    game.pending_direction = snake_module.Point(1, 0)

    snake_module.SnakeCashRush.handle_keydown(game, SimpleNamespace(key="r"))

    assert calls["restart"] == 1


def test_handle_keydown_starts_game_and_updates_direction_on_valid_input(snake_module):
    game = snake_module.SnakeCashRush.__new__(snake_module.SnakeCashRush)
    calls = {"start": 0}

    game.running = False
    game.game_over = False
    game.direction = snake_module.Point(1, 0)
    game.pending_direction = snake_module.Point(1, 0)

    def _start() -> None:
        calls["start"] += 1
        game.running = True

    game.start_game = _start

    snake_module.SnakeCashRush.handle_keydown(game, SimpleNamespace(key="ArrowDown"))

    assert calls["start"] == 1
    assert game.pending_direction == snake_module.Point(0, 1)


def test_handle_keydown_ignores_reverse_direction(snake_module):
    game = snake_module.SnakeCashRush.__new__(snake_module.SnakeCashRush)

    game.running = True
    game.game_over = False
    game.direction = snake_module.Point(1, 0)
    game.pending_direction = snake_module.Point(1, 0)
    game.start_game = lambda: None

    snake_module.SnakeCashRush.handle_keydown(game, SimpleNamespace(key="ArrowLeft"))

    assert game.pending_direction == snake_module.Point(1, 0)


def test_handle_keydown_ignores_unmapped_key_without_starting(snake_module):
    game = snake_module.SnakeCashRush.__new__(snake_module.SnakeCashRush)
    calls = {"start": 0}

    game.running = False
    game.game_over = False
    game.direction = snake_module.Point(0, -1)
    game.pending_direction = snake_module.Point(0, -1)
    game.start_game = lambda: calls.__setitem__("start", calls["start"] + 1)

    snake_module.SnakeCashRush.handle_keydown(game, SimpleNamespace(key="q"))

    assert calls["start"] == 0
    assert game.pending_direction == snake_module.Point(0, -1)
