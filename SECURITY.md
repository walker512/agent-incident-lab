# Security and privacy

## Boundary

This application treats transcripts as untrusted data. It never evaluates shell commands, JavaScript, tool arguments, or links contained in a transcript. The server reads no session directories, logs no request bodies, binds only `127.0.0.1`, validates Host/Origin, rejects cross-site requests, and accepts JSON POST bodies only. No external fonts, analytics, model APIs or remote scripts are loaded.

The browser sends selected content to your local Python process. Memory, browser devtools, local extensions, a compromised OS, swap and crash dumps are outside this boundary. “Local” is not a guarantee against a malicious local user or extension. Do not proxy or expose the server. The browser retains selected text only for the lifetime of the current page; no localStorage persistence is implemented.

## Export policy

Export builds new JSONL using a closed set of event/content discriminators, public tool categories, failure booleans, and zero/nonzero exit classes. Original prose, filenames, URLs, timestamps, commands, inputs, outputs, unknown keys, and original identifiers are not copied. Other tool names and identifiers are assigned ordinal labels. Source line numbers, record ordering, workflow categories, counts and failure structure remain visible and can be sensitive. Review the exact preview. There is no automatic publishing or sending.

This is not cryptographic anonymization, reversible pseudonymization, raw-log redaction, or a full semantic reproduction. The allowlist deliberately destroys content. An equivalence check covers a structural diagnostic signature only; its scope is documented in README. Unknown/malformed inputs can lose diagnostic detail. A false projection check is surfaced; verify before calling it an equivalent case.

Report JSON contains a SHA-256 of the original input for local identity checks. This can identify a known source via dictionary comparison. Bundles do not include that original hash; they include a hash of their projected transcript. CLI `--out` writes readable files with your OS defaults; choose an appropriate private destination.

## Bounds

Server request size: 16 MiB, per-record JSONL size: 2 MiB, 100,000 physical lines. The server admits up to four concurrent connections with 15-second socket timeouts; this is a resource bound, not a claim of denial-of-service resistance. The UI file picker uses a 10 MiB limit to leave room for JSON escaping. This is a local utility, not a hardened multi-user upload service. Duplicate JSON keys and non-finite numbers are rejected. Excessive JSON nesting is handled as invalid input.

If you discover a vulnerability, do not publish private raw transcripts in an issue. Describe it with a synthetic or allowlist-projected case. There is no external security inbox configured in this unreleased source tree.

## Imported verification cases

The verifier checks local consistency, not whether the supplied transcript went through the allowlist exporter. An imported case can contain raw content. `bundleChecksPassed` is not a privacy verdict or authenticity proof. Source-line mapping is checked for shape only; version differences are flagged, and the exporter’s projection claim is checked for internal consistency, not authenticated against an absent original source. The legacy `verified` field remains structural signature match only.
