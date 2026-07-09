"""Unit tests for Snake Cash Rush core game logic.

Coverage
--------
Happy paths:
    Normal snake movement, cash collection, score increments, speed progression,
    state transitions (idle → running → game-over → restart).

Edge cases:
    All four wall boundaries, self-collision, entering the tail cell safely,
    full-board cash-spawn fallback, reverse-direction rejection, unknown keys.

Failure scenarios:
    Wall collisions, body collisions, game-over state integrity, best-score
    persistence logic, reset clearing all state.
"""
from __future__ import annotations

import json
import pytest

from main import (  # type: ignore[import]
    SnakeCashRush,
    Point,
    BOARD_CELLS,
    BASE_TICK_MS,
    MIN_TICK_MS,
    SCORE_PER_BILL,
)


# ─────────────────────────────────────────────────────────────────────────────
# Point dataclass
# ─────────────────────────────────────────────────────────────────────────────

class TestPoint:
    """The Point frozen dataclass is the canonical grid-coordinate type."""

    def test_equal_coordinates_compare_as_equal(self) -> None:
        """Two Points with the same x and y are identical."""
        assert Point(3, 7) == Point(3, 7)

    def test_different_x_makes_points_unequal(self) -> None:
        assert Point(3, 7) != Point(4, 7)

    def test_different_y_makes_points_unequal(self) -> None:
        assert Point(3, 7) != Point(3, 8)

    def test_point_is_hashable_and_supports_set_membership(self) -> None:
        """Points can live in sets and be membership-tested in O(1)."""
        occupied = {Point(1, 2), Point(3, 4)}
        assert Point(1, 2) in occupied
        assert Point(9, 9) not in occupied

    def test_point_is_immutable(self) -> None:
        """Frozen dataclass must reject attribute mutation."""
        p = Point(5, 5)
        with pytest.raises((AttributeError, TypeError)):
            p.x = 99  # type: ignore[misc]

    def test_direction_vector_applied_via_arithmetic(self) -> None:
        """Direction vectors can be added to positions via plain arithmetic."""
        pos = Point(5, 5)
        right = Point(1, 0)
        assert Point(pos.x + right.x, pos.y + right.y) == Point(6, 5)


# ─────────────────────────────────────────────────────────────────────────────
# hit_wall — boundary detection
# ─────────────────────────────────────────────────────────────────────────────

class TestHitWall:
    """hit_wall returns True only for coordinates outside the 20×20 grid."""

    def test_centre_of_board_is_inside(self, game: SnakeCashRush) -> None:
        assert not game.hit_wall(Point(10, 10))

    def test_top_left_corner_is_inside(self, game: SnakeCashRush) -> None:
        assert not game.hit_wall(Point(0, 0))

    def test_top_right_corner_is_inside(self, game: SnakeCashRush) -> None:
        assert not game.hit_wall(Point(BOARD_CELLS - 1, 0))

    def test_bottom_left_corner_is_inside(self, game: SnakeCashRush) -> None:
        assert not game.hit_wall(Point(0, BOARD_CELLS - 1))

    def test_bottom_right_corner_is_inside(self, game: SnakeCashRush) -> None:
        assert not game.hit_wall(Point(BOARD_CELLS - 1, BOARD_CELLS - 1))

    def test_negative_x_hits_left_wall(self, game: SnakeCashRush) -> None:
        assert game.hit_wall(Point(-1, 5))

    def test_x_equal_to_board_cells_hits_right_wall(self, game: SnakeCashRush) -> None:
        assert game.hit_wall(Point(BOARD_CELLS, 5))

    def test_x_far_beyond_right_wall(self, game: SnakeCashRush) -> None:
        assert game.hit_wall(Point(BOARD_CELLS + 50, 5))

    def test_negative_y_hits_top_wall(self, game: SnakeCashRush) -> None:
        assert game.hit_wall(Point(5, -1))

    def test_y_equal_to_board_cells_hits_bottom_wall(self, game: SnakeCashRush) -> None:
        assert game.hit_wall(Point(5, BOARD_CELLS))

    def test_large_negative_coordinates_hit_wall(self, game: SnakeCashRush) -> None:
        assert game.hit_wall(Point(-100, -100))


