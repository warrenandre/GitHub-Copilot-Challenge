# Intent: Snake Cash Rush

## User Request
Build a classic Snake web game that feels unique and super fun to play, where the snake eats money bills to grow, with a sleek modern UI and a score keeper.

## Inferred Product Intent
- Create a lightweight browser-based game that can run locally without backend infrastructure.
- Preserve the core Snake loop so the game is instantly familiar.
- Add a money-theme twist by replacing standard food with animated money bills.
- Make the presentation feel polished and modern rather than arcade-basic.
- Keep score visibly during play and preserve the best score within the browser.
- Provide a detailed getting started guide so the app is easy to run locally.

## Assumptions
- This will be a single-page web app in an otherwise empty workspace.
- The game source should be built under `games/snake/src`.
- The game logic should be implemented in Python while still running as a browser-playable web app.
- The score keeper means current score plus best score stored locally.
- "Unique and super fun" should come from visual theme, juice effects, speed tuning, and responsive controls rather than changing Snake into a different genre.
- The app should work on desktop first, with reasonable mobile support if the chosen controls allow it.

## Success Criteria
- Player can start, play, lose, and restart the game without reloading the page.
- Snake grows when it eats money bills.
- Score increases during play and best score is retained in local storage.
- UI feels modern, intentional, and visually distinct.
- Gameplay remains smooth and readable.

## Open Choices To Confirm Later
- Whether to include optional features such as pause, sound, combo scoring, or touch controls.
- Whether the best score is enough, or if a short leaderboard is needed.