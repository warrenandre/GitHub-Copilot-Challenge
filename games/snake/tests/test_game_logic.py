import importlib.util
import pathlib
import sys
import types
import unittest


class FakeClassList:
    def __init__(self):
        self._items = set()

    def add(self, name):
        self._items.add(name)

    def remove(self, name):
        self._items.discard(name)


class FakeElement:
    def __init__(self):
        self.textContent = ""
        self.parentElement = None
        self.classList = FakeClassList()
        self._listeners = {}

    def addEventListener(self, name, callback):
        self._listeners[name] = callback

    def removeEventListener(self, name, callback):
        existing = self._listeners.get(name)
        if existing is callback:
            del self._listeners[name]


class FakeCanvasContext:
    def clearRect(self, *_args):
        return None

    def fillRect(self, *_args):
        return None

    def beginPath(self):
        return None

    def moveTo(self, *_args):
        return None

    def lineTo(self, *_args):
        return None

    def stroke(self):
        return None

    def save(self):
        return None

    def restore(self):
        return None

    def fill(self):
        return None

    def arc(self, *_args):
        return None

    def fillText(self, *_args):
        return None

    def quadraticCurveTo(self, *_args):
        return None

    def closePath(self):
        return None


class FakeCanvas(FakeElement):
    def __init__(self):
        super().__init__()
        self._context = FakeCanvasContext()

    def getContext(self, _kind):
        return self._context


class FakeBridge:
    def __init__(self):
        self.best_score = 0
        self.last_write = None
        self._raf_id = 0

    def raf(self, callback):
        self._raf_id += 1
        return self._raf_id

    def cancelRaf(self, _handle):
        return None

    def readBestScore(self):
        return self.best_score

    def writeBestScore(self, score):
        self.best_score = score
        self.last_write = score


class FakeWindow:
    def __init__(self):
        self.snakeCashRushBridge = FakeBridge()
        self._timers = []

    def setTimeout(self, callback, _delay):
        self._timers.append(callback)
        callback()
        return len(self._timers)


class FakeDocument:
    def __init__(self):
        self._listeners = {}
        self.elements = {
            "gameCanvas": FakeCanvas(),
            "scoreValue": FakeElement(),
            "bestScoreValue": FakeElement(),
            "statusText": FakeElement(),
            "startButton": FakeElement(),
            "gameOverlay": FakeElement(),
            "overlayKicker": FakeElement(),
            "overlayTitle": FakeElement(),
            "overlayMessage": FakeElement(),
            "overlayButton": FakeElement(),
            "cashBurst": FakeElement(),
        }
        self.elements["scoreValue"].parentElement = FakeElement()
        self.elements["bestScoreValue"].parentElement = FakeElement()

    def getElementById(self, element_id):
        return self.elements[element_id]

    def addEventListener(self, name, callback):
        self._listeners[name] = callback

    def removeEventListener(self, name, callback):
        existing = self._listeners.get(name)
        if existing is callback:
            del self._listeners[name]


class FakeEvent:
    def __init__(self, key):
        self.key = key


def load_main_module():
    module_name = "snake_main_under_test"
    module_path = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"

    for name in [module_name, "js", "pyodide", "pyodide.ffi"]:
        if name in sys.modules:
            del sys.modules[name]

    fake_document = FakeDocument()
    fake_window = FakeWindow()

    js_mod = types.ModuleType("js")
    js_mod.document = fake_document
    js_mod.window = fake_window

    pyodide_mod = types.ModuleType("pyodide")
    pyodide_ffi_mod = types.ModuleType("pyodide.ffi")
    pyodide_ffi_mod.create_proxy = lambda callback: callback

    sys.modules["js"] = js_mod
    sys.modules["pyodide"] = pyodide_mod
    sys.modules["pyodide.ffi"] = pyodide_ffi_mod

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module, fake_document, fake_window


