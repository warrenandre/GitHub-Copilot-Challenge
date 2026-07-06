---
description: |
  This workflow creates repository enterprise-readiness score reports. It
  evaluates the codebase for documentation, custom instructions, spec-driven
  development agent, and testing, then publishes a scored summary as a GitHub issue.

on: push
permissions:
  contents: read
  issues: read
  pull-requests: read

network: defaults

tools:
  github:
    # If in a public repo, setting `lockdown: false` allows
    # reading issues, pull requests and comments from 3rd-parties
    # If in a private repo this has no particular effect.
    lockdown: false
    min-integrity: none # This workflow is allowed to examine and comment on any issues

safe-outputs:
  mentions: false
  allowed-github-references: []
  create-issue:
    title-prefix: "[repo-score] "
    labels: [report, repo-score, enterprise-score]
    deduplicate-by-title: true
  update-issue:
    target: "*"
    body: true
source: local/customized-for-repo-score
---

# Repo Score

Create a repository enterprise-readiness score report as a GitHub issue.

The issue title MUST always follow this exact format: `[repo-score] Branch: <branchname>` where `<branchname>` is the name of the branch being scored. The `[repo-score]` prefix is added automatically — you only need to provide `Branch: <branchname>` as the title.

## What to include

- An overall enterprise-readiness score out of 100 for the current repository state
- A category breakdown covering documentation, custom instructions, spec-driven development agent, and testing
- The strongest signals that the repository is enterprise-ready
- The biggest gaps preventing the repository from being enterprise-ready
- Exactly 3 high-value recommendations for improving the score
- A compact evidence snapshot listing the files, directories, workflows, or configuration signals used in the assessment

## Scoring model

- Documentation (Challenge 1): 25 points
  Look for a useful README in `games/snake/`, docstrings on classes and methods in `main.py`, inline comments explaining intent, setup instructions, architecture notes, or gameplay guidance. Award full points when a new developer could understand and run the project using only the documentation.

- Custom Instructions (Challenge 2): 25 points
  Look for a `.github/copilot-instructions.md` file. Award points based on: file exists (5 pts), covers naming conventions and code style (7 pts), covers architectural patterns and project-specific context like tech stack and dependencies (7 pts), and evidence that Copilot-generated code follows the defined standards (6 pts).

- Spec-Driven Development Agent (Challenge 3): 30 points
  Look for a custom agent file at `.github/agents/spec-driven-dev.agent.md` or similar path. Award points based on: agent file exists with a well-defined persona and phased workflow (7 pts), Phase 1 intent document exists with goal, constraints and criteria (6 pts), Phase 2 design document exists with architecture and components (6 pts), Phase 3 tasks document exists with actionable task breakdown (5 pts), executive summary document exists suitable for stakeholders (6 pts). Spec documents should be in a `specs/` folder with `intent.md`, `design.md`, `tasks.md`, and `summary.md`.

- Testing (Challenge 4): 20 points
  Look for test files (e.g. `games/snake/tests/test_main.py`). Award points based on: test file exists with meaningful test cases (4 pts), tests cover happy paths like movement and scoring (5 pts), tests cover edge cases like collisions and boundaries (5 pts), tests pass when executed (3 pts), tests are well-named describing the behavior they verify (3 pts).

## Report format

Use GitHub-flavored markdown and keep the visible content concise.

### Overall Score
- Show the score as `NN/100`.
- Give a short executive summary in 1 to 2 sentences.

### Category Breakdown
- One bullet per category with score, strongest evidence, and biggest missing signal.
- Format: `**Category Name** (Challenge N): XX/YY — evidence summary`

### Strengths
- 2 to 4 concise bullets.

### Gaps
- 2 to 5 concise bullets.

### Top Actions
1. First highest-value action.
2. Second highest-value action.
3. Third highest-value action.

### Evidence Snapshot
- List the most relevant files, directories, workflows, or config assets used in the assessment.

<details><summary>Scoring Notes</summary>

- Include caveats, ambiguous findings, or partial signals here.

</details>

## Style

- Be concise, factual, and useful
- Do not invent evidence that is not present in the repository
- Make uncertainty explicit when signals are weak or incomplete
- Focus on maintainers and engineering leads, not community engagement

## Process

1. Determine the pushed branch name from the event context.
2. Build the report title from the branch name, using the configured issue title prefix automatically.
3. Inspect the checked-out repository first.
4. Study the repository structure looking specifically for:
   - README and docstrings (Challenge 1: Documentation)
   - `.github/copilot-instructions.md` (Challenge 2: Custom Instructions)
   - `.github/agents/*.agent.md` and `specs/` folder contents (Challenge 3: Spec-Driven Development Agent)
   - Test files in `games/snake/tests/` or similar (Challenge 4: Testing)
5. Use GitHub reads when needed to find an existing open issue with the same branch-based title.
6. Score the repository using only evidence present in the codebase or repository metadata.
7. Summarize the strongest enterprise-ready signals and the biggest gaps.
8. If an open issue already exists for this branch title, use `update_issue` to replace its body with the latest score report.
9. If no matching open issue exists, use `create_issue` to create one for this branch.

## Safe Outputs

- Use `create_issue` when there is no existing open report issue for the branch.
- Use `update_issue` when an open issue already exists for the same branch title.
- Keep the issue title branch-based so later runs can update the same issue.
