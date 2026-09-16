# Verification record — v0.1.1

## Public-release preparation — 2026-09-16

Prepared eight marketing PNGs, an editable HTML source, an offline gallery, Chinese/English README presentation, launch copy and release notes. All images use real product screens with synthetic data. Chrome rendered the eight artboards at their stated dimensions; the gallery loaded every image at 360, 768 and 1280px without document overflow or JavaScript errors. An independent visual review identified a cropped statistic in the overview composition; its final layout shows the complete screenshot beside explanatory text.

Reran all **80 core tests**, JavaScript/Python syntax and `git diff --check`. Built a wheel from a temporary source snapshot and installed it into an isolated Python 3.12 environment; the CLI version, packaged assets and standalone HTML report passed verification. The application runtime dependency list remains empty; Playwright is optional tooling for tests and image rendering.

Reviewed current files, previous local files and all supplied/screenshotted images for private data. Removed references to private usage aggregates and changed fixture assertions to check the synthetic sample directly. The public `main` starts from a clean snapshot with a GitHub noreply commit identity; previous local history is retained separately and is not part of the public branch. No personal histories, databases or credentials are included. Repository CI execution is recorded in GitHub Actions; the earlier local-only records below retain their original scope.

## Latest interface refinement — 2026-09-16

Added the default `#start` introduction, grouped Chinese navigation, a light macOS-inspired visual layer with saved theme choice, plain-language page descriptions, and native disclosures for report details/exports. The existing eight working routes and backend contracts remain available.

Verified **80 core tests**, JavaScript/Python syntax and `git diff --check`. The browser test first failed because the old application lacked `.start-page`, then passed with the implementation. Real Google Chrome on direct localhost verified first-use navigation, import and demo actions, light default, persisted dark theme after reload, report disclosure access, and the existing evidence/audit/Skill/prompt/export/import/delete flows. No JavaScript errors were recorded.

The introduction and report were additionally inspected in **both themes at 320, 360, 736, 1024 and 1512px** without document overflow. A targeted final check verified the full mobile dataset label, keyboard Enter activation of the export disclosure, its visible inset focus ring, and 25px desktop body inset. Tables retain local horizontal scrolling. Screenshots and `browser-results.json` / `visual-results.json` are in `docs/screenshots/`.

Only temporary synthetic datasets were used. No private history was imported and no model request was sent. Browser bridge mode remains optional; saved-theme reload is explicitly untested for its opaque-origin document. Source and wheel delivery files were refreshed locally; there was no remote publication.

## Growth integration verification

Date: 2026-09-16. Verified locally on macOS arm64. The previous v0.1.0 record remains below as historical evidence.

- **Core:** `python3 -m unittest discover -s tests -v` — **80 tests passed**, Python 3.14.3. This includes the original 59 tests, nine growth analytics tests, ten growth export tests and two existing UI source contracts. Behavioral browser checks supplement those source contracts. A pre-existing mock-HTTPError cleanup `ResourceWarning` appeared under Python 3.14; it did not fail a test.
- **Syntax:** `python3 -m py_compile codex_evolution/*.py`, `node --check codex_evolution/web/app.js`, and `git diff --check` passed.
- **Browser:** the optional smoke ran with Playwright on Python 3.12.14 against the installed Google Chrome binary and a real temporary localhost server/database, using the normal `direct-localhost` mode. No fetch bridge or CSP bypass was used. It verified seven signal rows and six phase rows, values/counts against the API, endpoint units, month evidence, optional protocol, filtered short-window exports, synthetic/imported data isolation, imported gap months, and all prior upload/audit/prompt/download/keyboard flows. **No JavaScript page errors.**
- **Layout:** growth report checks passed at 320, 360, 736, 1024 and 1512 CSS pixels; overview checks passed at 360, 768, 1024 and 1512. Scrollable tables remain intentional. Dark/light and mobile screenshots were inspected. Standalone HTML also passed those five growth widths and a separate 200% **CSS zoom** reflow check; this is not a browser-UI zoom or exhaustive accessibility claim.
- **Packaging:** built `codex_evolution-0.1.1-py3-none-any.whl` with `pip wheel --no-deps --no-build-isolation --no-index` using the available local setuptools. Installed it into a fresh Python 3.12 virtual environment without network or dependencies. Verified the `0.1.1` console version, four web assets, five prompt files, seven/six growth rows and an installed HTML report identical to the source-generated report. The optional `build` module was unavailable; the wheel used the existing pip build path.
- **Review:** an independent review exercised project/date/timezone-filtered HTTP analysis/export equality, null gap months, short windows, source omission and filtered evidence. The sidebar version mismatch it found was corrected.