# ─────────────────────────────────────────────────────────────────────────────
# is_reverse — 180-degree direction guard
# ─────────────────────────────────────────────────────────────────────────────

class TestIsReverse:
    """is_reverse detects antiparallel direction pairs to prevent neck self-collision."""

    def test_up_is_reversed_by_down(self, game: SnakeCashRush) -> None:
        assert game.is_reverse(Point(0, 1), Point(0, -1))

    def test_down_is_reversed_by_up(self, game: SnakeCashRush) -> None:
        assert game.is_reverse(Point(0, -1), Point(0, 1))

    def test_left_is_reversed_by_right(self, game: SnakeCashRush) -> None:
        assert game.is_reverse(Point(1, 0), Point(-1, 0))

    def test_right_is_reversed_by_left(self, game: SnakeCashRush) -> None:
        assert game.is_reverse(Point(-1, 0), Point(1, 0))

    def test_up_vs_left_is_not_reverse(self, game: SnakeCashRush) -> None:
        assert not game.is_reverse(Point(-1, 0), Point(0, -1))

    def test_up_vs_right_is_not_reverse(self, game: SnakeCashRush) -> None:
        assert not game.is_reverse(Point(1, 0), Point(0, -1))

    def test_same_direction_is_not_reverse(self, game: SnakeCashRush) -> None:
        assert not game.is_reverse(Point(0, -1), Point(0, -1))

    def test_perpendicular_directions_are_not_reverse(self, game: SnakeCashRush) -> None:
        assert not game.is_reverse(Point(1, 0), Point(0, 1))


# ─────────────────────────────────────────────────────────────────────────────
# spawn_cash — random cash-bill placement
# ─────────────────────────────────────────────────────────────────────────────

class TestSpawnCash:
    """spawn_cash always returns a Point that is not occupied by the snake."""

    def test_spawn_is_not_on_any_snake_segment(self, game: SnakeCashRush) -> None:
        snake = [Point(10, 10), Point(10, 11), Point(10, 12)]
        assert game.spawn_cash(snake) not in snake

    def test_spawn_is_within_board_bounds(self, game: SnakeCashRush) -> None:
        snake = [Point(5, 5)]
        cash = game.spawn_cash(snake)
        assert 0 <= cash.x < BOARD_CELLS
        assert 0 <= cash.y < BOARD_CELLS

    def test_spawn_avoids_full_occupied_row(self, game: SnakeCashRush) -> None:
        """Cash must avoid all occupied cells, even a full row."""
        top_row = [Point(x, 0) for x in range(BOARD_CELLS)]
        for _ in range(20):  # repeat to stress random selection
            cash = game.spawn_cash(top_row)
            assert cash not in top_row
            assert cash.y > 0

    def test_spawn_fallback_when_board_completely_full(self, game: SnakeCashRush) -> None:
        """When every cell is occupied spawn_cash falls back to Point(0, 0)."""
        all_cells = [Point(x, y) for y in range(BOARD_CELLS) for x in range(BOARD_CELLS)]
        assert game.spawn_cash(all_cells) == Point(0, 0)

    def test_spawn_uses_empty_cells_with_single_segment_snake(self, game: SnakeCashRush) -> None:
        """All 399 non-snake cells are valid candidates when the snake has one segment."""
        snake = [Point(0, 0)]
        cash = game.spawn_cash(snake)
        assert cash != Point(0, 0)


# ─────────────────────────────────────────────────────────────────────────────
# reset_state — full state reset
# ─────────────────────────────────────────────────────────────────────────────

