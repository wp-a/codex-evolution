# Growth Dossier Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the requested evidence-led growth dossier to the existing Codex Evolution application while keeping one data pipeline and explicit privacy boundaries.

**Architecture:** Extend `codex_evolution.analytics.analyze()` with a small optional `growth` object built from its existing canonical natural-message rows. Extend `reports.py` and the existing “成长报告” view to render the object; keep evidence, audit, Skill Lab, and server routes from the ZIP unchanged unless a regression requires a narrow compatibility patch.

**Tech Stack:** Python 3.10+ standard library, SQLite snapshot, vanilla HTML/CSS/JavaScript, `unittest`.

---

### Task 1: Lock the growth contract with tests

**Files:**
- Modify: `tests/test_analytics.py`
- Modify: `tests/test_cli.py` or add `tests/test_growth.py`
- Modify: `tests/test_server.py` only if the JSON route needs an assertion

**Step 1: Write the failing test**

Add a compact fixture spanning three or more months and assert: seven signal labels/order, pooled denominators, endpoint length/short-prompt signals, six phase rows, `heuristic` evolution markers, empty strengths, optional protocol, and audit keep/avoid entries.

**Step 2: Run the focused test to verify it fails**

Run: `python3 -m unittest tests.test_growth -v`

Expected: FAIL because `analyze()` does not yet expose `growth`.

**Step 3: Commit**

```bash
git add tests/test_growth.py
git commit -m "test: define growth dossier contract"
```

### Task 2: Implement the minimal analytics extension

**Files:**
- Modify: `codex_evolution/analytics.py`
- Modify: `codex_evolution/rules.py` only if a named growth pattern cannot reuse the existing dictionary

**Step 1: Implement**

Add explicit message-level growth patterns, pooled three-period summaries, endpoint signals, six-row phase cells, at most six heuristic anchors, cautious readout, optional protocol, and keep/avoid audit. Use the already prepared `monthly` rows and natural records; do not add a second normalization or hash layer.

**Step 2: Run the focused test**

Run: `python3 -m unittest tests.test_growth -v`

Expected: PASS.

**Step 3: Run the existing analytics tests**

Run: `python3 -m unittest tests.test_analytics -v`

Expected: all existing tests pass.

### Task 3: Extend aggregate report exports

**Files:**
- Modify: `codex_evolution/reports.py`
- Modify: `tests/test_analytics.py` or add `tests/test_reports_growth.py`

**Step 1: Write the failing report assertions**

Assert public JSON includes growth aggregates but no raw text/path/thread IDs; Markdown and standalone HTML contain the change ledger, phase matrix, protocol, and first-principles boundary.

**Step 2: Run focused tests to verify red**

Run: `python3 -m unittest tests.test_reports_growth -v`

Expected: FAIL because reports currently omit growth.

**Step 3: Implement and run green**

Keep the public allowlist aggregate-only and render zero denominators as unavailable. Run the focused tests again.

### Task 4: Add the growth dossier to the existing web report page

**Files:**
- Modify: `codex_evolution/web/app.js`
- Modify: `codex_evolution/web/styles.css` only for the new compact grid/timeline styles
- Modify: `tests/test_server.py` or browser smoke assertions if needed

**Step 1: Write the failing UI contract assertion**

Assert the rendered report page contains the seven labels, six phase labels, heuristic marker, optional protocol copy, and a compact-window empty state when the analysis has fewer than three active months.

**Step 2: Run the focused test to verify red**

Run: `python3 -m unittest tests.test_web_growth -v`

Expected: FAIL because the page has no growth section.

**Step 3: Implement and run green**

Reuse existing filters, evidence modal, theme, keyboard behavior, and export actions. Do not add another navigation stack or a fixed approval gate.

### Task 5: Documentation and release checks

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/METHODOLOGY.md`, `docs/QA.md`, `docs/ROADMAP.md`

**Step 1: Document the new contract**

Explain pooled natural-message rates, endpoint metrics, overlap, heuristic limits, synthetic/demo separation, and the risk-triggered protocol.

**Step 2: Run full verification**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile codex_evolution/*.py
node --check codex_evolution/web/app.js
python3 -m build --wheel --no-isolation  # if the local build tool is available
```

Expected: all tests and syntax/build checks pass; report any unavailable optional command instead of claiming it ran.

**Step 3: Commit the integrated slice**

```bash
git add codex_evolution tests docs README.md README.zh-CN.md
git commit -m "feat: add evidence-led growth dossier"
```

### Completion record — 2026-09-16

Completed the existing integration slice in place, preserving the unfinished analytics work. The final contract uses neutral 前期/中期/后期 labels, retains empty calendar months in the phase matrix, exposes numerator/denominator counts, and declines to name a phase focus when no phrase matches. The continuation fixture's incorrect 75% expectation was corrected to its actual 2/4 = 50%.

The existing report page and aggregate Markdown/HTML/JSON exports now consume the dossier. Documentation and package version are updated to 0.1.1. Verified 80 core tests, direct-localhost Chrome smoke, responsive report layouts, standalone export, and isolated wheel installation; see `docs/QA.md` for actual environments and limits. Changes remain available for local review; no commit, remote publication or personal-history import was performed in this continuation.
