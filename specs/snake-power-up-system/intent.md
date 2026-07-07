# Intent

## Goal
Introduce a power-up system in Snake Cash Rush where the snake can collect temporary special items that grant gameplay abilities, starting with speed boost, invincibility, and double points.

## Problem Statement
Gameplay currently revolves around collecting standard cash pickups and avoiding collisions. This can become predictable over time, and there is no temporary risk-reward layer beyond baseline movement and scaling difficulty. A power-up system adds moment-to-moment variety, tactical decisions, and stronger progression feel during each run.

## Target Users
- Primary: Players of Snake Cash Rush who want more dynamic gameplay.
- Secondary: Maintainers of the PyScript codebase who need a structured way to extend gameplay mechanics safely.

## Constraints
- The game is a PyScript browser game.
- Python DOM interactions must use js module imports.
- Game state must remain encapsulated in the SnakeCashRush class.
- Power-up effects are temporary and must expire predictably.
- New mechanics must preserve existing controls and baseline game loop responsiveness.
- The first release scope includes exactly three power-up types:
  - Speed boost
  - Invincibility
  - Double points

## Acceptance Criteria
1. Power-up spawn and pickup
- During active gameplay, power-up items appear on valid board positions.
- A collected power-up is removed from the board and immediately applies its effect.

2. Supported power-up effects
- Speed boost temporarily increases movement speed for a defined duration.
- Invincibility temporarily prevents death from collision logic for a defined duration.
- Double points temporarily multiplies scoring rewards by 2 for qualifying score events.

3. Effect timing and lifecycle
- Each effect has a clear start time and end time.
- Effects end automatically when duration elapses.
- Expiration behavior is deterministic and testable.

4. Rules interaction
- Invincibility collision behavior is explicitly defined and consistently applied.
- Double points affects score additions while active and does not persist after expiration.
- Speed boost transitions in and out without freezing or skipping game updates.

5. UI and feedback
- The player can identify active power-up effects during gameplay.
- Remaining duration is visible or inferable through clear visual feedback.

6. Stability and compatibility
- Existing non-power-up gameplay remains functional.
- No global mutable game state is introduced outside SnakeCashRush.
- Existing restart/game-over flow continues to work with active or expiring effects.

## Open Questions
- Feature naming: Confirm folder slug as snake-power-up-system, or provide your preferred feature name.
- Spawn rules: Should only one power-up exist at a time, or can multiple exist concurrently?
- Stacking rules: If the same type is collected while active, should it refresh duration, stack intensity, or be ignored?
- Invincibility behavior: Should the snake pass through walls/body, bounce, or simply ignore death while still moving normally?
- Duration defaults: What durations should each effect use (for example 5s, 8s, 10s)?
- Spawn cadence: Time-based spawning, score-based spawning, or random chance each tick?
- Double points scope: Should it apply only to cash pickups, or also to other scoring events if introduced later?