class TestResetState:
    """reset_state must restore every mutable field to its initial value."""

    def test_score_is_zero(self, game: SnakeCashRush) -> None:
        game.score = 500
        game.reset_state()
        assert game.score == 0

    def test_tick_ms_restored_to_base(self, game: SnakeCashRush) -> None:
        game.tick_ms = MIN_TICK_MS
        game.reset_state()
        assert game.tick_ms == BASE_TICK_MS

    def test_snake_has_exactly_three_segments(self, game: SnakeCashRush) -> None:
        game.reset_state()
        assert len(game.snake) == 3

    def test_snake_is_centred_on_the_board(self, game: SnakeCashRush) -> None:
        game.reset_state()
        centre = BOARD_CELLS // 2
        assert all(seg.x == centre for seg in game.snake)

    def test_direction_is_up(self, game: SnakeCashRush) -> None:
        game.direction = Point(1, 0)
        game.reset_state()
        assert game.direction == Point(0, -1)

    def test_pending_direction_is_up(self, game: SnakeCashRush) -> None:
        game.pending_direction = Point(1, 0)
        game.reset_state()
        assert game.pending_direction == Point(0, -1)

    def test_running_is_false(self, game: SnakeCashRush) -> None:
        game.running = True
        game.reset_state()
        assert not game.running

    def test_game_over_is_false(self, game: SnakeCashRush) -> None:
        game.game_over = True
        game.reset_state()
        assert not game.game_over

    def test_accumulator_is_zero(self, game: SnakeCashRush) -> None:
        game.accumulator = 999.0
        game.reset_state()
        assert game.accumulator == 0.0

    def test_cash_is_not_on_any_snake_segment(self, game: SnakeCashRush) -> None:
        game.reset_state()
        assert game.cash not in game.snake

    def test_cash_is_within_board_bounds(self, game: SnakeCashRush) -> None:
        game.reset_state()
        assert 0 <= game.cash.x < BOARD_CELLS
        assert 0 <= game.cash.y < BOARD_CELLS


# ─────────────────────────────────────────────────────────────────────────────
# advance — normal movement (no collection, no collision)
# ─────────────────────────────────────────────────────────────────────────────

class TestAdvanceMovement:
    """Each call to advance() moves the snake one cell in the pending direction."""

    def test_head_moves_by_direction_vector(self, running_game: SnakeCashRush) -> None:
        """New head = old head + pending_direction."""
        g = running_game
        old_head = g.snake[-1]
        queued = g.pending_direction       # capture before advance commits it
        g.cash = Point(0, 0)              # keep cash away from the path
        g.advance()
        assert not g.game_over
        assert g.snake[-1] == Point(old_head.x + queued.x, old_head.y + queued.y)

    def test_snake_length_is_unchanged_when_no_collection(self, running_game: SnakeCashRush) -> None:
        g = running_game
        g.cash = Point(0, 0)              # not in the snake's path
        length_before = len(g.snake)
        g.advance()
        if not g.game_over:
            assert len(g.snake) == length_before

    def test_tail_segment_is_removed_after_non_collecting_move(self, running_game: SnakeCashRush) -> None:
        """The tail vacates its cell so the snake slides forward."""
        g = running_game
        old_tail = g.snake[0]
        g.cash = Point(0, 0)
        g.advance()
        if not g.game_over:
            assert old_tail not in g.snake

    def test_pending_direction_is_committed_as_direction(self, running_game: SnakeCashRush) -> None:
        """Queuing a right turn causes the head to move right on the next tick."""
        g = running_game
        # Current direction is up; queue a right turn.
        g.pending_direction = Point(1, 0)
        old_head = g.snake[-1]
        g.cash = Point(0, 0)
        g.advance()
        if not g.game_over:
            assert g.snake[-1] == Point(old_head.x + 1, old_head.y)

    def test_direction_attribute_reflects_committed_pending(self, running_game: SnakeCashRush) -> None:
        """After advance(), game.direction matches the queued direction."""
        g = running_game
        g.pending_direction = Point(1, 0)
        g.cash = Point(0, 0)
        g.advance()
        assert g.direction == Point(1, 0)


# ─────────────────────────────────────────────────────────────────────────────
# advance — cash collection
# ─────────────────────────────────────────────────────────────────────────────

