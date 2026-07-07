"""Unit tests for SnakeCashRush game logic.

Tests cover snake movement, collision detection, score tracking,
boundary collisions, self-collision, cash spawning, and game state reset.
"""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# ── Mock browser APIs before importing main ──────────────────────────────────

mock_element = MagicMock()
mock_element.parentElement = MagicMock()
mock_element.classList = MagicMock()

mock_document = MagicMock()
mock_document.getElementById.return_value = mock_element
mock_document.addEventListener = MagicMock()

mock_bridge = SimpleNamespace(
    raf=MagicMock(return_value=1),
    cancelRaf=MagicMock(),
    readBestScore=MagicMock(return_value=0),
    writeBestScore=MagicMock(),
)

mock_window = MagicMock()
mock_window.snakeCashRushBridge = mock_bridge
mock_window.setTimeout = MagicMock()
mock_window.localStorage = MagicMock()

mock_pyodide_ffi = MagicMock()
mock_pyodide_ffi.create_proxy = lambda fn: fn

sys.modules["js"] = SimpleNamespace(document=mock_document, window=mock_window)
sys.modules["pyodide"] = MagicMock()
sys.modules["pyodide.ffi"] = mock_pyodide_ffi

sys.path.insert(0, str(__file__).replace("\\", "/").rsplit("/", 1)[0].replace("/tests", "/src"))

