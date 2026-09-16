# Token usage and practical improvement

The user wants both recorded Token usage and help improving everyday AI collaboration. README clarity means ordered, complete explanations with visible screenshots. Author posting drafts belong outside the product repository; the requested author relay link stays in its own section.

## Implementation

- Parse explicit per-response usage and legacy cumulative snapshots from supported logs. Store whitelisted usage events in the existing messages table without a schema migration; exclude them from conversational analytics and model packets.
- Add a Token usage page with input/output and subset counters, month/model/thread views, coverage and aggregate-only JSON download. Missing data remains unknown. Legacy snapshots are separate reference data, never billing totals.
- Add an improvement workspace with evidence-based suggestions, an editable task brief and a browser-local improvement journal. Keep demo/live drafts separate. Users record success criteria and outcomes themselves; no inferred productivity score or cost estimate.
- Retain the zero-dependency local runtime, existing consent boundaries and read-only original histories. Use only synthetic development data.

## Verification

Unit tests cover usage parsing, deduplication, missing fields, filtering and export privacy. HTTP tests exercise import to storage to usage, demo isolation and exclusion from conversation evidence. Browser tests cover both pages, journal persistence and dataset isolation, editing/export, unknown-data states and responsive light/dark layouts. Run the existing core and browser regressions before publishing.