The direct browser run exposed old string-expression waits incompatible with the page's strict CSP. The smoke now uses locator retry assertions; the application security policy was not changed. Its initial short-window fixture was corrected from July–September (three active months) to August–September (two).

Artifacts use only the independent synthetic demo or minimal synthetic test fixtures. This release did not import real personal history, run paid inference, publish a package, deploy publicly, or run remote CI. Native Safari/Windows and the full Python version matrix were not exercised.

The current browser results and new growth screenshots are in `docs/screenshots/`. Local delivery files are in ignored `dist/`: wheel, source archive and standalone demo reports. Run the source with `python3 -m codex_evolution demo --open`.

## Historical verification — v0.1.0

Date: 2026-09-06. This record describes checks actually performed on the delivered source, not an unexecuted release checklist.

## Executed

**Core:** `python -m unittest discover -s tests -v` — **59 tests passed** on Python 3.13.5/Linux. The tests include Codex-shaped and normalized synthetic fixtures, same-stream repeated prompts, cross-stream mirrors, re-import snapshots, read-only SQLite metadata enrichment, weighted percentages, timezone boundaries, null gap months, evidence references, scope-aware audits, preserved approvals/integrity checks, skill drafts, aggregate export privacy, CLI commands, real localhost HTTP, and mocked model request/error paths.

**Frontend syntax:** `node --check codex_evolution/web/app.js` — passed. Node is a developer check here, not an application runtime requirement.

**Browser integration:** `python tests/browser_smoke.py --bridge --browser /usr/bin/chromium` — passed against a real temporary Python backend and SQLite database. Verified rendered demo totals; heatmap evidence dialog; six sample instruction findings and two protected lines; four sample plan concerns; eight workflow candidates; editable skill/prompt dialogs; actual HTML and PNG downloads; a 36-reference preview; message search; June–August filter (1,660 synthetic messages); both themes; command palette; real fixture upload (nine natural user messages); null-month layout; deletion of the application copy. No JavaScript page errors were recorded. Root-page horizontal overflow checks passed at 360, 768, 1024 and 1512 CSS pixels. Individual chart containers may scroll horizontally by design.

The managed browser in the verification environment rejects direct navigation to localhost with `ERR_BLOCKED_BY_ADMINISTRATOR`. The explicit `--bridge` mode therefore renders the shipped HTML/CSS/JS assets and forwards browser fetch calls through Python to the **actual** local server. It does not use fake API responses or alter browser policies. This validates UI/data integration, not browser-network security enforcement; direct HTTP tests separately exercise Host, Origin, session-token checks and static-path restrictions.

Actual screenshots are under `docs/screenshots/`. They use synthetic data, not personal conversations or generated dashboard illustrations. `browser-results.json` contains the latest browser check results.

**Packaging:** built the wheel with `pip wheel . --no-deps --no-build-isolation`; installed it into a fresh virtual environment using `--no-index --no-deps`; checked the console entry point, packaged web assets, five prompt files, and a generated demo report (3,086 natural messages). No package was published.

## Reproduce

Core tests require only Python's standard library:

```bash
python3 -m unittest discover -s tests -v
```

Optional developer browser setup:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
python3 tests/browser_smoke.py
```

For an existing Chromium binary use `--browser /path/to/chromium`. Use `--bridge` only in environments where managed navigation prevents the normal localhost test, and retain that limitation in any report. The test starts an isolated temporary server/database and stops it afterward; it does not import your personal history. Screenshots default to the documentation folder; choose another destination with `--screenshots`.

## Not verified here

No paid live OpenAI model inference; no real user Codex history or current Codex installation compatibility run; no published GitHub repository or remote Actions run; no native macOS/Windows/Safari execution; no claim of exhaustive language-level instruction-conflict detection or measurable productivity gains. CI configuration includes Python 3.10–3.13 on Ubuntu, but configuration is not proof those remote jobs have run.

The demo is independently synthetic. Its 3,086 natural messages and 132 threads must not be represented as a real user's history.
