# Executive Summary

> Feature: Pause / Resume for Snake Cash Rush
> Derived from: [`specs/intent.md`](./intent.md) · [`specs/design.md`](./design.md) · [`specs/tasks.md`](./tasks.md)

---

## Overview

This feature adds a **pause/resume capability** to Snake Cash Rush, allowing
players to freeze an active run with the **P** key or a dedicated HUD button and
continue exactly where they left off.

## Why It Matters

Players are frequently interrupted mid-run (phone calls, distractions) with no
way to preserve their progress. Without pause, any interruption ends the run.
This is a high-impact, low-effort quality-of-life improvement that directly
reduces player frustration.

## How It Fits the Architecture

Pause state is owned entirely by Python (`main.py`) as a single boolean
`self.paused`, consistent with the project's architectural boundary: game logic
in Python, browser APIs in the JS bridge, UI in HTML/CSS. The animation loop is
preserved while paused — `game_frame` continues to re-queue rAF ticks and
redraw the frozen canvas — enabling instant, glitch-free resume. The existing
overlay system is reused for the paused UI, so no new DOM elements, JS changes,
or external dependencies are introduced.

## Notable Risk

The only non-obvious implementation detail is resetting `self.last_frame_time`
to `0.0` on resume. Without this, the fixed-timestep accumulator would treat the
entire paused duration as elapsed game time and fire many `advance()` ticks in
rapid succession, causing the snake to teleport. The reset costs nothing and
eliminates the risk entirely.

## Effort & Dependencies

Total estimated effort: **S–M (2–4 hours)**. All 10 tasks are self-contained
within the existing codebase. No new libraries, build steps, or server-side
changes are required. The feature is safe to ship independently.
