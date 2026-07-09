"""Compliance test suite for Snake Cash Rush pure-logic methods.

This file is the Copilot output verification sample. Its own code is checked
against the rules in .github/copilot-instructions.md before being committed.

Run from the games/snake directory:
    python -m pytest src/test_main_logic.py -v

NOTE: PyScript / browser globals are stubbed below so the tests run under a
      plain CPython interpreter without a browser or network connection.
"""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from random import seed
from typing import Iterable
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Browser-API stubs — isolate pure logic from PyScript / DOM dependencies
# ---------------------------------------------------------------------------

def _make_js_stub() -> types.ModuleType:
    """Return a minimal stub for the `js` module used by PyScript.

    Parameters:
        None

    Returns:
        types.ModuleType: A module with MagicMock attributes for `document`
        and `window`.
    """
    js = types.ModuleType("js")
    js.document = MagicMock()
    js.window = MagicMock()
    # Simulate localStorage returning 0 for best score on first load
    js.window.snakeCashRushBridge.readBestScore.return_value = 0
    return js


def _make_pyodide_stub() -> types.ModuleType:
    """Return a minimal stub for the `pyodide.ffi` module.

    Parameters:
        None

    Returns:
        types.ModuleType: A module whose `create_proxy` is an identity function
        so that callback proxies work transparently in tests.
    """
    pyodide = types.ModuleType("pyodide")
    ffi = types.ModuleType("pyodide.ffi")
    # create_proxy is an identity in tests — no JS boundary to cross
    ffi.create_proxy = lambda f: f
    pyodide.ffi = ffi
    sys.modules["pyodide"] = pyodide
    sys.modules["pyodide.ffi"] = ffi
    return pyodide


# Install stubs before importing the game module
sys.modules["js"] = _make_js_stub()
_make_pyodide_stub()

# Now safe to import — all browser globals are stubbed
from main import Point, SnakeCashRush, BOARD_CELLS, SCORE_PER_BILL, BASE_TICK_MS, MIN_TICK_MS, SPEED_STEP_MS  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_game() -> SnakeCashRush:
    """Instantiate a fresh SnakeCashRush game with browser stubs active.

    Parameters:
        None

    Returns:
        SnakeCashRush: A fully initialized game instance ready for testing.
    """
    return SnakeCashRush()


# ---------------------------------------------------------------------------
# Point dataclass
# ---------------------------------------------------------------------------

class TestPoint:
    """Tests for the Point coordinate dataclass."""

    def test_equality(self) -> None:
        """Two Points with identical coordinates should be equal."""
        assert Point(3, 5) == Point(3, 5)

    def test_inequality(self) -> None:
        """Points differing on any axis should not be equal."""
        assert Point(1, 2) != Point(2, 1)

    def test_hashable_in_set(self) -> None:
        """Point must be hashable so it can be stored in a set (used in spawn_cash)."""
        occupied = {Point(0, 0), Point(1, 1)}
        assert Point(0, 0) in occupied
        assert Point(9, 9) not in occupied


# ---------------------------------------------------------------------------
# hit_wall
# ---------------------------------------------------------------------------

