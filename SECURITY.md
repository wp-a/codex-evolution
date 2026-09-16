# Privacy and security

## Trust boundary

This is a **single-user, trusted-local-machine** application. Bind is restricted to `127.0.0.1`; do not proxy, tunnel or expose it to the public internet. It does not isolate one local OS user/process from another, provide a production authentication system, or protect against a compromised computer/browser extension.

The application checks Host, rejects foreign Origin, requires a random per-run token for API calls, serves an asset allowlist, avoids query-string request logs, and sends no-store/CSP/referrer headers. These are ordinary controls for local file access, not a reason to expose the app publicly.

## Local data

Original Codex histories, selected instruction files and metadata databases are read-only. Imported message text, source identifiers and metadata are stored as **plaintext** in the app-owned SQLite database. On systems supporting Unix permissions the file is set to mode 0600. This is not encryption. Use OS full-disk encryption and appropriate backups where required.

The “delete imported records” operation deletes and vacuums this application database. It does not delete Codex history, exported reports, OS backups, snapshots or forensic SSD remnants. No secure-erasure guarantee is made.

No analytics, tracking, CDN, remote fonts, remote charts or model calls occur during default local workflows. The packaged demo is synthetic. The only normal network request outside localhost is the explicit optional model interpretation.

## Optional external processing

Preview every evidence packet before sending or copying it to Codex. Common-key/email/home-path redaction is best effort and misses arbitrary secrets, private code, organization identifiers and other sensitive information. File aliases reduce path leakage but do not make the text anonymous. Materials manually edited after redaction are sent as edited when explicitly approved.

The API request is tool-free and uses `store: false`; that parameter does not override all provider processing/retention terms. API inference can be billed. No API key is embedded in HTML, sent to the browser, written into project files, or copied from Codex `auth.json`.

## Changes and exports

Audit findings and diffs are proposals only. Explicit approvals, protected actions and integrity checks are not automatically weakened. A permission-expansion flag is a review warning, never an authorization grant. Workflow downloads are uninstalled drafts; manually installing a skill can affect future agent behavior and requires review.

Aggregate report exports exclude raw text, project names and source paths by an allowlist. Aggregate usage itself can still be sensitive. Audit exports, model handoff packets and cited evidence can contain selected original text; do not publish them as if they were anonymized.

Treat imported text as untrusted. The web UI escapes dynamic text and the application does not execute transcripts, generated code, model-suggested commands or skills. Optional model output remains fallible even when it cites a valid source.

## Reporting

Before publishing this repository, the maintainer should enable GitHub private vulnerability reporting or add a private contact. Do not post credentials or personal histories in a public issue. Until a private channel is available, report only a sanitized minimal reproduction, omitting exploitable/private details from public discussions. No private disclosure endpoint is falsely claimed by this source archive.