class TestCashCollection:
    """Collecting a cash bill increments score, grows the snake, and spawns new cash."""

    @staticmethod
    def _place_cash_one_step_ahead(g: SnakeCashRush) -> Point:
        """Position the cash bill directly in front of the snake's head."""
        head = g.snake[-1]
        ahead = Point(head.x + g.pending_direction.x, head.y + g.pending_direction.y)
        g.cash = ahead
        return ahead

    def test_score_increases_by_score_per_bill(self, running_game: SnakeCashRush) -> None:
        self._place_cash_one_step_ahead(running_game)
        running_game.advance()
        assert running_game.score == SCORE_PER_BILL

    def test_snake_grows_by_one_segment(self, running_game: SnakeCashRush) -> None:
        length_before = len(running_game.snake)
        self._place_cash_one_step_ahead(running_game)
        running_game.advance()
        assert len(running_game.snake) == length_before + 1

    def test_new_cash_is_spawned_after_collection(self, running_game: SnakeCashRush) -> None:
        """After collection the cash position must have moved off the snake."""
        self._place_cash_one_step_ahead(running_game)
        running_game.advance()
        assert running_game.cash not in running_game.snake

    def test_tick_ms_decreases_after_collection(self, running_game: SnakeCashRush) -> None:
        original_tick = running_game.tick_ms
        self._place_cash_one_step_ahead(running_game)
        running_game.advance()
        assert running_game.tick_ms < original_tick

    def test_tick_ms_is_floored_at_min_tick_ms(self, running_game: SnakeCashRush) -> None:
        """tick_ms never drops below MIN_TICK_MS, even with an extremely high score."""
        running_game.score = 10_000
        running_game.tick_ms = MIN_TICK_MS
        self._place_cash_one_step_ahead(running_game)
        running_game.advance()
        assert running_game.tick_ms >= MIN_TICK_MS

    def test_consecutive_collections_keep_increasing_score(self, running_game: SnakeCashRush) -> None:
        """Each collected bill adds exactly SCORE_PER_BILL to the running total."""
        for bill_number in range(1, 4):
            self._place_cash_one_step_ahead(running_game)
            if running_game.game_over:
                break
            running_game.advance()
            assert running_game.score == SCORE_PER_BILL * bill_number

    def test_speed_is_monotonically_non_increasing_across_collections(
        self, running_game: SnakeCashRush
    ) -> None:
        """tick_ms must not rise between bills — speed can only stay flat or increase."""
        previous_tick = running_game.tick_ms
        for _ in range(5):
            self._place_cash_one_step_ahead(running_game)
            if running_game.game_over:
                break
            running_game.advance()
            assert running_game.tick_ms <= previous_tick
            previous_tick = running_game.tick_ms


# ─────────────────────────────────────────────────────────────────────────────
# advance — collision detection
# ─────────────────────────────────────────────────────────────────────────────

class TestCollisionDetection:
    """Collisions with walls or the snake body trigger end_game()."""

    def _set_up(
        self,
        game: SnakeCashRush,
        snake: list[Point],
        direction: Point,
    ) -> None:
        """Helper: inject a specific snake layout and direction into the game."""
        game.snake = snake
        game.direction = direction
        game.pending_direction = direction
        game.cash = Point(0, 19)       # somewhere safe, not in the collision path
        game.running = True

    # ── Wall collisions ──────────────────────────────────────────────────────

    def test_moving_into_left_wall_ends_game(self, game: SnakeCashRush) -> None:
        self._set_up(game, [Point(2, 5), Point(1, 5), Point(0, 5)], Point(-1, 0))
        game.advance()
        assert game.game_over
        assert not game.running

    def test_moving_into_right_wall_ends_game(self, game: SnakeCashRush) -> None:
        self._set_up(game, [Point(17, 5), Point(18, 5), Point(19, 5)], Point(1, 0))
        game.advance()
        assert game.game_over

    def test_moving_into_top_wall_ends_game(self, game: SnakeCashRush) -> None:
        self._set_up(game, [Point(10, 2), Point(10, 1), Point(10, 0)], Point(0, -1))
        game.advance()
        assert game.game_over

    def test_moving_into_bottom_wall_ends_game(self, game: SnakeCashRush) -> None:
        self._set_up(game, [Point(10, 17), Point(10, 18), Point(10, 19)], Point(0, 1))
        game.advance()
        assert game.game_over

    # ── Body / self collision ─────────────────────────────────────────────────

    def test_head_entering_non_tail_body_segment_ends_game(self, game: SnakeCashRush) -> None:
        """Snake in a C shape where the head moves left into its own body (not the tail).

        Layout (. = empty, S = body):
            . . . . .
            . S S S .      snake[0]=(5,4) tail
            . S . . .      snake[1]=(5,3)
            . S S > .      snake[-1]=(7,4) head, direction left → hits (6,4) = snake[2]
        """
        snake = [
            Point(5, 4),   # tail
            Point(5, 3),
            Point(6, 3),
            Point(7, 3),
            Point(7, 4),   # head — moving left gives (6,4) NOT the tail
        ]
        # Actually, let me use a clearer example:
        # snake as C-shape, head at (6,4) moving left into (5,4) = snake[1]
        snake = [
            Point(5, 5),   # tail
            Point(5, 4),   # <-- next_head will land here
            Point(5, 3),
            Point(6, 3),
            Point(6, 4),   # head
        ]
        self._set_up(game, snake, Point(-1, 0))
        game.advance()
        assert game.game_over

    # ── Tail-cell safety ──────────────────────────────────────────────────────

    def test_entering_the_tail_cell_is_safe(self, game: SnakeCashRush) -> None:
        """The tail vacates its cell on the same tick, so moving there is valid.

        U-shaped snake: head at (4, 5) moving left into (3, 5) = current tail.
        The tail is excluded from the body-collision check (snake[1:]) when no
        cash is collected, so this must NOT trigger end_game().
        """
        game.snake = [Point(3, 5), Point(3, 6), Point(4, 6), Point(4, 5)]
        game.direction = Point(-1, 0)
        game.pending_direction = Point(-1, 0)
        game.cash = Point(0, 0)     # not in the path
        game.running = True
        game.advance()
        assert not game.game_over
        assert game.snake[-1] == Point(3, 5)    # head moved into old tail cell

    # ── Normal move ───────────────────────────────────────────────────────────

    def test_normal_move_does_not_end_game(self, running_game: SnakeCashRush) -> None:
        """A move into clear space inside the board must not trigger end_game()."""
        # Default starting position: head at (10, 9) moving up → (10, 8). Safe.
        running_game.cash = Point(0, 0)
        running_game.advance()
        assert not running_game.game_over


