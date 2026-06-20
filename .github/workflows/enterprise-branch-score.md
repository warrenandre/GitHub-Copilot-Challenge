---
emoji: 🏢
name: Enterprise Branch Score
description: Score non-default branch pushes for enterprise readiness and upsert a branch-named issue with the latest report.
on:
  push:
    tags-ignore:
      - '**'
permissions:
  contents: read
  issues: read
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
    deduplicate-by-title: true
    max: 1
  update-issue:
    target: "*"
    body: true
    max: 1
---

# Enterprise Branch Score

## Task

Evaluate each pushed branch for enterprise readiness and publish one rolling report issue per branch.

1. Determine the pushed branch name and the repository default branch.
2. If the event is not a branch push, or the branch is the default branch, or the branch matches obvious automation branches such as `dependabot/*`, `gh-readonly-queue/*`, or `copilot/*`, call `noop` with a short reason.
3. Inspect the checked-out repository contents first. Use GitHub reads only when you need metadata or to find an existing issue.
4. Score the branch out of 100 using only evidence that is present in the repository.

### Scoring Rubric

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

5. Compute the category scores and overall score, then explain the result with concise evidence.
6. Identify the strongest enterprise-ready signals, the most important gaps, and exactly 3 highest-value next actions.
7. The issue title must be exactly the branch name.
8. Before writing anything, search open issues for one whose title exactly matches the branch name.
9. If an open issue with that exact title exists, use `update_issue` to replace its body with the latest report.
10. If no matching open issue exists, use `create_issue` to create one with the exact branch name as the title.
11. Never create more than one issue for the same branch in a single run.
12. If the branch has too little material to score meaningfully, still produce a report, but make the uncertainty explicit.

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

## Safe Outputs

- Use `update_issue` when an open issue already exists for the current branch.
- Use `create_issue` when no matching open issue exists.
- Use `noop` only when the branch should be intentionally skipped.