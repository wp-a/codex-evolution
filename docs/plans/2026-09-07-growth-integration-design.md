# Codex Evolution Growth Dossier Integration Design

## Goal

Make the previous `codex-evolution` application the canonical project and add the evidence-led growth dossier as a first-class, optional layer without mixing private history into the public demo.

## Chosen shape

The existing local server, SQLite snapshot, import adapters, evidence explorer, instruction audit, Skill Lab, prompt workbench, and export routes remain the product core. The growth dossier is computed from the same canonical natural-user-message records and is exposed as one optional `growth` object in analysis responses. The existing “成长报告” page and aggregate report exports consume that object; no second ingestion pipeline or second dashboard is introduced.

The dossier has one pooled early/middle/late comparison, seven requested signals, one six-row overlapping phase matrix, a small heuristic month timeline, a cautious three-part readout, an optional four-line protocol, and a keep/avoid first-principles audit. Short windows render a compact boundary message instead of invented estimates.

## Data and privacy boundaries

- The observation unit is a natural user message; rates are `hits / natural_messages` and carry denominators.
- Empty months are null/“无数据”; first and last months may be partial.
- The demo remains the ZIP’s independent synthetic dataset (3,086 messages / 132 threads). Personal-history measurements are not merged into demo rows or published as fixtures.
- Default exports remain aggregate-only. Evidence remains opt-in and source-linked in the existing explorer. No content hashes/SHA, composite score, fixed Gate, automatic edits, or model calls are added.

## Verification

Add focused analytics/report tests first, run them red, then implement the smallest green slice. Re-run the existing 59-test suite, package/install checks, and the existing browser smoke path. Browser checks must distinguish synthetic demo values from any user-approved aggregate calibration text.