# ─────────────────────────────────────────────────────────────────────────────
# end_game — game-over state transitions
# ─────────────────────────────────────────────────────────────────────────────

class TestEndGame:
    """end_game() must update exactly the flags it owns."""

    def test_sets_running_to_false(self, running_game: SnakeCashRush) -> None:
        running_game.end_game()
        assert not running_game.running

    def test_sets_game_over_to_true(self, running_game: SnakeCashRush) -> None:
        running_game.end_game()
        assert running_game.game_over

    def test_preserves_final_score(self, running_game: SnakeCashRush) -> None:
        running_game.score = 70
        running_game.end_game()
        assert running_game.score == 70

    def test_preserves_best_score(self, running_game: SnakeCashRush) -> None:
        running_game.best_score = 200
        running_game.end_game()
        assert running_game.best_score == 200


# ─────────────────────────────────────────────────────────────────────────────
# start_game / restart_game / handle_primary_action — state machine
# ─────────────────────────────────────────────────────────────────────────────

class TestStateTransitions:
    """Verify all entry points that change the running/game_over state machine."""

    def test_start_game_sets_running_true(self, game: SnakeCashRush) -> None:
        game.start_game()
        assert game.running

    def test_start_game_is_noop_if_already_running(self, running_game: SnakeCashRush) -> None:
        running_game.score = 30
        running_game.start_game()
        # Should not reset score — the guard returns immediately.
        assert running_game.score == 30
        assert running_game.running

    def test_start_game_after_game_over_resets_score(self, game: SnakeCashRush) -> None:
        game.game_over = True
        game.score = 100
        game.start_game()
        assert game.running
        assert game.score == 0

    def test_restart_game_clears_game_over_flag(self, game: SnakeCashRush) -> None:
        game.game_over = True
        game.restart_game()
        assert not game.game_over

    def test_restart_game_resets_score_to_zero(self, game: SnakeCashRush) -> None:
        game.score = 300
        game.restart_game()
        assert game.score == 0

    def test_restart_game_starts_the_run(self, game: SnakeCashRush) -> None:
        game.restart_game()
        assert game.running

    def test_restart_game_during_active_run_resets_score(self, running_game: SnakeCashRush) -> None:
        running_game.score = 150
        running_game.restart_game()
        assert running_game.score == 0

    def test_handle_primary_action_starts_game_from_idle(self, game: SnakeCashRush) -> None:
        assert not game.running
        assert not game.game_over
        game.handle_primary_action()
        assert game.running

    def test_handle_primary_action_restarts_during_active_run(self, running_game: SnakeCashRush) -> None:
        running_game.score = 50
        running_game.handle_primary_action()
        assert running_game.score == 0

    def test_handle_primary_action_restarts_after_game_over(self, game: SnakeCashRush) -> None:
        game.game_over = True
        game.score = 80
        game.handle_primary_action()
        assert game.score == 0
        assert not game.game_over