class SnakeGameLogicTests(unittest.TestCase):
    def setUp(self):
        self.module, self.document, self.window = load_main_module()
        self.game = self.module.SnakeCashRush()

    def test_advance_moves_snake_without_growth(self):
        self.game.running = True
        original = list(self.game.snake)
        self.game.cash = self.module.Point(0, 0)

        self.game.advance()

        self.assertEqual(len(self.game.snake), len(original))
        self.assertEqual(self.game.snake[-1], self.module.Point(original[-1].x, original[-1].y - 1))
        self.assertEqual(self.game.score, 0)

    def test_collecting_cash_increases_score_and_grows_snake(self):
        self.game.running = True
        self.game.best_score = 0
        head = self.game.snake[-1]
        self.game.cash = self.module.Point(head.x, head.y - 1)

        previous_len = len(self.game.snake)
        self.game.advance()

        self.assertEqual(self.game.score, self.module.SCORE_PER_BILL)
        self.assertEqual(len(self.game.snake), previous_len + 1)
        self.assertEqual(
            self.game.tick_ms,
            max(self.module.MIN_TICK_MS, self.module.BASE_TICK_MS - self.module.SPEED_STEP_MS),
        )
        self.assertEqual(self.window.snakeCashRushBridge.last_write, self.module.SCORE_PER_BILL)

    def test_hit_wall_ends_game(self):
        self.game.running = True
        self.game.snake = [self.module.Point(0, 1), self.module.Point(0, 0)]
        self.game.direction = self.module.Point(0, -1)
        self.game.pending_direction = self.module.Point(0, -1)
        self.game.cash = self.module.Point(5, 5)

        self.game.advance()

        self.assertTrue(self.game.game_over)
        self.assertFalse(self.game.running)

    def test_self_collision_ends_game(self):
        self.game.running = True
        self.game.snake = [
            self.module.Point(1, 1),
            self.module.Point(2, 1),
            self.module.Point(2, 2),
            self.module.Point(1, 2),
            self.module.Point(1, 3),
            self.module.Point(2, 3),
        ]
        self.game.direction = self.module.Point(0, -1)
        self.game.pending_direction = self.module.Point(0, -1)
        self.game.cash = self.module.Point(0, 0)

        self.game.advance()

        self.assertTrue(self.game.game_over)
        self.assertFalse(self.game.running)

    def test_can_move_into_tail_when_not_collecting(self):
        self.game.running = True
        self.game.snake = [
            self.module.Point(5, 5),
            self.module.Point(6, 5),
            self.module.Point(6, 6),
            self.module.Point(5, 6),
        ]
        self.game.direction = self.module.Point(0, -1)
        self.game.pending_direction = self.module.Point(0, -1)
        self.game.cash = self.module.Point(0, 0)

        self.game.advance()

        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.snake[-1], self.module.Point(5, 5))

    def test_spawn_cash_avoids_occupied_cells(self):
        occupied = [self.module.Point(0, 0), self.module.Point(1, 0), self.module.Point(2, 0)]
        for _ in range(50):
            cash = self.game.spawn_cash(occupied)
            self.assertNotIn(cash, occupied)
            self.assertGreaterEqual(cash.x, 0)
            self.assertLess(cash.x, self.module.BOARD_CELLS)
            self.assertGreaterEqual(cash.y, 0)
            self.assertLess(cash.y, self.module.BOARD_CELLS)

    def test_spawn_cash_returns_origin_when_board_is_full(self):
        full = [
            self.module.Point(x, y)
            for y in range(self.module.BOARD_CELLS)
            for x in range(self.module.BOARD_CELLS)
        ]
        self.assertEqual(self.game.spawn_cash(full), self.module.Point(0, 0))

    def test_is_reverse_and_non_reverse(self):
        self.assertTrue(
            self.game.is_reverse(self.module.Point(0, 1), self.module.Point(0, -1))
        )
        self.assertFalse(
            self.game.is_reverse(self.module.Point(1, 0), self.module.Point(0, -1))
        )

    def test_invalid_key_does_not_change_direction(self):
        self.game.pending_direction = self.module.Point(0, -1)

        self.game.handle_keydown(FakeEvent("?"))

        self.assertEqual(self.game.pending_direction, self.module.Point(0, -1))

    def test_reverse_key_is_ignored(self):
        self.game.running = True
        self.game.direction = self.module.Point(0, -1)
        self.game.pending_direction = self.module.Point(0, -1)

        self.game.handle_keydown(FakeEvent("ArrowDown"))

        self.assertEqual(self.game.pending_direction, self.module.Point(0, -1))

    def test_valid_key_starts_game_and_sets_direction(self):
        self.assertFalse(self.game.running)

        self.game.handle_keydown(FakeEvent("ArrowRight"))

        self.assertTrue(self.game.running)
        self.assertEqual(self.game.pending_direction, self.module.Point(1, 0))

    def test_step_debug_noops_when_game_over(self):
        original = list(self.game.snake)
        self.game.game_over = True

        self.game.step_debug()

        self.assertEqual(self.game.snake, original)

    def test_restart_key_resets_score_and_state(self):
        self.game.running = True
        self.game.score = 40
        self.game.score_value.textContent = "40"

        self.game.handle_keydown(FakeEvent("r"))

        self.assertTrue(self.game.running)
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.score_value.textContent, "0")


if __name__ == "__main__":
    unittest.main()
