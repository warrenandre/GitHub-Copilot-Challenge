---
emoji: 🏢
name: Enterprise Branch Score
description: |
  This workflow reviews new branch pushes and produces an enterprise-readiness
  score for the codebase. It looks for tests, documentation, CI/CD,
  security/governance, developer experience, and operational readiness signals,
  then creates or updates a GitHub issue named after the branch with the latest
  score and summary.
on:
  push:
    tags-ignore:
      - '**'
  workflow_dispatch:
permissions:
  contents: read
  issues: read
  pull-requests: read
  copilot-requests: write
strict: true
network:
  allowed: [defaults, github]
tools:
  github:
    mode: gh-proxy
    toolsets: [default]
safe-outputs:
  mentions: false
  allowed-github-references: []
  max-bot-mentions: 1
  create-issue:
    labels: [report, enterprise-score]
    deduplicate-by-title: true
    max: 1
  update-issue:
    target: "*"
    body: true
    max: 1
---

# Enterprise Branch Score

Create an enterprise-readiness report for every non-default branch push and keep a single rolling issue per branch.

## What to include

- An overall enterprise-readiness score out of 100
- Evidence-based scoring for tests, documentation, CI/CD, security/governance, developer experience, and operations readiness
- A concise executive summary of the branch state
- Key strengths, important gaps, and exactly 3 highest-value next actions
- A compact evidence snapshot listing the files, directories, or workflow assets that drove the score

## Scoring model

- Testing and quality gates: 25 points
  Look for automated tests, test directories, linting, formatting, type checking, coverage signals, or similar quality controls.
- Documentation: 15 points
  Look for a useful README, setup documentation, architecture notes, contribution guidance, ADRs, or operational documentation.
- CI/CD automation: 20 points
  Look for GitHub Actions, other pipeline definitions, build validation, deployment automation, release workflows, or environment promotion signals.
- Security and governance: 15 points
  Look for SECURITY guidance, CODEOWNERS, dependency update automation, license files, policy docs, secrets handling guidance, or other governance controls.
- Developer experience: 10 points
  Look for reproducible setup, pinned toolchains, local run instructions, task runners, dev containers, or consistent scaffolding.
- Operations and production readiness: 15 points
  Look for infrastructure as code, deployment manifests, environment configuration strategy, observability hooks, health checks, migration guidance, backup or recovery guidance, or release/versioning signals.

## Style

- Be concise, factual, and useful
- Keep the summary readable for engineering leads and maintainers
- Do not invent signals that are not present in the repository
- If evidence is weak or incomplete, say so explicitly

## Report Format

Write the issue body in GitHub-flavored markdown with this structure.

`<!-- enterprise-branch-score -->`

### Overall Score
- Show the score as `NN/100`.
- Give a short executive summary in 1 to 2 sentences.

### Category Breakdown
- One bullet per category with the category score, the strongest evidence found, and the biggest missing signal.

### Strengths
- 2 to 4 concise bullets.

### Gaps
- 2 to 5 concise bullets.

### Top Actions
1. First highest-value action.
2. Second highest-value action.
3. Third highest-value action.

### Evidence Snapshot
- List the most relevant files, directories, or workflow assets used in the assessment.

<details><summary>Scoring Notes</summary>

- Add any nuanced caveats, ambiguous findings, or partial signals here.

</details>

## Process

1. Determine the pushed branch name and the repository default branch.
2. If the event is not a branch push, or the branch is the default branch, or the branch matches obvious automation branches such as `dependabot/*`, `gh-readonly-queue/*`, or `copilot/*`, call `noop` with a short reason.
3. Inspect the checked-out repository contents first. Use GitHub reads only when needed for metadata or to find an existing issue.
4. Score the branch using only evidence found in the repository.
5. Compute the category scores and overall score, then explain the result with concise evidence.
6. Identify the strongest enterprise-ready signals, the most important gaps, and exactly 3 highest-value next actions.
7. Search open issues for one whose title exactly matches the branch name.
8. If a matching open issue exists, use `update_issue` to replace its body with the latest report.
9. If no matching open issue exists, use `create_issue` to create one whose title is exactly the branch name.
10. Never create more than one issue for the same branch in a single run.
11. If the branch has too little material to score meaningfully, still produce a report, but make the uncertainty explicit.

## Safe Outputs

- Use `update_issue` when an open issue already exists for the current branch.
- Use `create_issue` when no matching open issue exists.
- Use `noop` only when the branch should be intentionally skipped.