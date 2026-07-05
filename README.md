# GitHub Copilot Enterprise Challenge Race

Build enterprise-grade software with GitHub Copilot — race through 4 challenges to level up your code!

## Challenge Tracker

**[Launch the Challenge Tracker](https://github-copilot-challenge-tracker.azurewebsites.net/)**

## What Is This?

A hands-on hackathon challenge where participants use GitHub Copilot to apply enterprise best practices to an existing Python Snake game. You'll race through 4 challenges, each focusing on a key pillar of production-ready software.

## The Challenges

| # | Challenge | Focus |
|---|-----------|-------|
| 1 | Documentation | README, docstrings, and inline comments |
| 2 | Testing | Unit tests and edge case coverage |
| 3 | Code Readability | Refactoring, naming, and clean structure |
| 4 | Exception Handling | Error handling and graceful fallbacks |

## How It Works

1. Visit the [Challenge Tracker](https://github-copilot-challenge-tracker.azurewebsites.net/) for step-by-step instructions
2. Create a branch with your initials and surname (e.g. `jd-doe`)
3. Open the Snake Cash Rush project in VS Code with GitHub Copilot
4. Complete each challenge using Copilot Chat prompts
5. Commit and push your changes after each challenge

## Pre-requisites

- [Visual Studio Code](https://code.visualstudio.com/download)
- [Python 3.10+](https://www.python.org/downloads/)
- GitHub Copilot and GitHub Copilot Chat extensions installed
- A modern browser (Edge or Chrome)

## Running the Snake Game

```powershell
cd games/snake
python -m http.server 8000
```

Then open http://localhost:8000/src/ in your browser.

## Project Structure

```
games/snake/        # The Snake Cash Rush game (your target project)
home/               # Challenge tracker web page
specs/              # Challenge specifications and scoring
```

## Scoring

Your branch is scored across 5 categories by an automated GitHub workflow:

- **Documentation** — 20 points
- **Testing** — 25 points
- **Code Readability** — 25 points
- **Exception Handling** — 20 points
- **CI/CD** — 10 points

Push your changes and check the repo issues for your score report.
