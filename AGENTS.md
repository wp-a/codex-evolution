# Working on Codex Evolution

Build a small, real local application, not a mock UI. Read README.md and the relevant module before editing.

Use `python3 -m unittest discover -s tests -v` for core regression checks. Browser tests are optional development tooling; explain what was and was not tested.

Keep runtime dependencies at zero unless the requested feature provides a concrete reason to change that decision. Preserve aggregate-only report exports, explicit model consent, source references, and original-file read-only behavior.

Use synthetic fixtures. Never commit real histories, credentials, private instruction files or application databases. Do not weaken explicit user approvals to make an audit appear cleaner.

Proceed with requested, scoped implementation work; ask only when missing information materially blocks correctness or authorization. Finish with the actual change, validation results and remaining limitations. Do not claim a feature, test, deployment or API call succeeded without evidence.
