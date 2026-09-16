# Reproducible measurements, not inferred ability

Schema: `1.0`. Rule set: `2026.09-v1`. The complete dictionaries are in `codex_evolution/rules.py`; the algorithm is in `analytics.py`.

## Observation unit and denominator

The observation unit is a supported, canonical **natural user message**. Blank messages and known injected context wrappers are excluded from this denominator. Assistant messages and supported tool-call records remain available as thread context but do not enter prompt-word rates. The injection detector uses explicit prefixes, not a universal classifier, and can misclassify a manually pasted wrapper. Unicode length means Python code-point count after trimming, not tokens, words, grapheme clusters, or display width.

For word group `w` and month `m`:

```text
hits(w,m) = number of natural user messages matching at least one regex in group w
rate(w,m) = 100 × hits(w,m) / natural_user_messages(m)
```

A message containing “继续” five times contributes **one** hit to that group. Multiple word groups and stage groups can match the same message; columns need not sum to 100%. Counts and denominators are returned alongside percentages. Rates are rounded to two decimal places; the UI may show integer cell labels or one decimal place.

Monthly counts of threads are actual distinct thread IDs among natural messages in that month. The all-period distinct thread count is not the sum of monthly thread counts. Tool-event counts are supported call records, not completed commands or success outcomes.

## Duplicates and missing data

Within a rollout file, when `event_msg.user_message` exists, that adapter prefers those user events over user `response_item` messages. This avoids mirrored model inputs but can undercount mixed-version files where the latter contain additional genuine user messages. This is an explicit adapter limitation, not a full lossless decoder.

Across sources/channels, records with identical thread, role, text and tool are mirror-matched one-to-one within two seconds. Repeated identical prompts in the same stream are retained. No content hash or fuzzy similarity is required. Different exported copies can still be ambiguous. Re-import replaces the snapshot of each successfully parsed source; it does not delete sources absent from a later import selection.

Empty calendar months within the selected range have zero messages and **null rates**. Missing history is not evidence of zero usage. First/last dates reflect observed records, not guaranteed complete calendar months; in the synthetic demo September ends on the fifth. The application does not extrapolate that month or compare raw partial-month volume as growth.

Timestamps are converted to the chosen timezone before assigning dates and months. Naive ISO timestamps are interpreted as UTC. Invalid timestamps are excluded and counted. The current synthetic sample is frozen in `demo.py`, with 3,086 natural messages and 132 threads; it is not the original user's reported history.

## Early/late comparisons

With `M` included calendar months, compare the first and last `max(1, floor(M/3))` months, only when `M >= 2`. Calculate each phase by **summing hits and denominators**; do not average monthly percentages. Differences use **percentage points (pp)**, not relative percent growth. Edge phases with fewer than 30 messages are marked small-sample; this threshold is a UI caution, not a confidence interval. There is no significance test, causal claim, or adjustment for changing task mix.

## Growth dossier (v0.1.1)

The optional `growth` object is calculated from the same canonical natural messages and filters as the overview. It adds no import pipeline, classifier or model request. Its small literal Chinese phrase dictionaries are declared as `GROWTH_TERM_PATTERNS` and `GROWTH_PHASE_PATTERNS` in `analytics.py`; these are distinct from the overview's multilingual regex groups. Identically named signals can therefore have different rates across those two views. Literal substring matching can, for example, count “请求” under “请”; these are surface observations, not intent detection.

With at least three active months, split those months chronologically into three balanced groups labelled early, middle and late. Any remainder goes to earlier groups. Each group exposes its observed month list and natural-message denominator. Pool message hits and denominators; never average monthly percentages. These groups describe positions within the selected window, not detected developmental stages.

The seven ledger rows, in order, are “请/请你”, “帮我”, “继续”, median natural-message length, the share of prompts of at most 20 Unicode code points, “验证/证据”, and “确认”. Phrase rows compare the first and last pooled groups. The length and short-prompt rows instead compare the first and last active month, with those month names and sample counts. Rate differences are percentage points; length differences are Unicode code points. The continuation peak uses the earliest month in a tie. No month is extrapolated.

The six-row phase matrix covers all selected calendar months. Cells carry hits, denominators and nullable rates; empty months are unavailable, not 0%. Groups may overlap. Up to six evenly selected active months provide explicitly `heuristic` observation anchors. A month with no matching phrases has no focus signal. Anchors neither detect stages nor prove task completion, first adoption, skills or personal growth. The readout separates observations from cautious interpretation, leaves inferred strengths empty, and offers a four-line protocol only as optional guidance for longer tasks.

Fewer than three active months produces an unavailable comparison with a reason and no ledger signals; report views use a compact message. The JSON contract can still carry the available monthly matrix. Default Markdown, HTML and JSON exports contain aggregates only. Growth fields use a nested allowlist so additional evidence text, source paths or thread IDs do not become public merely by being attached to the internal object. This is not a general secret detector, and behavioral aggregates still require care when sharing. Demo values remain the independent 3,086-message synthetic dataset; personal histories are not used as fixtures.

## Task signals, timeline and skill candidates

The six task-stage groups and monthly topic labels are regex heuristics. A monthly topic is the group with most matching messages; ties use dictionary order, and one keyword can contribute to more than one topic. This is not a model-written account of a user's actual career development.

Skill mining assigns one primary request-stage per natural message using the declared priority: reflection, verification, planning, execution, goal, iteration. Adjacent repeats are collapsed within a thread. Three consecutive distinct stages containing verification form a candidate, supported by at least three independent threads. The top eight patterns are returned with up to three example threads. Missing/unclassified messages are skipped, so the stages are not necessarily adjacent original messages.

A candidate is a request-pattern proposal, **not** proof the assistant followed it, the task succeeded, or the method is stable. Draft triggers and boundaries must be reviewed before adopting the skill. No effectiveness ranking is presented.

## Audit interpretation and model coverage

Rule audit findings are review questions. A broad confirmation requirement may be intentional. Same-directory nonempty override files shadow AGENTS; ancestor/descendant scopes may overlap, sibling scopes do not automatically overlap; skills are conditional. Global files, configuration-defined fallback names, actual runtime activation and policy are not silently reconstructed.

Model interpretation is a separate optional layer. Retrospectives receive aggregates and at most 36 selected excerpts; file/plan review receives a bounded preview packet. Statistics cover all imported supported records, but semantic analysis does not claim to read every conversation. Unsupported model source IDs are removed and confidence lowered; even valid IDs do not guarantee a correct interpretation.

Recommendations are qualitative, not evidence that the user lacks a skill. There are no IQ, personality, maturity, productivity or task-success scores.
