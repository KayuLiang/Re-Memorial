# Local Repository Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate the local ReMemorial repositories around `E:\Re-Memorial` and prepare its `main` branch as a verified local `0.0.0` release candidate without pushing or tagging.

**Architecture:** Treat `E:\RenpyProject\ReMemorial` as the source project and `E:\Re-Memorial` as the only Git repository. First preserve and commit the coherent opening/CRT work already present, then synchronize intended source files, add an executable version contract, and document the local version workflow.

**Tech Stack:** Git, PowerShell, Python `unittest`, Ren'Py 8.5.3

---

### Task 1: Inventory and Preserve Existing Work

**Files:**
- Inspect: `E:\RenpyProject\ReMemorial`
- Inspect: `E:\Re-Memorial`
- Commit existing modified opening/CRT files and their design/plan documents

- [ ] **Step 1: Compare source and repository trees**

Run a PowerShell hash comparison over both trees while excluding `.git`, `game/cache`, `game/saves`, compiled scripts, logs, errors, and tracebacks.

Expected: a concrete list of source-only, repository-only, and content-different files.

- [ ] **Step 2: Run the current automated tests**

Run:

```powershell
python -m unittest discover -s tools -p "test_*.py" -v
```

Expected: all existing tests pass before committing the preserved work.

- [ ] **Step 3: Review and commit the coherent opening/CRT changes**

Run:

```powershell
git diff --check
git diff --stat
git add -- game/crt_effect.rpy game/images/effects/crt_scanlines.png game/opening_sequence.rpy game/screens_opening_system.rpy tools/generate_crt_assets.py tools/test_opening_contracts.py docs/superpowers/plans/2026-06-20-opening-dimming-crt-paced-audio.md docs/superpowers/plans/2026-06-20-opening-interaction-fixes.md docs/superpowers/plans/2026-06-21-crt-scanline-clarity.md docs/superpowers/specs/2026-06-20-opening-dimming-crt-paced-audio-design.md docs/superpowers/specs/2026-06-21-crt-scanline-clarity-design.md
git commit -m "fix: refine opening interaction and CRT presentation"
```

Expected: one local commit preserving the current coherent work.

### Task 2: Synchronize the Authoritative Development Project

**Files:**
- Source: `E:\RenpyProject\ReMemorial`
- Destination: `E:\Re-Memorial`

- [ ] **Step 1: Copy only intended source and asset differences**

Copy files identified in Task 1 from the development project into the Git repository. Do not copy `.git`, caches, saves, compiled files, logs, errors, tracebacks, or build output.

- [ ] **Step 2: Inspect all resulting changes**

Run:

```powershell
git status --short
git diff --check
git diff --stat
```

Expected: only intentional project source, asset, or documentation differences remain.

- [ ] **Step 3: Run tests and commit synchronized content**

Run:

```powershell
python -m unittest discover -s tools -p "test_*.py" -v
git add -- <reviewed-files>
git commit -m "chore: synchronize active Ren'Py project"
```

Expected: tests pass and synchronized content is preserved in a focused local commit. Skip the commit if no differences remain.

### Task 3: Establish the `0.0.0` Version Contract

**Files:**
- Modify: `E:\Re-Memorial\tools\test_opening_contracts.py`
- Modify: `E:\Re-Memorial\game\options.rpy`

- [ ] **Step 1: Add a failing version contract test**

Add a test that reads `game/options.rpy` and asserts:

```python
self.assertRegex(source, r'(?m)^define config\.version = "0\.0\.0"$')
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```powershell
python -m unittest tools.test_opening_contracts.ProjectVersionContractTests -v
```

Expected: failure because the current value is `"1.0"`.

- [ ] **Step 3: Set the Ren'Py version**

Change:

```renpy
define config.version = "0.0.0"
```

- [ ] **Step 4: Run the test and verify GREEN**

Run:

```powershell
python -m unittest tools.test_opening_contracts.ProjectVersionContractTests -v
```

Expected: pass.

### Task 4: Add Repository Hygiene and Version Documentation

**Files:**
- Modify: `E:\Re-Memorial\.gitignore`
- Create: `E:\Re-Memorial\.gitattributes`
- Create: `E:\Re-Memorial\docs\VERSIONING.md`

- [ ] **Step 1: Extend generated-file exclusions**

Ensure `.gitignore` excludes Ren'Py launcher/build outputs including `game/bytecode.rpyb`, root build distribution directories, and common generated diagnostic files.

- [ ] **Step 2: Normalize repository line endings**

Create `.gitattributes` with LF normalization for text and explicit binary treatment for image, audio, font, and archive formats.

- [ ] **Step 3: Document the workflow**

Document:

- active project: `E:\RenpyProject\ReMemorial`;
- Git repository: `E:\Re-Memorial`;
- retired C-drive copy must not be committed or pushed;
- `main` is the stable local branch;
- version values use `0.0.0`, tags use `v0.0.0`;
- published tags are immutable;
- release order is test, lint, commit, push, tag, GitHub Release.

- [ ] **Step 4: Verify and commit metadata**

Run:

```powershell
git diff --check
python -m unittest discover -s tools -p "test_*.py" -v
git add -- .gitignore .gitattributes docs/VERSIONING.md game/options.rpy tools/test_opening_contracts.py
git commit -m "chore: establish 0.0.0 version policy"
```

Expected: tests pass and one focused local version-policy commit is created.

### Task 5: Final Verification

**Files:**
- Verify: `E:\Re-Memorial`

- [ ] **Step 1: Run the complete Python test suite**

Run:

```powershell
python -m unittest discover -s tools -p "test_*.py" -v
```

Expected: zero failures and zero errors.

- [ ] **Step 2: Run Ren'Py lint**

Run:

```powershell
E:\renpy-8.5.3-sdk\renpy.exe E:\Re-Memorial lint
```

Expected: lint completes without script errors.

- [ ] **Step 3: Confirm repository state and release boundaries**

Run:

```powershell
git status --short --branch
git log --oneline --decorate -12
git tag --list
git remote -v
git diff HEAD
```

Expected:

- working tree is clean;
- `main` contains the local consolidation commits;
- no `v0.0.0` tag exists yet;
- no push or GitHub Release has been made;
- `config.version` is `0.0.0`.