import main
from main import (
    BOARD_CELLS,
    SCORE_PER_BILL,
    Point,
    PowerUpType,
    SnakeCashRush,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def game() -> SnakeCashRush:
    """Create a fresh game instance for each test."""
    mock_bridge.readBestScore.return_value = 0
    return SnakeCashRush()


# ── Snake Movement Tests ─────────────────────────────────────────────────────


class TestSnakeMovement:
    """Tests for basic snake movement mechanics."""

    def test_snake_moves_in_current_direction(self, game: SnakeCashRush) -> None:
        """Snake head advances one cell in the pending direction."""
        game.running = True
        game.direction = Point(0, -1)
        game.pending_direction = Point(0, -1)
        head_before = game.snake[-1]

        game.advance()

        head_after = game.snake[-1]
        assert head_after.x == head_before.x
        assert head_after.y == head_before.y - 1

    def test_snake_moves_right(self, game: SnakeCashRush) -> None:
        """Snake moves right when direction is (1, 0)."""
        game.running = True
        game.pending_direction = Point(1, 0)
        head_before = game.snake[-1]

        game.advance()

        head_after = game.snake[-1]
        assert head_after.x == head_before.x + 1
        assert head_after.y == head_before.y

    def test_snake_moves_down(self, game: SnakeCashRush) -> None:
        """Snake moves down when direction is (0, 1)."""
        game.running = True
        # Set up snake moving right so switching to down is not a reversal
        game.snake = [Point(8, 10), Point(9, 10), Point(10, 10)]
        game.direction = Point(1, 0)
        game.pending_direction = Point(0, 1)
        game.cash = Point(0, 0)
        head_before = game.snake[-1]

        game.advance()

        head_after = game.snake[-1]
        assert head_after.y == head_before.y + 1

    def test_snake_tail_removed_on_normal_move(self, game: SnakeCashRush) -> None:
        """Snake length stays the same when no cash is collected."""
        game.running = True
        game.pending_direction = Point(1, 0)
        # Place cash far away
        game.cash = Point(0, 0)
        length_before = len(game.snake)

        game.advance()

        assert len(game.snake) == length_before

    def test_snake_grows_on_cash_collection(self, game: SnakeCashRush) -> None:
        """Snake grows by one segment when collecting cash."""
        game.running = True
        game.pending_direction = Point(0, -1)
        head = game.snake[-1]
        game.cash = Point(head.x, head.y - 1)
        length_before = len(game.snake)

        game.advance()

        assert len(game.snake) == length_before + 1

    def test_reverse_direction_blocked(self, game: SnakeCashRush) -> None:
        """Cannot reverse 180 degrees from current direction."""
        game.direction = Point(0, -1)
        assert game.is_reverse(Point(0, 1), Point(0, -1)) is True
        assert game.is_reverse(Point(1, 0), Point(0, -1)) is False
        assert game.is_reverse(Point(-1, 0), Point(1, 0)) is True


# ── Collision Detection Tests ────────────────────────────────────────────────


class TestCollisionDetection:
    """Tests for wall and body collision detection."""

    def test_hit_wall_top(self, game: SnakeCashRush) -> None:
        """Point above the board is a wall hit."""
        assert game.hit_wall(Point(5, -1)) is True

    def test_hit_wall_bottom(self, game: SnakeCashRush) -> None:
        """Point below the board is a wall hit."""
        assert game.hit_wall(Point(5, BOARD_CELLS)) is True

    def test_hit_wall_left(self, game: SnakeCashRush) -> None:
        """Point left of the board is a wall hit."""
        assert game.hit_wall(Point(-1, 5)) is True

    def test_hit_wall_right(self, game: SnakeCashRush) -> None:
        """Point right of the board is a wall hit."""
        assert game.hit_wall(Point(BOARD_CELLS, 5)) is True

    def test_no_wall_hit_inside_board(self, game: SnakeCashRush) -> None:
        """Points inside the board are not wall hits."""
        assert game.hit_wall(Point(0, 0)) is False
        assert game.hit_wall(Point(BOARD_CELLS - 1, BOARD_CELLS - 1)) is False
        assert game.hit_wall(Point(10, 10)) is False

    def test_wall_collision_ends_game(self, game: SnakeCashRush) -> None:
        """Moving into a wall ends the game."""
        game.running = True
        # Place snake at top edge, moving up
        game.snake = [Point(5, 2), Point(5, 1), Point(5, 0)]
        game.pending_direction = Point(0, -1)
        game.cash = Point(15, 15)

        game.advance()

        assert game.game_over is True
        assert game.running is False

    def test_self_collision_ends_game(self, game: SnakeCashRush) -> None:
        """Moving into own body ends the game."""
        game.running = True
        # Snake: tail=(4,6), body=(5,6), body=(5,7), head=(5,8)
        # Head moves up => next_head=(5,7) which is in snake[1:] => collision
        game.snake = [Point(4, 6), Point(5, 6), Point(5, 7), Point(5, 8)]
        game.direction = Point(0, -1)
        game.pending_direction = Point(0, -1)
        game.cash = Point(15, 15)

        game.advance()

        assert game.game_over is True

    def test_boundary_corner_collision(self, game: SnakeCashRush) -> None:
        """Moving into a corner is still a wall hit."""
        game.running = True
        game.snake = [Point(1, 0), Point(0, 0)]
        game.pending_direction = Point(-1, 0)  # Move left off board
        game.cash = Point(15, 15)

        game.advance()

        # Next head would be (-1, 0)
        assert game.game_over is True

    def test_invincibility_ignores_body_collision(self, game: SnakeCashRush) -> None:
        """Invincibility allows passing through own body."""
        game.running = True
        game.active_effect = PowerUpType.INVINCIBILITY
        game.effect_remaining_ms = 5000.0
        game.snake = [
            Point(5, 5),
            Point(6, 5),
            Point(6, 4),
            Point(5, 4),
        ]
        game.pending_direction = Point(0, 1)  # Would hit body at (5, 5)
        game.cash = Point(15, 15)

        game.advance()

        assert game.game_over is False
        assert game.running is True

    def test_invincibility_does_not_ignore_wall(self, game: SnakeCashRush) -> None:
        """Invincibility does NOT prevent wall deaths."""
        game.running = True
        game.active_effect = PowerUpType.INVINCIBILITY
        game.effect_remaining_ms = 5000.0
        game.snake = [Point(1, 0), Point(0, 0)]
        game.pending_direction = Point(0, -1)  # Move up off board
        game.cash = Point(15, 15)

        game.advance()

        assert game.game_over is True


# ── Score Tracking Tests ─────────────────────────────────────────────────────


class TestScoreTracking:
    """Tests for score calculation and best score persistence."""

    def test_score_increases_on_cash_collection(self, game: SnakeCashRush) -> None:
        """Score increases by SCORE_PER_BILL on cash collection."""
        game.running = True
        game.pending_direction = Point(0, -1)
        head = game.snake[-1]
        game.cash = Point(head.x, head.y - 1)

        game.advance()

        assert game.score == SCORE_PER_BILL

    def test_score_accumulates(self, game: SnakeCashRush) -> None:
        """Score accumulates over multiple collections."""
        game.running = True
        game.pending_direction = Point(0, -1)

        # First collection
        head = game.snake[-1]
        game.cash = Point(head.x, head.y - 1)
        game.advance()

        # Second collection
        head = game.snake[-1]
        game.cash = Point(head.x, head.y - 1)
        game.advance()

        assert game.score == SCORE_PER_BILL * 2

    def test_double_points_powerup(self, game: SnakeCashRush) -> None:
        """Double points power-up doubles the cash value."""
        game.running = True
        game.active_effect = PowerUpType.DOUBLE_POINTS
        game.effect_remaining_ms = 5000.0
        game.pending_direction = Point(0, -1)
        head = game.snake[-1]
        game.cash = Point(head.x, head.y - 1)

        game.advance()

        assert game.score == SCORE_PER_BILL * 2

    def test_normal_points_without_powerup(self, game: SnakeCashRush) -> None:
        """Without power-up, score increases by normal amount."""
        game.running = True
        game.active_effect = None
        game.pending_direction = Point(0, -1)
        head = game.snake[-1]
        game.cash = Point(head.x, head.y - 1)

        game.advance()

        assert game.score == SCORE_PER_BILL

    def test_best_score_updates_when_exceeded(self, game: SnakeCashRush) -> None:
        """Best score updates when current score surpasses it."""
        game.best_score = 0
        game.score = 15
        game.sync_best_score()

        assert game.best_score == 15

    def test_best_score_unchanged_when_not_exceeded(self, game: SnakeCashRush) -> None:
        """Best score stays the same when current score is lower."""
        game.best_score = 100
        game.score = 50
        game.sync_best_score()

        assert game.best_score == 100

    def test_speed_increases_with_score(self, game: SnakeCashRush) -> None:
        """Tick interval decreases (speed increases) as score grows."""
        game.running = True
        game.pending_direction = Point(0, -1)
        head = game.snake[-1]
        game.cash = Point(head.x, head.y - 1)
        tick_before = game.tick_ms

        game.advance()

        assert game.tick_ms <= tick_before


# ── Cash Spawning Tests ──────────────────────────────────────────────────────


class TestCashSpawning:
    """Tests for cash bill spawn position validity."""

    def test_cash_not_on_snake(self, game: SnakeCashRush) -> None:
        """Cash never spawns on a cell occupied by the snake."""
        for _ in range(50):
            cash = game.spawn_cash(game.snake)
            assert cash not in game.snake

    def test_cash_within_board(self, game: SnakeCashRush) -> None:
        """Cash always spawns within board boundaries."""
        for _ in range(50):
            cash = game.spawn_cash(game.snake)
            assert 0 <= cash.x < BOARD_CELLS
            assert 0 <= cash.y < BOARD_CELLS

    def test_cash_not_on_powerup(self, game: SnakeCashRush) -> None:
        """Cash does not spawn on the power-up position."""
        from main import PowerUp

        game.powerup = PowerUp(position=Point(5, 5), kind=PowerUpType.DOUBLE_POINTS)

        for _ in range(50):
            cash = game.spawn_cash(game.snake)
            assert cash != Point(5, 5)

    def test_cash_spawns_when_board_nearly_full(self, game: SnakeCashRush) -> None:
        """Cash spawns on the only available cell when board is nearly full."""
        # Fill almost all cells with snake body
        full_snake = [
            Point(x, y)
            for y in range(BOARD_CELLS)
            for x in range(BOARD_CELLS)
            if not (x == 0 and y == 0)
        ]
        game.powerup = None
        cash = game.spawn_cash(full_snake)
        assert cash == Point(0, 0)


# ── Game State Reset Tests ───────────────────────────────────────────────────


class TestGameStateReset:
    """Tests for game state reset behavior."""

    def test_reset_clears_score(self, game: SnakeCashRush) -> None:
        """Reset sets score to zero."""
        game.score = 150
        game.reset_state()
        assert game.score == 0

    def test_reset_clears_game_over(self, game: SnakeCashRush) -> None:
        """Reset clears the game_over flag."""
        game.game_over = True
        game.reset_state()
        assert game.game_over is False

    def test_reset_clears_running(self, game: SnakeCashRush) -> None:
        """Reset clears the running flag."""
        game.running = True
        game.reset_state()
        assert game.running is False

    def test_reset_restores_initial_snake_length(self, game: SnakeCashRush) -> None:
        """Reset restores the snake to 3 segments."""
        game.snake = [Point(i, 0) for i in range(10)]
        game.reset_state()
        assert len(game.snake) == 3

    def test_reset_places_snake_in_center(self, game: SnakeCashRush) -> None:
        """Reset places the snake head near the center of the board."""
        game.reset_state()
        head = game.snake[-1]
        center = BOARD_CELLS // 2
        assert head.x == center
        # Head should be near center vertically
        assert abs(head.y - center) <= 2

    def test_reset_restores_base_tick(self, game: SnakeCashRush) -> None:
        """Reset restores tick_ms to BASE_TICK_MS."""
        game.tick_ms = 50
        game.reset_state()
        assert game.tick_ms == main.BASE_TICK_MS

    def test_reset_clears_powerup_state(self, game: SnakeCashRush) -> None:
        """Reset clears all power-up related state."""
        from main import PowerUp

        game.powerup = PowerUp(position=Point(3, 3), kind=PowerUpType.DOUBLE_POINTS)
        game.active_effect = PowerUpType.INVINCIBILITY
        game.effect_remaining_ms = 3000.0

        game.reset_state()

        assert game.powerup is None
        assert game.active_effect is None
        assert game.effect_remaining_ms == 0.0

    def test_reset_sets_direction_up(self, game: SnakeCashRush) -> None:
        """Reset sets direction to up (0, -1)."""
        game.direction = Point(1, 0)
        game.reset_state()
        assert game.direction == Point(0, -1)

    def test_restart_game_starts_fresh_run(self, game: SnakeCashRush) -> None:
        """Restart resets state and starts a new running game."""
        game.score = 100
        game.game_over = True
        game.restart_game()
        assert game.score == 0
        assert game.running is True
        assert game.game_over is False


# ── Snapshot Tests ───────────────────────────────────────────────────────────


class TestSnapshotJson:
    """Tests for the debug snapshot serialization."""

    def test_snapshot_contains_required_fields(self, game: SnakeCashRush) -> None:
        """Snapshot JSON includes all expected top-level keys."""
        data = json.loads(game.snapshot_json())
        expected_keys = {
            "running", "gameOver", "score", "bestScore", "tickMs",
            "direction", "cash", "snake", "powerup", "activeEffect",
            "effectRemainingMs",
        }
        assert expected_keys.issubset(data.keys())

    def test_snapshot_powerup_null_when_none(self, game: SnakeCashRush) -> None:
        """Snapshot shows null when no power-up is on board."""
        game.powerup = None
        data = json.loads(game.snapshot_json())
        assert data["powerup"] is None

    def test_snapshot_active_effect_value(self, game: SnakeCashRush) -> None:
        """Snapshot includes the active effect string value."""
        game.active_effect = PowerUpType.DOUBLE_POINTS
        game.effect_remaining_ms = 4000.0
        data = json.loads(game.snapshot_json())
        assert data["activeEffect"] == "double_points"
        assert data["effectRemainingMs"] == 4000.0
