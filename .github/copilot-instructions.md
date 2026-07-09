# GitHub Copilot Instructions

This file contains guidelines and best practices for GitHub Copilot when generating code for this repository. Follow these conventions to maintain consistency and code quality across the project.

## Python Code Standards

### Type Hints

**Requirement**: Always use Python type hints for function parameters and return values.

**Examples**:

```python
# Good ✓
def calculate_total(items: list[int], tax_rate: float) -> float:
    """Calculate total with tax."""
    return sum(items) * (1 + tax_rate)

def process_data(data: dict[str, int] | None) -> list[str]:
    """Process data and return results."""
    if data is None:
        return []
    return [f"{k}:{v}" for k, v in data.items()]

# Avoid ✗
def calculate_total(items, tax_rate):
    return sum(items) * (1 + tax_rate)

def process_data(data):
    if data is None:
        return []
    return [f"{k}:{v}" for k, v in data.items()]
```

**Guidelines**:
- Use built-in types for simple cases: `str`, `int`, `float`, `bool`, `list`, `dict`, `set`, `tuple`
- Use `list[T]`, `dict[K, V]`, `set[T]`, `tuple[T, ...]` for generic types (Python 3.9+)
- Use union types with `|` for multiple types: `str | None`, `int | float`
- For complex types, import from `typing`: `Optional`, `Union`, `Callable`, `TypeVar`, etc.
- Always include return type hints, even if returning `None`

### PEP 8 Naming Conventions

**Requirement**: Follow PEP 8 naming conventions strictly.

**Examples**:

```python
# Good ✓
class DataProcessor:
    MAX_RETRIES = 3
    DEFAULT_TIMEOUT = 30
    
    def process_items(self) -> None:
        """Process items from queue."""
        pass
    
    def _internal_helper(self) -> str:
        """Internal helper method."""
        return "result"
    
    @property
    def item_count(self) -> int:
        """Return total item count."""
        return len(self.items)

user_data = {"name": "Alice", "age": 30}
max_attempts = 5
is_valid = True

# Avoid ✗
class dataProcessor:
    maxRetries = 3
    
    def ProcessItems(self):
        pass
    
    def InternalHelper(self):
        return "result"

UserData = {"name": "Alice"}
MAX_Attempts = 5
isValid = True
```

**Guidelines**:
- **Classes**: Use `PascalCase` (e.g., `GameEngine`, `DataProcessor`)
- **Functions and methods**: Use `snake_case` (e.g., `calculate_total`, `process_items`)
- **Constants**: Use `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private methods/attributes**: Prefix with single underscore `_` (e.g., `_internal_method`)
- **Variables**: Use `snake_case` (e.g., `user_data`, `is_valid`)
- **Boolean variables**: Prefix with `is_`, `has_`, `can_`, `should_` (e.g., `is_active`, `has_items`)

### Docstrings with Args and Returns

**Requirement**: Always include comprehensive docstrings for all functions, methods, and classes. Use the Google-style docstring format with `Args` and `Returns` sections.

**Examples**:

```python
# Good ✓
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate final price after applying discount.
    
    Applies a percentage-based discount to the given price and returns
    the final amount. Validates that discount is between 0 and 100.
    
    Args:
        price: The original price in dollars.
        discount_percent: The discount percentage (0-100).
    
    Returns:
        The final price after discount.
    
    Raises:
        ValueError: If discount_percent is not between 0 and 100.
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError(f"Discount must be 0-100, got {discount_percent}")
    return price * (1 - discount_percent / 100)


def fetch_user_data(user_id: int) -> dict[str, str | int] | None:
    """Retrieve user data from the database.
    
    Fetches user information by ID with caching support. Returns None
    if user is not found.
    
    Args:
        user_id: The unique identifier for the user.
    
    Returns:
        A dictionary containing user data (name, email, age) or None
        if user not found.
    """
    # Implementation
    pass


