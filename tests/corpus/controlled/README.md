# Controlled Codex executions, 2026-11-16

These are structural projections of fresh Codex CLI 0.151.0 --json stdout on Windows with Python 3.11.9. They are NOT hand-authored event fixtures and NOT naturally occurring user incidents. CLI default model selection was used; the emitted diagnostics identified gpt-5.6-sol. The two successful controlled sessions used --ephemeral --ignore-user-config --skip-git-repo-check --approve-for-me; no sandbox bypass, credential copies, private session discovery or settings edits were used.

- codex-test-failure.projected.jsonl: attempted read-only run. Model text reported sandbox prevented command; no command events were emitted. This is a no-tool-activity/observability limitation case, NOT proof of a structured permission failure.
- codex-test-failure-retry.projected.jsonl: fixture test_example.py actually executed, assertion 4 != 5, exit 1. Call line 4, result line 5.
- codex-controlled-cases.projected.jsonl: one run with four separate commands, not four independent sessions/users: missing file (L4-5), invalid JSON (L6-7), Python subprocess timeout (L8-9), success control (L10-11). First three exit 1; last exit 0. Timeout was fixture-generated, not Codex tool-timeout semantics.

Projection removes prose, command strings, output, paths, account/thread IDs, usage; correlation IDs are renumbered and nonzero exits normalized to 1. It retains record order. Raw stdout and stderr stay local and must not be published; stderr contains user account metadata. The project cannot infer exception class from the public projection. Ground-truth labels come from this controlled experiment and local review, not from the parser.

Hashes are in capture_hashes.json (raw hashes refer to exact original PowerShell redirection bytes). Projections and original fixture programs may be incorporated into Agent Incident Lab under its MIT license by its owner. Do not assert multi-version or Claude compatibility, diagnostic precision/recall, user adoption, time saved or comprehensive security from these three sessions.
