"""Unit tests for SnakeCashRush gameplay logic."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _FakeClassList:
    def add(self, _name: str) -> None:
        return None

    def remove(self, _name: str) -> None:
        return None


class _FakeContext:
    def __getattr__(self, _name: str):
        def _noop(*_args, **_kwargs):
            return None

        return _noop


class _FakeElement:
    def __init__(self) -> None:
        self.textContent = ""
        self.parentElement = self
        self.classList = _FakeClassList()

    def getContext(self, _ctx_type: str) -> _FakeContext:
        return _FakeContext()

    def addEventListener(self, _event: str, _handler) -> None:
        return None


class _FakeDocument:
    def __init__(self) -> None:
        self._elements = {}
        for element_id in (
            "gameCanvas",
            "scoreValue",
            "bestScoreValue",
            "powerUpValue",
            "statusText",
            "startButton",
            "gameOverlay",
            "overlayKicker",
            "overlayTitle",
            "overlayMessage",
            "overlayButton",
            "cashBurst",
        ):
            self._elements[element_id] = _FakeElement()

    def getElementById(self, element_id: str) -> _FakeElement:
        return self._elements.setdefault(element_id, _FakeElement())

    def addEventListener(self, _event: str, _handler) -> None:
        return None

    def removeEventListener(self, _event: str, _handler) -> None:
        return None


class _FakeBridge:
    def __init__(self) -> None:
        self._best_score = 0

    def readBestScore(self) -> int:
        return self._best_score

    def writeBestScore(self, value: int) -> None:
        self._best_score = value

    def raf(self, _callback):
        return 1

    def cancelRaf(self, _handle) -> None:
        return None


class _FakeWindow:
    def __init__(self) -> None:
        self.snakeCashRushBridge = _FakeBridge()

    def setTimeout(self, callback, _delay: int) -> None:
        callback()


def _load_main_module():
    js_module = types.ModuleType("js")
    js_module.document = _FakeDocument()
    js_module.window = _FakeWindow()

    pyodide_module = types.ModuleType("pyodide")
    pyodide_ffi_module = types.ModuleType("pyodide.ffi")

    def _create_proxy(func):
        return func

    pyodide_ffi_module.create_proxy = _create_proxy
    pyodide_module.ffi = pyodide_ffi_module

    sys.modules["js"] = js_module
    sys.modules["pyodide"] = pyodide_module
    sys.modules["pyodide.ffi"] = pyodide_ffi_module

    module_name = "snake_main_under_test"
    module_path = Path(__file__).resolve().parents[1] / "src" / "main.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load main.py module for testing.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class SnakeCashRushTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main = _load_main_module()

    def setUp(self) -> None:
        self.game = self.main.SnakeCashRush()

    def test_snake_moves_one_cell_without_scoring(self) -> None:
        initial_length = len(self.game.snake)
        self.game.snake = [
            self.main.Point(5, 5),
            self.main.Point(6, 5),
            self.main.Point(7, 5),
        ]
        self.game.direction = self.main.Point(1, 0)
        self.game.pending_direction = self.main.Point(1, 0)
        self.game.cash = self.main.Point(0, 0)

        self.game.advance(1000.0)

        self.assertEqual(self.game.snake[-1], self.main.Point(8, 5))
        self.assertEqual(len(self.game.snake), initial_length)
        self.assertFalse(self.game.game_over)

    def test_wall_collision_triggers_game_over(self) -> None:
        self.game.snake = [
            self.main.Point(1, 0),
            self.main.Point(0, 0),
        ]
        self.game.direction = self.main.Point(-1, 0)
        self.game.pending_direction = self.main.Point(-1, 0)
        self.game.cash = self.main.Point(10, 10)

        self.game.advance(1000.0)

        self.assertTrue(self.game.game_over)
        self.assertFalse(self.game.running)

    def test_self_collision_triggers_game_over(self) -> None:
        self.game.snake = [
            self.main.Point(2, 2),
            self.main.Point(3, 2),
            self.main.Point(3, 3),
            self.main.Point(2, 3),
        ]
        self.game.direction = self.main.Point(1, 0)
        self.game.pending_direction = self.main.Point(1, 0)
        self.game.cash = self.main.Point(0, 0)

        self.game.advance(1000.0)

        self.assertTrue(self.game.game_over)

    def test_score_increases_when_cash_collected(self) -> None:
        self.game.snake = [
            self.main.Point(5, 5),
            self.main.Point(6, 5),
            self.main.Point(7, 5),
        ]
        self.game.direction = self.main.Point(1, 0)
        self.game.pending_direction = self.main.Point(1, 0)
        self.game.cash = self.main.Point(8, 5)
        self.game.spawn_cash = lambda _snake: self.main.Point(0, 0)

        self.game.advance(1000.0)

        self.assertEqual(self.game.score, self.main.SCORE_PER_BILL)
        self.assertEqual(self.game.score_value.textContent, str(self.main.SCORE_PER_BILL))

    def test_double_points_multiplier_affects_score(self) -> None:
        self.game.snake = [
            self.main.Point(5, 5),
            self.main.Point(6, 5),
            self.main.Point(7, 5),
        ]
        self.game.direction = self.main.Point(1, 0)
        self.game.pending_direction = self.main.Point(1, 0)
        self.game.cash = self.main.Point(8, 5)
        self.game.spawn_cash = lambda _snake: self.main.Point(0, 0)
        self.game.active_effects["double_points"] = 1500.0

        self.game.advance(1000.0)

        self.assertEqual(self.game.score, self.main.SCORE_PER_BILL * 2)


if __name__ == "__main__":
    unittest.main()