class GameEngine:
    """Main game engine managing game state and updates.
    
    Coordinates game logic, rendering, and input handling. Maintains
    game state and provides methods for state transitions.
    
    Attributes:
        state: Current game state (idle, running, paused, over).
        score: Current player score.
    """
    
    def __init__(self, width: int, height: int) -> None:
        """Initialize the game engine.
        
        Args:
            width: The game board width in pixels.
            height: The game board height in pixels.
        """
        self.width = width
        self.height = height
    
    def update(self, delta_time: float) -> None:
        """Update game state for one frame.
        
        Processes game logic, updates entities, and checks for collisions.
        Should be called once per frame at the target frame rate.
        
        Args:
            delta_time: Time elapsed since last update in milliseconds.
        
        Returns:
            None
        """
        pass


# Avoid ✗
def calculate_discount(price, discount_percent):
    # Missing type hints and docstring
    return price * (1 - discount_percent / 100)

def fetch_user_data(user_id):
    # Minimal docstring without Args/Returns
    """Fetch user from database."""
    pass
```

**Guidelines**:
- Use Google-style docstrings (as shown above)
- Always include:
  - **One-line summary**: Brief description of what the function does
  - **Extended description** (if needed): More detailed explanation of behavior
  - **Args section**: List all parameters with descriptions
  - **Returns section**: Describe what is returned
  - **Raises section** (if applicable): Document exceptions that may be raised
- For methods, document `self` only if non-obvious behavior
- For class docstrings, include Attributes section for public attributes
- Keep descriptions concise but complete

## PyScript Browser Game Standards

**Context**: This project uses PyScript to run Python directly in the browser. The main application is a browser-based Snake game called Snake Cash Rush.

### DOM Interactions

**Requirement**: Use the `js` module to interact with DOM elements. Never use JavaScript directly unless absolutely necessary.

**Examples**:

```python
# Good ✓
from js import document, window

# Get elements
canvas = document.getElementById("gameCanvas")
ctx = canvas.getContext("2d")

# Modify element properties
button.textContent = "Click Me"
element.classList.add("visible")

# Event handling
from pyodide.ffi import create_proxy
event_handler = create_proxy(lambda event: handle_click(event))
button.addEventListener("click", event_handler)

# Browser APIs
window.localStorage.setItem("key", "value")
animation_id = window.requestAnimationFrame(frame_callback)

# Avoid ✗
# Don't use JavaScript strings or eval
# import js; js.eval("document.getElementById(...)")
```

**Guidelines**:
- Import `document` and `window` from `js` module
- Use `document.getElementById()`, `querySelector()` for element selection
- Modify CSS classes via `classList.add()`, `classList.remove()`
- Update text/HTML via `textContent` (preferred) or `innerHTML`
- Always wrap event handlers with `create_proxy()` from `pyodide.ffi`
- Use browser APIs like `localStorage`, `requestAnimationFrame` via `window` object
- Handle Canvas 2D context operations directly on the context object

### Game State Encapsulation

**Requirement**: All game state must be encapsulated in the `SnakeCashRush` class. No global state outside the class.

**Examples**:

```python
# Good ✓
class SnakeCashRush:
    def __init__(self) -> None:
        """Initialize game with all state."""
        self.canvas = document.getElementById("gameCanvas")
        self.ctx = self.canvas.getContext("2d")
        self.score = 0
        self.running = False
        self.snake: list[Point] = []
        self.direction = Point(0, -1)
        # ... more initialization
    
    def start_game(self) -> None:
        """Start the game."""
        self.running = True
        self.score = 0
        # ...

# Instantiate once at module level
game = SnakeCashRush()

# Avoid ✗
# Global state scattered across module
SCORE = 0
RUNNING = False
SNAKE = []
DIRECTION = Point(0, -1)

def start_game() -> None:
    global SCORE, RUNNING
    RUNNING = True
    SCORE = 0