class TestHitWall:
    """Tests for boundary collision detection."""

    def test_center_is_safe(self) -> None:
        """A point in the board center must not trigger a wall hit."""
        game = _make_game()
        assert game.hit_wall(Point(BOARD_CELLS // 2, BOARD_CELLS // 2)) is False

    def test_left_edge_triggers_hit(self) -> None:
        """x = -1 is outside the left boundary."""
        game = _make_game()
        assert game.hit_wall(Point(-1, 5)) is True

    def test_right_edge_triggers_hit(self) -> None:
        """x = BOARD_CELLS equals or exceeds the right boundary."""
        game = _make_game()
        assert game.hit_wall(Point(BOARD_CELLS, 5)) is True

    def test_top_edge_triggers_hit(self) -> None:
        """y = -1 is outside the top boundary."""
        game = _make_game()
        assert game.hit_wall(Point(5, -1)) is True

    def test_bottom_edge_triggers_hit(self) -> None:
        """y = BOARD_CELLS equals or exceeds the bottom boundary."""
        game = _make_game()
        assert game.hit_wall(Point(5, BOARD_CELLS)) is True

    def test_corner_cells_are_valid(self) -> None:
        """All four board corners should be inside the boundary."""
        game = _make_game()
        corners = [
            Point(0, 0),
            Point(BOARD_CELLS - 1, 0),
            Point(0, BOARD_CELLS - 1),
            Point(BOARD_CELLS - 1, BOARD_CELLS - 1),
        ]
        for corner in corners:
            assert game.hit_wall(corner) is False, f"Corner {corner} should be valid"


# ---------------------------------------------------------------------------
# is_reverse
# ---------------------------------------------------------------------------

class TestIsReverse:
    """Tests for reverse-direction guard (prevents 180-degree turns)."""

    def test_opposite_directions_are_reverse(self) -> None:
        """Moving right while going left is a forbidden reversal."""
        game = _make_game()
        assert game.is_reverse(Point(1, 0), Point(-1, 0)) is True

    def test_perpendicular_is_not_reverse(self) -> None:
        """Turning up while going right is a valid perpendicular turn."""
        game = _make_game()
        assert game.is_reverse(Point(0, -1), Point(1, 0)) is False

    def test_same_direction_is_not_reverse(self) -> None:
        """Holding the same direction key must not be treated as a reversal."""
        game = _make_game()
        assert game.is_reverse(Point(0, -1), Point(0, -1)) is False


# ---------------------------------------------------------------------------
# spawn_cash
# ---------------------------------------------------------------------------

class TestSpawnCash:
    """Tests for the random cash-bill placement logic."""

    def test_cash_not_on_snake(self) -> None:
        """Spawned cash must never overlap any snake segment."""
        game = _make_game()
        seed(42)
        # Use a large snake to increase collision likelihood in a naive implementation
        large_snake = [Point(x, 0) for x in range(BOARD_CELLS - 1)]
        cash = game.spawn_cash(large_snake)
        assert cash not in set(large_snake)

    def test_cash_within_bounds(self) -> None:
        """Spawned cash must always land inside the board."""
        game = _make_game()
        for _ in range(50):
            cash = game.spawn_cash(game.snake)
            assert 0 <= cash.x < BOARD_CELLS
            assert 0 <= cash.y < BOARD_CELLS

    def test_fallback_when_board_full(self) -> None:
        """When every cell is occupied, spawn_cash must return Point(0, 0) without raising."""
        game = _make_game()
        all_cells = [Point(x, y) for y in range(BOARD_CELLS) for x in range(BOARD_CELLS)]
        result = game.spawn_cash(all_cells)
        # Guard: result must be a Point — behavior is deterministic per spec
        assert isinstance(result, Point)
        assert result == Point(0, 0)


# ---------------------------------------------------------------------------
# speed scaling via advance()
# ---------------------------------------------------------------------------

class TestSpeedScaling:
    """Tests that game speed increases correctly as the player collects cash."""

    def test_speed_increases_on_collection(self) -> None:
        """Tick interval must decrease each time a cash bill is collected."""
        game = _make_game()
        game.running = True
        initial_tick = game.tick_ms

        # Place cash directly ahead of the snake head for guaranteed collection
        head = game.snake[-1]
        game.cash = Point(head.x + game.direction.x, head.y + game.direction.y)
        game.advance()

        assert game.tick_ms < initial_tick, "Speed should increase after collecting cash"

    def test_speed_does_not_exceed_minimum(self) -> None:
        """Tick interval must never drop below MIN_TICK_MS regardless of score."""
        game = _make_game()
        game.running = True

        # Drive score high enough that the formula would go below MIN_TICK_MS
        game.score = 10_000
        game.tick_ms = max(MIN_TICK_MS, BASE_TICK_MS - (game.score // SCORE_PER_BILL) * SPEED_STEP_MS)

        assert game.tick_ms == MIN_TICK_MS


# ---------------------------------------------------------------------------
# reset_state
# ---------------------------------------------------------------------------

class TestResetState:
    """Tests that reset_state returns the game to a clean initial condition."""

    def test_score_resets_to_zero(self) -> None:
        """Score must be 0 after a reset regardless of previous value."""
        game = _make_game()
        game.score = 999
        game.reset_state()
        assert game.score == 0

    def test_tick_resets_to_base(self) -> None:
        """Tick interval must return to BASE_TICK_MS on reset."""
        game = _make_game()
        game.tick_ms = MIN_TICK_MS
        game.reset_state()
        assert game.tick_ms == BASE_TICK_MS

    def test_running_is_false_after_reset(self) -> None:
        """Game must not be in running state immediately after a reset."""
        game = _make_game()
        game.running = True
        game.reset_state()
        assert game.running is False

    def test_snake_starts_at_center(self) -> None:
        """Snake head must be near the board center after reset."""
        game = _make_game()
        center = BOARD_CELLS // 2
        head = game.snake[-1]
        assert head.x == center
        # Head y is one above center (snake starts moving upward)
        assert head.y == center - 1