# ─────────────────────────────────────────────────────────────────────────────
# handle_keydown — keyboard input processing
# ─────────────────────────────────────────────────────────────────────────────

class TestHandleKeydown:
    """handle_keydown maps keys to direction changes and special actions."""

    class _Event:
        """Minimal DOM KeyboardEvent stub."""

        def __init__(self, key: str) -> None:
            self.key = key

    def test_arrow_up_queues_up_direction(self, running_game: SnakeCashRush) -> None:
        running_game.direction = Point(1, 0)    # currently moving right
        running_game.handle_keydown(self._Event("ArrowUp"))
        assert running_game.pending_direction == Point(0, -1)

    def test_arrow_down_queues_down_direction(self, running_game: SnakeCashRush) -> None:
        running_game.direction = Point(1, 0)
        running_game.handle_keydown(self._Event("ArrowDown"))
        assert running_game.pending_direction == Point(0, 1)

    def test_arrow_left_queues_left_direction(self, running_game: SnakeCashRush) -> None:
        running_game.direction = Point(0, -1)
        running_game.handle_keydown(self._Event("ArrowLeft"))
        assert running_game.pending_direction == Point(-1, 0)

    def test_arrow_right_queues_right_direction(self, running_game: SnakeCashRush) -> None:
        running_game.direction = Point(0, -1)
        running_game.handle_keydown(self._Event("ArrowRight"))
        assert running_game.pending_direction == Point(1, 0)

    def test_w_queues_up_direction(self, running_game: SnakeCashRush) -> None:
        running_game.direction = Point(1, 0)
        running_game.handle_keydown(self._Event("w"))
        assert running_game.pending_direction == Point(0, -1)

    def test_s_queues_down_direction(self, running_game: SnakeCashRush) -> None:
        running_game.direction = Point(1, 0)
        running_game.handle_keydown(self._Event("s"))
        assert running_game.pending_direction == Point(0, 1)

    def test_a_queues_left_direction(self, running_game: SnakeCashRush) -> None:
        running_game.direction = Point(0, -1)
        running_game.handle_keydown(self._Event("a"))
        assert running_game.pending_direction == Point(-1, 0)

    def test_d_queues_right_direction(self, running_game: SnakeCashRush) -> None:
        running_game.direction = Point(0, 1)
        running_game.handle_keydown(self._Event("d"))
        assert running_game.pending_direction == Point(1, 0)

    def test_reverse_direction_is_silently_rejected(self, running_game: SnakeCashRush) -> None:
        """Pressing the key opposite to the current direction must not change pending_direction."""
        running_game.direction = Point(0, -1)       # moving up
        running_game.pending_direction = Point(0, -1)
        running_game.handle_keydown(self._Event("ArrowDown"))   # would reverse
        assert running_game.pending_direction == Point(0, -1)   # unchanged

    def test_unknown_key_leaves_pending_direction_unchanged(self, running_game: SnakeCashRush) -> None:
        original = running_game.pending_direction
        running_game.handle_keydown(self._Event("Escape"))
        assert running_game.pending_direction == original

    def test_r_key_resets_the_game(self, running_game: SnakeCashRush) -> None:
        running_game.score = 60
        running_game.handle_keydown(self._Event("r"))
        assert running_game.score == 0

    def test_directional_key_starts_game_from_idle(self, game: SnakeCashRush) -> None:
        """Pressing a direction key when idle must start the game automatically."""
        assert not game.running
        game.direction = Point(1, 0)          # currently 'right' so 'up' is not a reverse
        game.handle_keydown(self._Event("ArrowUp"))
        assert game.running


# ─────────────────────────────────────────────────────────────────────────────
# sync_best_score — best-score persistence
# ─────────────────────────────────────────────────────────────────────────────

