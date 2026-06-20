---
emoji: 🏢
name: Enterprise Branch Score
description: Score non-default branches for enterprise readiness and upsert a branch-named issue with the latest summary.
on:
  push:
    tags-ignore:
      - '**'
permissions:
  contents: read
  issues: read
strict: true
network:
  allowed: [defaults, github]
tools:
  github:
    mode: gh-proxy
    toolsets: [default]
safe-outputs:
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

Evaluate the pushed branch for enterprise readiness and publish the latest score as a single branch-specific issue.

1. Determine the current branch name and the repository default branch.
2. If the push is not for a branch, or the branch is the default branch, or the branch matches obvious automation branches such as `dependabot/*` or `gh-readonly-queue/*`, call `noop` with a short explanation.
3. Inspect the checked-out repository contents first. Use GitHub reads only when you need repository metadata or existing issues.
4. Score the branch using this 100-point rubric. Use evidence from the repository only. Do not invent missing signals.

### Scoring Rubric

- Testing and quality gates: 25 points
Look for automated tests, test directories, coverage clues, linting, formatting, static analysis, or similar quality controls.

- Documentation: 15 points
Look for a useful README, architecture or setup docs, contribution guidance, ADRs, or operational documentation.

- CI/CD automation: 20 points
Look for GitHub Actions, other pipeline definitions, build validation, deployment automation, release workflows, or environment promotion signals.

- Security and governance: 15 points
Look for SECURITY guidance, CODEOWNERS, dependency update automation, license files, policy docs, or other governance/security controls visible from the repo.

- Developer experience: 10 points
Look for reproducible setup, pinned toolchains, local run instructions, dev containers, task runners, or consistent project scaffolding.

- Operations and production readiness: 15 points
Look for infrastructure as code, deployment manifests, observability hooks, configuration strategy, health checks, backup or migration guidance, or release/versioning signals.

5. Produce an evidence-based overall score out of 100, plus a short rationale for each category.
6. Identify the top strengths, the highest-risk gaps, and the top 3 actions that would most improve enterprise readiness.
7. The issue title must be exactly the branch name.
8. Before writing, search open issues for one whose title exactly matches the branch name and whose body already contains the marker `<!-- enterprise-branch-score:{branch-name} -->`.
9. If that issue exists, use `update_issue` to replace its body with the new report.
10. If no matching issue exists, use `create_issue` to create one with the exact branch name as the title.
11. Never create more than one issue for the branch in a single run.

## Report Format

Write the issue body in GitHub-flavored markdown using this structure:

`<!-- enterprise-branch-score:{branch-name} -->`

`### Overall Score`
- Show the score as `NN/100`.
- Give a 1-2 sentence executive summary.

`### Category Breakdown`
- One bullet per category with score, evidence, and notable gap.

`### Enterprise Readiness Summary`
- `Strengths:` 2-4 concise bullets.
- `Gaps:` 2-5 concise bullets.
- `Top actions:` exactly 3 numbered actions.

`### Evidence Snapshot`
- List the most relevant files, directories, or workflow assets used for the assessment.

## Safe Outputs

- Use `update_issue` when an open issue already exists for this branch.
- Use `create_issue` when no matching issue exists.
- Use `noop` only when the event should be intentionally skipped.