```

**Guidelines**:
- Store all game state as instance variables in `SnakeCashRush`
- Use instance methods to access and modify state
- Create a single instance at module initialization: `game = SnakeCashRush()`
- Pass necessary state to helper functions rather than using globals
- Keep game logic separate from DOM interactions (though DOM references can be instance variables)

### PyScript-Specific Patterns

**Browser Integration**:
- Wrap all DOM event callbacks with `create_proxy()` to ensure proper Python-to-JavaScript bridging
- Use `window.setTimeout()` with `create_proxy()` for scheduled callbacks
- Store proxy references as instance variables to prevent garbage collection
- Use `# type: ignore[import-not-found]` for `js` and `pyodide` imports since they're only available in PyScript

**Example**:

```python
from js import document, window
from pyodide.ffi import create_proxy

class SnakeCashRush:
    def __init__(self) -> None:
        # Store proxies as instance variables to keep them alive
        self._key_proxy = create_proxy(self.handle_keydown)
        self._frame_proxy = create_proxy(self.game_frame)
        self._restart_proxy = create_proxy(lambda _event: self.restart_game())
        
        # Register event listeners
        document.addEventListener("keydown", self._key_proxy)
        self.start_button.addEventListener("click", self._restart_proxy)
        
        # Schedule callbacks
        window.setTimeout(create_proxy(self.initialize), 100)
    
    def handle_keydown(self, event) -> None:
        """Handle keyboard input."""
        key = str(event.key).lower()
        # ...
    
    def destroy(self) -> None:
        """Clean up event listeners and proxies."""
        document.removeEventListener("keydown", self._key_proxy)
        # Proxies are cleaned up when instance is destroyed
```

## Project-Specific Standards

### File Structure

- Keep Python files under 500 lines when possible
- One class per file unless tightly coupled
- Group related functions into modules
- Main game logic should reside in `SnakeCashRush` class

### Testing

- Write tests alongside implementation
- Use descriptive test names: `test_<function>_<condition>_<expected_outcome>`
- Include docstrings explaining complex test logic

### Comments

- Use comments to explain **why**, not **what**
- Code should be self-explanatory; avoid over-commenting
- Use `# type: ignore` sparingly and document why it's needed

## Implementation Checklist

When generating new Python code, ensure:

- [ ] All functions have parameter and return type hints
- [ ] All functions/methods have docstrings with Args and Returns sections
- [ ] Function and variable names follow PEP 8 (snake_case)
- [ ] Class names follow PEP 8 (PascalCase)
- [ ] Constants use UPPER_SNAKE_CASE
- [ ] Private methods are prefixed with `_`
- [ ] Boolean variables start with `is_`, `has_`, `can_`, or `should_`
- [ ] No unused imports or variables
- [ ] Code passes basic linting (pylint, flake8, or pyright)

### PyScript-Specific Checklist

When generating PyScript browser game code, additionally ensure:

- [ ] DOM interactions use `js` module imports (`from js import document, window`)
- [ ] All event handlers are wrapped with `create_proxy()` from `pyodide.ffi`
- [ ] Event handler proxies are stored as instance variables to prevent garbage collection
- [ ] All game state is encapsulated in the `SnakeCashRush` class
- [ ] No global game state variables exist outside the class
- [ ] The `SnakeCashRush` class is instantiated once at module level
- [ ] The class has an `__init__()` method that initializes all state and event listeners
- [ ] The class has a `destroy()` method that cleans up event listeners
- [ ] `# type: ignore[import-not-found]` comments are used for `js` and `pyodide` imports
- [ ] Canvas operations use the 2D context directly (no global canvas variable)
- [ ] All DOM element references are stored as instance variables
- [ ] Helper functions receive necessary parameters rather than accessing global state

## Examples from This Repository

### Snake Cash Rush (main.py)

The Snake game implementation demonstrates these standards:

```python
def spawn_cash(self, snake: Iterable[Point]) -> Point:
    """Spawn a cash item at a random unoccupied board location.
    
    Finds all empty cells (not occupied by the snake) and randomly selects
    one for the new cash item. Falls back to (0, 0) if no cells are available.
    
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
    return choice(available) if available else Point(0, 0)
```

## Questions or Exceptions?

If you encounter a situation where these guidelines don't apply or conflict with project requirements, document the exception and the reasoning in a comment or issue.

---

**Last Updated**: July 9, 2026  
**Version**: 1.0
