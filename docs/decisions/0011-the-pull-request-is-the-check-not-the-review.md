# 0011. Treat the pull request as the check, not the review — and wait for it

- **Status:** accepted
- **Date:** 2026-09-11
- **Where it lives:** `AGENTS.md`, `.github/workflows/check.yml`

## The decision

The pull request exists for one reason: **CI runs the checks somewhere other than the
machine that wrote the change.** Never merge before the checks report:

```bash
gh pr checks --watch && gh pr merge --merge --delete-branch
```

One branch, one subject, deleted on merge. Design arguments go in `docs/`, not in a PR
body.

## Why

There is one author and there will not be a reviewer, so the review framing was never the
point and pretending otherwise made the flow look ceremonial. What CI actually provides is
the only thing `make check` locally cannot: the `parity` job regenerates the OpenSCAD
reference from scratch on a clean runner, rather than reading whatever is already sitting
in `exports/`. Everything this project claims about its geometry rests on that.

The measurement that prompted it, across the first 33 merged PRs: median time from opening
to merge **about two minutes**, median CI duration **103 seconds**. Roughly half were
merged while the answer was still being computed. PR #22 was merged **eleven seconds**
after it was opened, its run failed, and `main` stayed red until the next change happened
to repair it.

## What was rejected

- **Dropping the PR and pushing straight to `main`.** Consistent, and it gives up the
  clean-clone parity run on the change itself.
- **Required status checks.** Not available on a private repository without a paid plan.
  If the repo is ever made public, turn them on for `python` and `parity` and delete the
  paragraph in `AGENTS.md` that says this.

## What it costs

About two minutes per change, and the gate is a habit rather than an enforced rule.
