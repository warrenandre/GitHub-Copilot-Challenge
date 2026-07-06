---
description: |
  This workflow creates repository enterprise-readiness score reports. It
  evaluates the codebase for documentation, testing, CI/CD, and exception
  handling, then publishes a scored summary as a GitHub issue.

on:
  workflow_dispatch:
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
- A category breakdown covering documentation, testing, CI/CD, and exception handling
- The strongest signals that the repository is enterprise-ready
- The biggest gaps preventing the repository from being enterprise-ready
- Exactly 3 high-value recommendations for improving the score
- A compact evidence snapshot listing the files, directories, workflows, or configuration signals used in the assessment

## Scoring model

- Documentation: 25 points
  Look for a useful README, docstrings on classes and methods, inline comments explaining intent, setup instructions, architecture notes, or contribution guidance.
- Testing: 30 points
  Look for automated tests, test directories, unit tests, integration tests, edge case coverage, test structure, or test runner configuration.
- CI/CD: 20 points
  Look for CI/CD pipeline definitions, automated linting, test execution on push, build validation, deployment automation, or environment promotion signals.
- Exception Handling: 25 points
  Look for try-except blocks, meaningful error messages, graceful fallbacks, input validation, defensive coding, custom exception classes, or error logging.

## Report format

Use GitHub-flavored markdown and keep the visible content concise.

### Overall Score
- Show the score as `NN/100`.
- Give a short executive summary in 1 to 2 sentences.

### Category Breakdown
- One bullet per category with score, strongest evidence, and biggest missing signal.

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
4. Study the repository structure, documentation, workflows, and configuration files.
5. Use GitHub reads when needed to find an existing open issue with the same branch-based title.
6. Score the repository using only evidence present in the codebase or repository metadata.
7. Summarize the strongest enterprise-ready signals and the biggest gaps.
8. If an open issue already exists for this branch title, use `update_issue` to replace its body with the latest score report.
9. If no matching open issue exists, use `create_issue` to create one for this branch.

## Safe Outputs

- Use `create_issue` when there is no existing open report issue for the branch.
- Use `update_issue` when an open issue already exists for the same branch title.
- Keep the issue title branch-based so later runs can update the same issue.
