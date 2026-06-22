# Local Repository Consolidation Design

## Goal

Make `E:\Re-Memorial` the single authoritative local Git repository and prepare
its current `main` branch as the local `0.0.0` release candidate without
rewriting history, pushing, tagging, or deleting other working copies.

## Repository Roles

- `E:\RenpyProject\ReMemorial` remains the active Ren'Py development project.
- `E:\Re-Memorial` remains the only Git repository used for commits and future
  pushes.
- `C:\Users\19512\Documents\ReMemorial` is considered retired. It will not be
  merged, deleted, committed, or pushed during this work.

## Consolidation Strategy

Preserve the complete history of `E:\Re-Memorial`. Compare the active
development project with that repository, synchronize intended source and
asset changes into the Git repository, and exclude generated files, caches,
saves, compiled scripts, logs, errors, and tracebacks.

Existing uncommitted work will be reviewed and divided into focused local
commits where practical. No force operations, history squashing, remote
updates, tags, or GitHub Releases are in scope.

## Version Policy

Set Ren'Py's user-visible project version to `0.0.0`. The resulting verified
local `main` commit is the release candidate for the future `v0.0.0` tag.
The next release will use `0.0.1`.

Version tags use the `vMAJOR.MINOR.PATCH` form, while `config.version` uses the
plain `MAJOR.MINOR.PATCH` form.

## Repository Hygiene

The repository will contain a short version-management document describing:

- the authoritative development and Git directories;
- the branch and release workflow;
- version-number and tag conventions;
- the rule that published tags are immutable.

The ignore rules will be checked against Ren'Py-generated artifacts and
extended only where the current rules leave generated files unprotected.

## Verification

Before the consolidation is considered complete:

1. Relevant project tests must pass.
2. Ren'Py lint must complete successfully.
3. `config.version` must report `0.0.0`.
4. The local Git history and working tree must be inspected.
5. No remote push, version tag, GitHub Release, or deletion of the retired
   C-drive repository may have occurred.

