# Synthetic examples

`normalized.jsonl` contains nine user messages, nine assistant messages and three tool-call records across three threads and three nonadjacent months. All content is synthetic; the tool events are fixture data, not commands that were executed. It produces a plan → execute → verify candidate with three supporting threads.

`project/AGENTS.md` intentionally contains potentially conflicting instructions for testing the audit. These are test data, not the working policy of this repository. `plan.md` is an intentionally bloated local-analytics plan with two purposeful safeguards that should remain protected.
