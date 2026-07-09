# GitHub Copilot Enterprise Challenge Race

Build enterprise-grade software with GitHub Copilot — race through 4 challenges to level up your code!


## Challenge Website

**<a href="https://github-copilot-challange.azurewebsites.net/" target="_blank">Launch the Challenge Website</a>**


## Challenge Tracker

**<a href="https://githubcopilot-race-challenge.azurewebsites.net/race" target="_blank">Launch the Challenge Tracker</a>**

## What Is This?

A hands-on hackathon challenge where participants use GitHub Copilot to apply enterprise best practices to an existing Python Snake game. You'll race through 4 challenges, each focusing on a key pillar of production-ready software.

## The Challenges

| # | Challenge | Focus |
|---|-----------|-------|
| 1 | Documentation | README, docstrings, and inline comments |
| 2 | Testing | Unit tests and edge case coverage |
| 3 | CI/CD | Automated pipelines for linting and testing |
| 4 | Exception Handling | Error handling and graceful fallbacks |

## How It Works

1. Clone this repository to your local machine
2. Visit the <a href="https://github-copilot-challange.azurewebsites.net/" target="_blank">Challenge Website</a> for step-by-step instructions
3. Create a branch with your initials and surname (e.g. `jd-doe`)
4. Open the Snake Cash Rush project in VS Code with GitHub Copilot
5. Complete each challenge using Copilot Chat prompts
6. Commit and push your changes after each challenge

## Getting Started

```powershell
# Clone the repository
git clone https://github.com/warrenandre/GitHub-Copilot-Challenge
cd GitHub-Copilot-Challenge
```

## Pre-requisites

- <a href="https://git-scm.com/downloads" target="_blank">Git</a>
- <a href="https://code.visualstudio.com/download" target="_blank">Visual Studio Code</a>
- <a href="https://www.python.org/downloads/" target="_blank">Python 3.10+</a>
- GitHub Copilot and GitHub Copilot Chat extensions installed
- A modern browser (Edge or Chrome)

## Running the Snake Game (Optional)

> **Note:** Running the game is optional. The challenges can be completed by reading and modifying the source code directly — you don't need to run the game to participate.

```powershell
cd games/snake
python -m http.server 8000
```

Then open http://localhost:8000/src/ in your browser.

## Snake Game Guide

For full gameplay, architecture, controls, and troubleshooting details, see [games/snake/README.md](games/snake/README.md).

## Project Structure

```
games/snake/        # The Snake Cash Rush game (your target project)
home/               # Challenge tracker web page
specs/              # Challenge specifications and scoring
```

## Scoring

Your branch is scored across 4 categories by an automated GitHub workflow:

- **Documentation** — 25 points
- **Testing** — 30 points
- **CI/CD** — 20 points
- **Exception Handling** — 25 points

Push your changes and check the repo issues for your score report.
