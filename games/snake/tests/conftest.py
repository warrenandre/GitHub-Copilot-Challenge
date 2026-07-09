"""pytest configuration: mock browser-only modules so main.py can be imported
in a pure-Python test environment without a browser or PyScript runtime.

Injection order matters — sys.modules must be patched BEFORE any import of
main.py so the module-level ``from js import ...`` and
``from pyodide.ffi import create_proxy`` resolve to our stubs.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

# ── 1. Add src/ to the Python path so ``import main`` resolves ───────────────

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ── 2. Minimal DOM / browser stub classes ────────────────────────────────────

class MockClassList:
    """Stand-in for a DOM element's classList — supports add/remove/in."""

    def __init__(self) -> None:
        self._classes: set[str] = set()

    def add(self, cls: str) -> None:
        self._classes.add(cls)

    def remove(self, cls: str) -> None:
        self._classes.discard(cls)

    def __contains__(self, cls: str) -> bool:
        return cls in self._classes


class MockElement:
    """Stand-in for a DOM HTMLElement with the subset of attributes used by main.py."""

    def __init__(self) -> None:
        self.textContent: str = ""
        self.classList: MockClassList = MockClassList()
        # parentElement is needed for score_tile / best_score_tile; create a
        # lightweight sibling to avoid infinite recursion.
        parent: MockElement = object.__new__(MockElement)
        object.__setattr__(parent, "textContent", "")
        object.__setattr__(parent, "classList", MockClassList())
        object.__setattr__(parent, "parentElement", None)
        self.parentElement: MockElement = parent

    def addEventListener(self, *args: object, **kwargs: object) -> None:
        pass

    def removeEventListener(self, *args: object, **kwargs: object) -> None:
        pass

    def getContext(self, ctx_type: str) -> MockContext:
        return MockContext()


class MockContext:
    """Stand-in for CanvasRenderingContext2D — all drawing calls are no-ops."""

    fillStyle: str = ""
    strokeStyle: str = ""
    lineWidth: float = 1.0
    shadowColor: str = ""
    shadowBlur: float = 0.0
    font: str = ""
    textAlign: str = ""
    textBaseline: str = ""

    def clearRect(self, *a: object) -> None: pass
    def fillRect(self, *a: object) -> None: pass
    def beginPath(self) -> None: pass
    def moveTo(self, *a: object) -> None: pass
    def lineTo(self, *a: object) -> None: pass
    def stroke(self) -> None: pass
    def fill(self) -> None: pass
    def arc(self, *a: object) -> None: pass
    def quadraticCurveTo(self, *a: object) -> None: pass
    def save(self) -> None: pass
    def restore(self) -> None: pass
    def closePath(self) -> None: pass
    def fillText(self, *a: object) -> None: pass


class MockBridge:
    """Stand-in for window.snakeCashRushBridge defined in app.js."""

    def __init__(self) -> None:
        self._best_score: int = 0

    def raf(self, callback: object) -> int:
        return 42  # fake requestAnimationFrame handle

    def cancelRaf(self, handle: object) -> None:
        pass

    def readBestScore(self) -> int:
        return self._best_score

    def writeBestScore(self, score: object) -> None:
        self._best_score = int(score)  # type: ignore[arg-type]


class MockWindow:
    """Stand-in for the browser window global."""

    def __init__(self) -> None:
        self.snakeCashRushBridge: MockBridge = MockBridge()

    def setTimeout(self, callback: object, delay: object) -> None:
        pass  # timer callbacks are not needed for pure-logic tests


class MockDocument:
    """Stand-in for the browser document global."""

    def getElementById(self, element_id: str) -> MockElement:
        return MockElement()

    def addEventListener(self, *args: object, **kwargs: object) -> None:
        pass

    def removeEventListener(self, *args: object, **kwargs: object) -> None:
        pass


# ── 3. Inject stubs into sys.modules before main.py is imported ──────────────

_js_module = types.ModuleType("js")
_js_module.document = MockDocument()  # type: ignore[attr-defined]
_js_module.window = MockWindow()       # type: ignore[attr-defined]
sys.modules["js"] = _js_module

_pyodide_module = types.ModuleType("pyodide")
_pyodide_ffi_module = types.ModuleType("pyodide.ffi")
# create_proxy(fn) just returns fn — no GC concerns in the test environment.
_pyodide_ffi_module.create_proxy = lambda fn: fn  # type: ignore[attr-defined]
_pyodide_module.ffi = _pyodide_ffi_module          # type: ignore[attr-defined]
sys.modules["pyodide"] = _pyodide_module
sys.modules["pyodide.ffi"] = _pyodide_ffi_module


# ── 4. Shared pytest fixtures ─────────────────────────────────────────────────

import pytest  # noqa: E402 — must come after sys.modules injection


@pytest.fixture()
def game():
    """Return a freshly initialised SnakeCashRush instance in the idle state."""
    from main import SnakeCashRush  # import here so mocks are already active
    return SnakeCashRush()


@pytest.fixture()
def running_game(game):
    """Return a SnakeCashRush instance with running=True, ready for advance()."""
    game.running = True
    return game