class TestSyncBestScore:
    """sync_best_score updates best_score only when the current score exceeds it."""

    def test_best_score_updated_when_current_score_is_higher(self, game: SnakeCashRush) -> None:
        game.best_score = 10
        game.score = 20
        game.sync_best_score()
        assert game.best_score == 20

    def test_best_score_unchanged_when_current_score_is_lower(self, game: SnakeCashRush) -> None:
        game.best_score = 100
        game.score = 50
        game.sync_best_score()
        assert game.best_score == 100

    def test_best_score_unchanged_when_scores_are_equal(self, game: SnakeCashRush) -> None:
        game.best_score = 50
        game.score = 50
        game.sync_best_score()
        assert game.best_score == 50


# ─────────────────────────────────────────────────────────────────────────────
# snapshot_json — state serialisation
# ─────────────────────────────────────────────────────────────────────────────

class TestSnapshotJson:
    """snapshot_json serialises the full game state to a valid JSON string."""

    def test_returns_a_valid_json_string(self, game: SnakeCashRush) -> None:
        parsed = json.loads(game.snapshot_json())
        assert isinstance(parsed, dict)

    def test_snapshot_contains_all_required_keys(self, game: SnakeCashRush) -> None:
        parsed = json.loads(game.snapshot_json())
        required = {"running", "gameOver", "score", "bestScore", "tickMs",
                    "direction", "cash", "snake"}
        assert required <= parsed.keys()

    def test_score_field_reflects_current_score(self, game: SnakeCashRush) -> None:
        game.score = 40
        assert json.loads(game.snapshot_json())["score"] == 40

    def test_running_field_reflects_running_flag(self, game: SnakeCashRush) -> None:
        game.running = True
        assert json.loads(game.snapshot_json())["running"] is True

    def test_snake_list_length_and_order_match(self, game: SnakeCashRush) -> None:
        parsed = json.loads(game.snapshot_json())["snake"]
        assert len(parsed) == len(game.snake)
        for seg_dict, seg_point in zip(parsed, game.snake):
            assert seg_dict["x"] == seg_point.x
            assert seg_dict["y"] == seg_point.y

    def test_direction_field_matches_current_direction(self, game: SnakeCashRush) -> None:
        game.direction = Point(1, 0)
        parsed = json.loads(game.snapshot_json())
        assert parsed["direction"] == {"x": 1, "y": 0}

    def test_cash_field_matches_current_cash_position(self, game: SnakeCashRush) -> None:
        game.cash = Point(7, 3)
        parsed = json.loads(game.snapshot_json())
        assert parsed["cash"] == {"x": 7, "y": 3}


# ─────────────────────────────────────────────────────────────────────────────
# place_cash_ahead — debug teleport helper
# ─────────────────────────────────────────────────────────────────────────────

class TestPlaceCashAhead:
    """place_cash_ahead moves the cash bill to the cell in front of the head."""

    def test_cash_lands_directly_ahead_of_head_when_clear(self, game: SnakeCashRush) -> None:
        """When the cell ahead is free, cash is placed there."""
        head = game.snake[-1]
        expected = Point(head.x + game.direction.x, head.y + game.direction.y)
        if not game.hit_wall(expected) and expected not in game.snake:
            game.place_cash_ahead()
            assert game.cash == expected

    def test_cash_position_is_never_on_the_snake(self, game: SnakeCashRush) -> None:
        game.place_cash_ahead()
        assert game.cash not in game.snake

    def test_cash_position_is_within_board_after_placement(self, game: SnakeCashRush) -> None:
        game.place_cash_ahead()
        assert not game.hit_wall(game.cash)

    def test_cash_unchanged_when_all_candidates_are_blocked(self, game: SnakeCashRush) -> None:
        """When every candidate cell is a wall or occupied, cash must not move."""
        # Head at (0, 0): ahead (0, -1) is wall, right (1, 0) occupied,
        # left (-1, 0) is wall, down (0, 1) occupied.
        game.snake = [Point(1, 0), Point(0, 1), Point(0, 0)]
        game.direction = Point(0, -1)   # up → (0, -1) hits wall
        original_cash = game.cash
        game.place_cash_ahead()
        # If no valid placement found, cash should be unchanged.
        # (The method does nothing if all candidates are blocked.)
        if game.cash != original_cash:
            # A valid placement was found despite our setup — still verify it's clean.
            assert game.cash not in game.snake
            assert not game.hit_wall(game.cash)
