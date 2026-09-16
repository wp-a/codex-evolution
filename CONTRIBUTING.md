# Contributing

Start from a reproducible user problem: a supported history shape that fails, a misleading metric, an audit false positive, a usability issue, or an accessibility problem. Keep the change small and include synthetic evidence.

Run `python3 -m unittest discover -s tests -v`. For frontend changes run the optional browser smoke suite and inspect the relevant page at a narrow width. A build step is not required. Do not add runtime dependencies or architecture merely to satisfy a style preference.

For adapters, include minimal events and expected counts, source positions, excluded records and duplicate behavior. For audits, include the quoted rule, scope, expected concern/protection and whether a proposed change affects permissions. Changes to measurement semantics must update `docs/METHODOLOGY.md` and the rule/schema version where appropriate.

Never commit real transcripts, secrets, local databases or confidential AGENTS files. Share-card examples and screenshots must use clearly labeled synthetic data. Do not relabel a model hypothesis as a measured result.

A useful pull request explains the problem, concrete changes, tests actually run, remaining uncertainty and privacy impact. Keep deliberate approval and integrity protections unless the task explicitly authorizes a specific reviewed change. No repeated hashes or broad checklist bureaucracy is required for routine development.
