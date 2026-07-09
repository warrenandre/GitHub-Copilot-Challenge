"""Unit tests for Snake Cash Rush game logic.

Tests cover snake movement, collision detection, score tracking, and game state management.
These tests use a mock environment since the actual game requires PyScript and browser APIs.
"""

import pytest
from dataclasses import dataclass
from typing import Iterable


# Mock the Point dataclass used in main.py
@dataclass(frozen=True)
class Point:
    """Represents a grid position."""
    x: int
    y: int


# Constants from main.py
GRID_SIZE = 20
BOARD_CELLS = 20
BASE_TICK_MS = 160
MIN_TICK_MS = 82
SPEED_STEP_MS = 5
SCORE_PER_BILL = 10


class MockGameState:
    """Mock game state for testing without PyScript/browser dependencies."""
    
    def __init__(self) -> None:
        """Initialize mock game state."""
        center = BOARD_CELLS // 2
        self.snake: list[Point] = [
            Point(center, center + 1),
            Point(center, center),
            Point(center, center - 1),
        ]
        self.direction = Point(0, -1)
        self.pending_direction = Point(0, -1)
        self.cash = Point(0, 0)
        self.score = 0
        self.best_score = 0
        self.tick_ms = BASE_TICK_MS
        self.running = False
        self.game_over = False
    
    def hit_wall(self, point: Point) -> bool:
        """Check if a point is outside the game board boundaries.
        
        Args:
            point: The position to check.
        
        Returns:
            True if the point is outside the board bounds, False otherwise.
        """
        return point.x < 0 or point.y < 0 or point.x >= BOARD_CELLS or point.y >= BOARD_CELLS
    
    def spawn_cash(self, snake: Iterable[Point]) -> Point:
        """Spawn a cash item at a random unoccupied board location.
        
        Args:
            snake: The current snake body as an iterable of Point objects.
        
        Returns:
            A Point object representing the location for the new cash item.
        """
        occupied = set(snake)
        available = [
            Point(x, y)
            for y in range(BOARD_CELLS)
            for x in range(BOARD_CELLS)
            if Point(x, y) not in occupied
        ]
        return available[0] if available else Point(0, 0)
    
    def advance(self) -> None:
        """Advance game state by one tick.
        
        Moves the snake, checks for collisions with walls and body,
        handles cash collection (growing snake and increasing score),
        and increases difficulty.
        """
        self.direction = self.pending_direction
        head = self.snake[-1]
        next_head = Point(head.x + self.direction.x, head.y + self.direction.y)
        will_collect = next_head == self.cash
        collision_body = self.snake if will_collect else self.snake[1:]

        if self.hit_wall(next_head) or next_head in collision_body:
            self.game_over = True
            return

        self.snake.append(next_head)

        if will_collect:
            self.score += SCORE_PER_BILL
            self.tick_ms = max(MIN_TICK_MS, BASE_TICK_MS - (self.score // SCORE_PER_BILL) * SPEED_STEP_MS)
            self.cash = self.spawn_cash(self.snake)
        else:
            self.snake.pop(0)


class TestSnakeMovement:
    """Test suite for snake movement mechanics."""
    
    def test_initial_snake_position(self) -> None:
        """Test that the snake initializes at the center of the board.
        
        The snake should start as a 3-segment line pointing upward.
        """
        game = MockGameState()
        center = BOARD_CELLS // 2
        
        assert len(game.snake) == 3
        assert game.snake[0] == Point(center, center + 1)
        assert game.snake[1] == Point(center, center)
        assert game.snake[2] == Point(center, center - 1)
    
    def test_initial_direction(self) -> None:
        """Test that the snake initially moves upward."""
        game = MockGameState()
        
        assert game.direction == Point(0, -1)
        assert game.pending_direction == Point(0, -1)
    
    def test_move_up(self) -> None:
        """Test moving the snake upward."""
        game = MockGameState()
        game.cash = Point(10, 10)  # Place cash away from snake
        game.pending_direction = Point(0, -1)
        game.running = True
        
        head_before = game.snake[-1]
        game.advance()
        head_after = game.snake[-1]
        
        assert head_after.y == head_before.y - 1
        assert head_after.x == head_before.x
    
    def test_move_down(self) -> None:
        """Test moving the snake downward."""
        game = MockGameState()
        game.cash = Point(10, 10)
        game.direction = Point(0, 1)
        game.pending_direction = Point(0, 1)
        game.running = True
        
        head_before = game.snake[-1]
        game.advance()
        head_after = game.snake[-1]
        
        assert head_after.y == head_before.y + 1
        assert head_after.x == head_before.x
    
    def test_move_left(self) -> None:
        """Test moving the snake left."""
        game = MockGameState()
        game.cash = Point(10, 10)
        game.direction = Point(-1, 0)
        game.pending_direction = Point(-1, 0)
        game.running = True
        
        head_before = game.snake[-1]
        game.advance()
        head_after = game.snake[-1]
        
        assert head_after.x == head_before.x - 1
        assert head_after.y == head_before.y
    
    def test_move_right(self) -> None:
        """Test moving the snake right."""
        game = MockGameState()
        game.cash = Point(10, 10)
        game.direction = Point(1, 0)
        game.pending_direction = Point(1, 0)
        game.running = True
        
        head_before = game.snake[-1]
        game.advance()
        head_after = game.snake[-1]
        
        assert head_after.x == head_before.x + 1
        assert head_after.y == head_before.y
    
    def test_snake_maintains_length_without_cash(self) -> None:
        """Test that snake length stays constant when not collecting cash."""
        game = MockGameState()
        game.cash = Point(10, 10)
        game.running = True
        initial_length = len(game.snake)
        
        game.advance()
        
        assert len(game.snake) == initial_length
    
    def test_snake_tail_follows_body(self) -> None:
        """Test that the snake's tail follows when moving."""
        game = MockGameState()
        game.cash = Point(10, 10)
        game.running = True
        
        initial_body = game.snake[:-1]
        initial_head = game.snake[-1]
        game.advance()
        
        # After one move, the new body should match the old snake (minus tail)
        assert game.snake[:-1] == [initial_head] + initial_body[:-1]


class TestCollisionDetection:
    """Test suite for collision detection."""
    
    def test_wall_collision_left(self) -> None:
        """Test collision detection when hitting the left wall."""
        game = MockGameState()
        
        assert game.hit_wall(Point(-1, 10)) is True
    
    def test_wall_collision_right(self) -> None:
        """Test collision detection when hitting the right wall."""
        game = MockGameState()
        
        assert game.hit_wall(Point(BOARD_CELLS, 10)) is True
    
    def test_wall_collision_top(self) -> None:
        """Test collision detection when hitting the top wall."""
        game = MockGameState()
        
        assert game.hit_wall(Point(10, -1)) is True
    
    def test_wall_collision_bottom(self) -> None:
        """Test collision detection when hitting the bottom wall."""
        game = MockGameState()
        
        assert game.hit_wall(Point(10, BOARD_CELLS)) is True
    
    def test_no_collision_at_boundary(self) -> None:
        """Test that positions at board boundaries are valid."""
        game = MockGameState()
        
        assert game.hit_wall(Point(0, 0)) is False
        assert game.hit_wall(Point(BOARD_CELLS - 1, BOARD_CELLS - 1)) is False
    
    def test_game_over_on_wall_collision(self) -> None:
        """Test that game ends when snake hits a wall."""
        game = MockGameState()
        game.cash = Point(10, 10)
        game.running = True
        game.direction = Point(0, -1)
        game.pending_direction = Point(0, -1)
        
        # Move snake to top-left corner
        while not game.hit_wall(Point(game.snake[-1].x, game.snake[-1].y - 1)):
            game.advance()
            if game.game_over:
                break
        
        # One more move should cause wall collision
        game.advance()
        assert game.game_over is True
    
    def test_game_over_on_self_collision(self) -> None:
        """Test that game ends when snake collides with itself."""
        game = MockGameState()
        game.cash = Point(15, 10)
        game.running = True
        
        # Create a situation where snake can collide with itself
        # Snake starts: [(10, 11), (10, 10), (10, 9)] moving up
        # Move right: [(10, 11), (10, 10), (10, 9), (11, 10)]
        # Move down: [(10, 11), (10, 10), (10, 9), (11, 10), (11, 11)]
        # Move left: [(10, 11), (10, 10), (10, 9), (11, 10), (11, 11), (10, 11)]
        # Move up: [(10, 11), (10, 10), (10, 9), (11, 10), (11, 11), (10, 11), (10, 10)]
        
        # Simpler test: move in a tight loop
        game.direction = Point(1, 0)
        game.pending_direction = Point(1, 0)
        game.advance()  # Move right
        
        game.direction = Point(0, 1)
        game.pending_direction = Point(0, 1)
        game.advance()  # Move down
        
        game.direction = Point(-1, 0)
        game.pending_direction = Point(-1, 0)
        game.advance()  # Move left
        
        game.direction = Point(0, -1)
        game.pending_direction = Point(0, -1)
        game.advance()  # Move up (should collide)
        
        assert game.game_over is True
    
    def test_cash_not_collision_with_body(self) -> None:
        """Test that collecting cash doesn't trigger body collision check."""
        game = MockGameState()
        game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
        game.running = True
        initial_length = len(game.snake)
        
        game.advance()
        
        # Snake should grow (cash collected) not trigger collision
        assert len(game.snake) == initial_length + 1
        assert game.game_over is False


class TestScoreTracking:
    """Test suite for score tracking and difficulty progression."""
    
    def test_initial_score_is_zero(self) -> None:
        """Test that score starts at zero."""
        game = MockGameState()
        
        assert game.score == 0
    
    def test_score_increases_on_cash_collection(self) -> None:
        """Test that score increases by SCORE_PER_BILL when collecting cash."""
        game = MockGameState()
        game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
        game.running = True
        
        game.advance()
        
        assert game.score == SCORE_PER_BILL
    
    def test_multiple_cash_collection(self) -> None:
        """Test that score accumulates correctly with multiple collections."""
        game = MockGameState()
        game.running = True
        
        for _ in range(5):
            game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
            game.advance()
        
        assert game.score == SCORE_PER_BILL * 5
    
    def test_best_score_updated_on_high_score(self) -> None:
        """Test that best score is updated when exceeded."""
        game = MockGameState()
        game.best_score = 50
        game.running = True
        
        for _ in range(10):
            game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
            game.advance()
        
        if game.score > game.best_score:
            game.best_score = game.score
        
        assert game.best_score == 100
    
    def test_best_score_not_downgraded(self) -> None:
        """Test that best score is never decreased."""
        game = MockGameState()
        game.best_score = 100
        game.score = 50
        
        if game.score > game.best_score:
            game.best_score = game.score
        
        assert game.best_score == 100


class TestDifficultyProgression:
    """Test suite for game speed and difficulty progression."""
    
    def test_initial_tick_speed(self) -> None:
        """Test that the game starts at base speed."""
        game = MockGameState()
        
        assert game.tick_ms == BASE_TICK_MS
    
    def test_speed_increases_with_score(self) -> None:
        """Test that game speed increases as score increases."""
        game = MockGameState()
        game.running = True
        initial_tick = game.tick_ms
        
        for _ in range(5):
            game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
            game.advance()
        
        assert game.tick_ms < initial_tick
    
    def test_speed_never_below_minimum(self) -> None:
        """Test that game speed never goes below minimum tick time."""
        game = MockGameState()
        game.score = 10000  # Very high score
        game.running = True
        
        # Simulate many cash collections
        for _ in range(100):
            game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
            game.advance()
            if game.game_over:
                break
        
        assert game.tick_ms >= MIN_TICK_MS
    
    def test_speed_progression_formula(self) -> None:
        """Test that speed progression follows the correct formula."""
        game = MockGameState()
        game.running = True
        
        # Collect exactly 10 bills (score = 100)
        for _ in range(10):
            game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
            game.advance()
            if game.game_over:
                break
        
        expected_tick = BASE_TICK_MS - (10 * SPEED_STEP_MS)
        assert game.tick_ms == expected_tick


class TestGameStateManagement:
    """Test suite for overall game state and state transitions."""
    
    def test_initial_game_not_running(self) -> None:
        """Test that game starts in non-running state."""
        game = MockGameState()
        
        assert game.running is False
        assert game.game_over is False
    
    def test_game_not_advancing_when_not_running(self) -> None:
        """Test that game state doesn't advance when not running."""
        game = MockGameState()
        initial_snake = game.snake.copy()
        initial_score = game.score
        
        game.advance()
        
        # State should be unchanged (except potentially game_over)
        assert game.snake == initial_snake
        assert game.score == initial_score
    
    def test_cash_never_spawned_at_snake_position(self) -> None:
        """Test that cash is never spawned where the snake is."""
        game = MockGameState()
        game.running = True
        
        for _ in range(20):
            game.cash = game.spawn_cash(game.snake)
            assert game.cash not in game.snake
            game.advance()
            if game.game_over:
                break
    
    def test_direction_change_buffering(self) -> None:
        """Test that direction changes are buffered for next tick."""
        game = MockGameState()
        game.cash = Point(10, 10)
        game.running = True
        
        original_direction = game.direction
        game.pending_direction = Point(1, 0)  # Change to moving right
        
        # Direction shouldn't change until advance() is called
        assert game.direction == original_direction
        
        game.advance()
        
        # After advance, direction should match pending
        assert game.direction == Point(1, 0)


class TestCashSpawning:
    """Test suite for cash spawning logic."""
    
    def test_cash_spawns_at_valid_position(self) -> None:
        """Test that cash spawns at a valid board position."""
        game = MockGameState()
        
        cash = game.spawn_cash(game.snake)
        
        assert 0 <= cash.x < BOARD_CELLS
        assert 0 <= cash.y < BOARD_CELLS
    
    def test_cash_not_in_snake_body(self) -> None:
        """Test that cash never spawns inside the snake."""
        game = MockGameState()
        
        for _ in range(50):
            cash = game.spawn_cash(game.snake)
            assert cash not in game.snake
    
    def test_cash_respawns_after_collection(self) -> None:
        """Test that new cash spawns after collection."""
        game = MockGameState()
        game.running = True
        initial_cash = game.cash
        
        game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
        game.advance()
        
        # After collecting cash, new cash should spawn
        assert game.cash != initial_cash


class TestEdgeCasesBoundaryCollisions:
    """Test suite for boundary collision edge cases."""
    
    def test_collision_at_top_boundary(self) -> None:
        """Test collision when snake head reaches y = -1."""
        game = MockGameState()
        game.cash = Point(10, 10)
        game.running = True
        game.direction = Point(0, -1)
        game.pending_direction = Point(0, -1)
        
        # Move to top row
        while game.snake[-1].y > 0:
            game.advance()
        
        assert game.snake[-1].y == 0
        assert game.game_over is False
        
        # One more move should trigger collision
        game.advance()
        assert game.game_over is True
    
    def test_collision_at_bottom_boundary(self) -> None:
        """Test collision when snake head reaches y = BOARD_CELLS."""
        game = MockGameState()
        game.cash = Point(10, 5)
        game.running = True
        game.direction = Point(0, 1)
        game.pending_direction = Point(0, 1)
        
        # Move to bottom row
        while game.snake[-1].y < BOARD_CELLS - 1:
            game.advance()
        
        assert game.snake[-1].y == BOARD_CELLS - 1
        assert game.game_over is False
        
        # One more move should trigger collision
        game.advance()
        assert game.game_over is True
    
    def test_collision_at_left_boundary(self) -> None:
        """Test collision when snake head reaches x = -1."""
        game = MockGameState()
        game.cash = Point(10, 10)
        game.running = True
        game.direction = Point(-1, 0)
        game.pending_direction = Point(-1, 0)
        
        # Move to left column
        while game.snake[-1].x > 0:
            game.advance()
        
        assert game.snake[-1].x == 0
        assert game.game_over is False
        
        # One more move should trigger collision
        game.advance()
        assert game.game_over is True
    
    def test_collision_at_right_boundary(self) -> None:
        """Test collision when snake head reaches x = BOARD_CELLS."""
        game = MockGameState()
        game.cash = Point(5, 10)
        game.running = True
        game.direction = Point(1, 0)
        game.pending_direction = Point(1, 0)
        
        # Move to right column
        while game.snake[-1].x < BOARD_CELLS - 1:
            game.advance()
        
        assert game.snake[-1].x == BOARD_CELLS - 1
        assert game.game_over is False
        
        # One more move should trigger collision
        game.advance()
        assert game.game_over is True
    
    def test_corner_collision_top_left(self) -> None:
        """Test collision at top-left corner."""
        game = MockGameState()
        game.snake = [Point(1, 1), Point(1, 0), Point(0, 0)]
        game.cash = Point(15, 15)
        game.running = True
        game.direction = Point(-1, 0)
        game.pending_direction = Point(-1, 0)
        
        game.advance()
        assert game.game_over is True
    
    def test_corner_collision_bottom_right(self) -> None:
        """Test collision at bottom-right corner."""
        game = MockGameState()
        last_cell = BOARD_CELLS - 1
        game.snake = [Point(last_cell - 1, last_cell - 1), Point(last_cell, last_cell - 1), Point(last_cell, last_cell)]
        game.cash = Point(5, 5)
        game.running = True
        game.direction = Point(1, 0)
        game.pending_direction = Point(1, 0)
        
        game.advance()
        assert game.game_over is True


class TestEdgeCasesSelfCollision:
    """Test suite for self-collision edge cases."""
    
    def test_immediate_reverse_collision(self) -> None:
        """Test that reversing immediately causes collision."""
        game = MockGameState()
        game.cash = Point(10, 10)
        game.running = True
        game.direction = Point(0, -1)
        game.pending_direction = Point(0, -1)
        
        # Move once
        game.advance()
        
        # Try to reverse (should be blocked by is_reverse check)
        game.pending_direction = Point(0, 1)
        initial_direction = game.direction
        game.advance()
        
        # Direction should not have changed due to reverse prevention
        assert game.direction == initial_direction
    
    def test_self_collision_tight_loop(self) -> None:
        """Test self-collision in a tight 4-move loop."""
        game = MockGameState()
        game.cash = Point(15, 15)
        game.running = True
        
        # Create a loop: right, down, left, up
        directions = [Point(1, 0), Point(0, 1), Point(-1, 0), Point(0, -1)]
        initial_length = len(game.snake)
        
        for direction in directions:
            game.direction = direction
            game.pending_direction = direction
            game.advance()
        
        # After loop, should collide with self
        game.advance()
        assert game.game_over is True
    
    def test_self_collision_with_growing_snake(self) -> None:
        """Test self-collision is still possible after snake grows."""
        game = MockGameState()
        game.running = True
        
        # Grow snake multiple times
        for _ in range(5):
            game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
            game.advance()
        
        # Now attempt a collision loop
        game.direction = Point(1, 0)
        game.pending_direction = Point(1, 0)
        
        for _ in range(len(game.snake) + 2):
            if game.game_over:
                break
            
            if game.snake[-1].x == BOARD_CELLS - 1:
                game.pending_direction = Point(0, 1)
            elif game.snake[-1].y == BOARD_CELLS - 1:
                game.pending_direction = Point(-1, 0)
            elif game.snake[-1].x == 0:
                game.pending_direction = Point(0, -1)
            elif game.snake[-1].y == 0:
                game.pending_direction = Point(1, 0)
            
            game.advance()
        
        # Should eventually collide
        assert game.game_over is True


class TestEdgeCasesCashSpawning:
    """Test suite for cash spawning edge cases."""
    
    def test_cash_never_spawns_on_snake_head(self) -> None:
        """Test that cash never spawns at the snake's head position."""
        game = MockGameState()
        
        for _ in range(100):
            cash = game.spawn_cash(game.snake)
            assert cash != game.snake[-1]
    
    def test_cash_never_spawns_on_snake_body(self) -> None:
        """Test that cash never spawns anywhere on the snake."""
        game = MockGameState()
        game.running = True
        
        # Grow snake
        for _ in range(10):
            game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
            game.advance()
        
        # Test spawning
        for _ in range(50):
            cash = game.spawn_cash(game.snake)
            assert cash not in game.snake
    
    def test_cash_spawns_within_valid_bounds(self) -> None:
        """Test that cash always spawns within board boundaries."""
        game = MockGameState()
        
        for _ in range(100):
            cash = game.spawn_cash(game.snake)
            assert 0 <= cash.x < BOARD_CELLS
            assert 0 <= cash.y < BOARD_CELLS
    
    def test_cash_spawn_with_very_long_snake(self) -> None:
        """Test cash spawning when snake occupies many cells."""
        game = MockGameState()
        game.running = True
        
        # Grow snake to occupy many cells
        for _ in range(50):
            game.cash = Point(game.snake[-1].x + 1, game.snake[-1].y)
            if game.hit_wall(game.snake[-1]):
                break
            game.advance()
            if game.game_over:
                break
        
        # Cash should still spawn in available space
        cash = game.spawn_cash(game.snake)
        assert cash not in game.snake
        assert 0 <= cash.x < BOARD_CELLS
        assert 0 <= cash.y < BOARD_CELLS
    
    def test_cash_respawns_at_different_locations(self) -> None:
        """Test that cash respawns at different locations after collection."""
        game = MockGameState()
        game.running = True
        cash_positions = set()
        
        for _ in range(10):
            game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
            game.advance()
            cash_positions.add(game.cash)
        
        # Should have at least some variation (not all the same position)
        assert len(cash_positions) > 1


class TestEdgeCasesGameStateReset:
    """Test suite for game state reset behavior."""
    
    def test_reset_state_restores_initial_snake(self) -> None:
        """Test that reset_state restores the initial snake configuration."""
        game = MockGameState()
        original_snake = game.snake.copy()
        
        # Modify snake
        game.snake = [Point(5, 5), Point(6, 6)]
        
        # Reset
        game.reset_state()
        
        assert game.snake == original_snake
    
    def test_reset_state_clears_score(self) -> None:
        """Test that reset_state clears the current score."""
        game = MockGameState()
        game.score = 500
        
        game.reset_state()
        
        assert game.score == 0
    
    def test_reset_state_resets_direction(self) -> None:
        """Test that reset_state resets direction to initial upward."""
        game = MockGameState()
        game.direction = Point(1, 0)
        game.pending_direction = Point(-1, 0)
        
        game.reset_state()
        
        assert game.direction == Point(0, -1)
        assert game.pending_direction == Point(0, -1)
    
    def test_reset_state_restores_base_speed(self) -> None:
        """Test that reset_state restores game to base speed."""
        game = MockGameState()
        game.tick_ms = 50  # Modified speed
        
        game.reset_state()
        
        assert game.tick_ms == BASE_TICK_MS
    
    def test_reset_state_clears_game_over_flag(self) -> None:
        """Test that reset_state clears the game over flag."""
        game = MockGameState()
        game.game_over = True
        
        game.reset_state()
        
        assert game.game_over is False
    
    def test_reset_state_stops_game(self) -> None:
        """Test that reset_state sets running to False."""
        game = MockGameState()
        game.running = True
        
        game.reset_state()
        
        assert game.running is False
    
    def test_reset_does_not_clear_best_score(self) -> None:
        """Test that reset_state preserves the best score."""
        game = MockGameState()
        game.best_score = 1000
        game.score = 500
        
        game.reset_state()
        
        assert game.best_score == 1000
        assert game.score == 0
    
    def test_multiple_resets_in_sequence(self) -> None:
        """Test that multiple resets maintain consistent state."""
        game = MockGameState()
        
        for _ in range(5):
            game.score = 999
            game.game_over = True
            game.reset_state()
            
            assert game.score == 0
            assert game.game_over is False
            assert len(game.snake) == 3


class TestEdgeCasesGameFlow:
    """Test suite for complex game flow edge cases."""
    
    def test_rapid_direction_changes(self) -> None:
        """Test that rapid direction changes are buffered correctly."""
        game = MockGameState()
        game.cash = Point(10, 10)
        game.running = True
        game.direction = Point(0, -1)
        
        # Rapid direction changes
        game.pending_direction = Point(1, 0)
        game.pending_direction = Point(0, 1)
        game.pending_direction = Point(-1, 0)
        
        # Only the last pending direction should matter
        game.advance()
        assert game.direction == Point(-1, 0)
    
    def test_score_increments_correctly_with_multiple_collections(self) -> None:
        """Test that score increments are consistent across multiple collections."""
        game = MockGameState()
        game.running = True
        expected_score = 0
        
        for i in range(1, 11):
            game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
            game.advance()
            expected_score += SCORE_PER_BILL
            
            assert game.score == expected_score
            assert game.score == i * SCORE_PER_BILL
    
    def test_speed_increases_are_monotonic(self) -> None:
        """Test that speed always decreases (tick_ms gets smaller) monotonically."""
        game = MockGameState()
        game.running = True
        previous_tick = game.tick_ms
        
        for i in range(20):
            game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
            game.advance()
            
            if i > 0:
                # Speed should either stay same (at minimum) or decrease
                assert game.tick_ms <= previous_tick
                previous_tick = game.tick_ms
    
    def test_snake_length_increases_only_on_cash_collection(self) -> None:
        """Test that snake only grows when collecting cash."""
        game = MockGameState()
        game.cash = Point(15, 15)
        game.running = True
        initial_length = len(game.snake)
        
        # Move without collecting cash
        for _ in range(10):
            game.advance()
        
        assert len(game.snake) == initial_length
        
        # Collect cash and verify growth
        game.cash = Point(game.snake[-1].x, game.snake[-1].y - 1)
        game.advance()
        
        assert len(game.snake) == initial_length + 1
    
    def test_game_over_prevents_further_advances(self) -> None:
        """Test that game over state persists through advance calls."""
        game = MockGameState()
        game.cash = Point(10, 10)
        game.running = True
        
        # Move to wall and trigger collision
        game.direction = Point(0, -1)
        game.pending_direction = Point(0, -1)
        while not game.game_over:
            game.advance()
        
        assert game.game_over is True
        
        # Further advances shouldn't change state meaningfully
        snake_at_gameover = game.snake.copy()
        score_at_gameover = game.score
        
        game.advance()
        
        # Game over shouldn't allow further movement
        assert game.running is False


class TestEdgeCasesZeroEdgeCases:
    """Test suite for zero and extreme value edge cases."""
    
    def test_zero_score_game(self) -> None:
        """Test game flow with zero score."""
        game = MockGameState()
        assert game.score == 0
        assert game.best_score == 0
        
        game.running = True
        game.cash = Point(10, 10)
        game.advance()
        
        # Score should still be zero if no cash collected
        assert game.score == 0
    
    def test_single_segment_collision_detection(self) -> None:
        """Test collision detection works with minimal snake."""
        game = MockGameState()
        game.snake = [Point(10, 10)]
        game.cash = Point(15, 15)
        game.running = True
        
        # Wall collision should work
        game.direction = Point(0, -1)
        game.pending_direction = Point(0, -1)
        
        while game.snake[-1].y > 0:
            game.advance()
        
        game.advance()
        assert game.game_over is True
    
    def test_maximum_board_occupancy(self) -> None:
        """Test behavior when snake fills significant board space."""
        game = MockGameState()
        game.running = True
        max_cells = BOARD_CELLS * BOARD_CELLS
        
        # Fill as much as possible without hitting wall
        while len(game.snake) < max_cells - 10 and not game.game_over:
            game.cash = Point(game.snake[-1].x + 1, game.snake[-1].y)
            game.advance()
        
        # Should still be able to spawn cash
        if not game.game_over:
            cash = game.spawn_cash(game.snake)
            assert cash is not None
            assert cash not in game.snake


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
