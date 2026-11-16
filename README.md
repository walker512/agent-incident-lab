# Agent Incident Lab

**A failed agent run deserves evidence, not a dashboard full of zeroes.**

Inspect native Claude Code and Codex JSONL locally. Find missing results, ambiguous call IDs, explicit tool failures, and parser blind spots. Turn the relevant source lines into a content-stripped parser case that another maintainer can verify offline.

> This is an incident inspection and parser reproduction tool. It does **not** execute commands, replay a model, reproduce the original environment, or judge task success.

## See the point in 60 seconds

Requires Python 3.10 or newer. Download and extract this repository, then run from its root:

```sh
python -m incidentlab serve
```

Open **http://127.0.0.1:8765**. Windows users can also double-click `start.cmd`.

1. Click **Try the sample →**. It is a structural projection of a publicly licensed, upstream-described real Claude Code session, not fabricated agent activity.
2. See **349 records → 92 tools → 5 explicit failures**, each linked to source lines. Complete parser coverage does not make a failed run healthy.
3. Open a failure's evidence, then create a bundle focused on `tool_failed`: **10 records retain the 5 failure pairs**. No prompts, commands, file contents, paths, original IDs, or outputs are copied.
4. Preview and download the bundle. Verify it in the UI or CLI. Verification re-runs the parser and compares its structural diagnostic signature. It does not run the agent.

No account. No API key. No telemetry. No remote assets. Only files you explicitly select are read. The web app talks to a loopback Python server on your own computer; imported content is processed in memory and is not written by the server.

```text
349 records → 92 paired tools → 5 explicit failures → 10-line evidence slice → offline verification
```

Need your own input? See [installation, transcript location, and capture guidance](docs/IMPORTING.md). For a useful upstream issue, see [the maintainer handoff and reproducibility loop](docs/TRIAGE.md).

## What makes this different

Most session viewers show what the parser understood. Incident Lab also shows **what it did not understand**.

- **A coverage ledger:** physical source line, native event kind, recognized / unknown / malformed. Unsupported input is `metrics: null`, never a reassuring zero.
- **Native format separation:** Codex exec stream is not Codex session rollout. Wrong parser and mixed formats are explicit failures.
- **Correlation evidence:** calls and results, incomplete sessions, orphan results, duplicate IDs, conflicting tool names, and explicit failures.
- **A privacy boundary, not a regex promise:** export constructs a new allowlisted structure. It does not “clean” arbitrary prose. Unknown tool names and IDs are deterministically renamed within each bundle.
- **A reproducible handoff:** bundle hashes, parser version, expected signature, original-source line mapping, full structure or finding-focused slice, and a verifier. Projection equivalence is checked, not assumed.
- **A conservative CI gate:** any diagnostic finding or incomplete coverage fails `--gate`. A clean gate is a parser/tool-observation check, not task success.
- **A/B imports:** compare two observed files, with compatibility checks. No claim that this is a controlled experiment or a causal model comparison.

### A measured distinction, not “better at everything”

At fixed upstream commits, `agent-eval`'s Codex parser returned **0 events and 0 errors** for a 27-record native Codex rollout fixture. Incident Lab reports 2 calls, 2 results with unknown outcomes, and one unsupported native event; the gate fails. On the real Claude fixture **both tools correctly find 92 calls and 92 results**.

`agent-eval` remains a broader agent-execution/evaluation system. This project is a complementary evidence and parser-quality tool. See [the measured comparison](docs/COMPARISON.md), including exact revisions, methodology, and limits.

## CLI workflows

```sh
# Local report. Does not echo transcript prose.
python -m incidentlab inspect path/to/session.jsonl --out report.json

# Wrong schema or explicit failure must not silently pass CI.
python -m incidentlab inspect path/to/session.jsonl --gate

# Full allowlisted structural case, or a focused evidence slice.
python -m incidentlab bundle path/to/session.jsonl --out case.json
python -m incidentlab bundle path/to/session.jsonl --focus tool_failed --out failures.json

# Reproduce parsing on the exported structure, offline.
python -m incidentlab verify failures.json

# Compare two imports, not two newly executed agents.
python -m incidentlab compare before.jsonl after.jsonl --out comparison.json
```

Use `--format codex-exec`, `--format codex-session`, or `--format claude` to diagnose a parser-selection problem. Auto mode refuses mixed known native families. CLI exit codes: `0` command completed (or gate/verification passed); `1` invalid input/I/O; `2` gate or bundle consistency checks failed. Without `--gate`, an inspect command returning a report can exit 0 even if the report contains failures.

## Input support and honest limits

| Input | Support |
|---|---|
| Claude Code JSONL `assistant`/`user` content with `tool_use`/`tool_result` | Calls, results, explicit `is_error`, correlation; metadata records classified |
| Codex `exec --json` `item.*` stream | Command, MCP, web-search, file-change lifecycle; explicit status/exit code |
| Codex native `session_meta` / `response_item` / `event_msg` rollout | Function/custom-tool calls and outputs; opaque output strings remain **unknown outcome** |
| Cursor, OTLP, Codex TUI event capture, arbitrary JSON | Unsupported unless it actually conforms to a supported schema; no auto-conversion claim |

“Recognized” measures record/content-discriminator coverage, **not validation of every metadata field**. Unknown optional keys are ignored and omitted on export. Known metadata and narrative records do not produce tool activity. Native server-side tools and new content variants are deliberately unknown. Unknown content variants may contribute lower-bound tool counts from their supported blocks. Malformed Claude message rows are validated atomically: no calls, results or correlation changes from that row are committed. A complete file can still have unknown tool outcomes. A source-derived demo proves one fixture, not every future CLI version.

An evidence slice is the union of finding source lines and their linked call/result rows. It is not a mathematically minimal reproducer and loses unrelated session context. A diagnostic signature compares format, coverage, counts, gate and finding-code multiplicities, not original text, command semantics, exact timing, or the original execution's cause. `projectionVerified: false` means the export did not preserve that signature; do not submit it as equivalent evidence.

## Privacy and threat model

Read [SECURITY.md](SECURITY.md) before using confidential data. Structural workflow information may itself be confidential. Review the export preview before sharing. The application does not send bundles anywhere. CLI files are saved only at your explicit `--out` destination. Do not expose the local server on a public interface or use a reverse proxy.

## Provenance and licensing

Project code is MIT. The demo is derived from an MIT-licensed Entire fixture with its notice retained. [Provenance](docs/PROVENANCE.md) distinguishes an upstream-described real session from curated Codex test fixtures. The original transcript is **not** shipped. We do not scan installed agents' session directories.

## Project status

Early, deliberately narrow release candidate. Live Codex producer verification and multi-version real-session coverage remain important gaps. A small, owner-authorized synthetic regression suite and CI configuration are now included; hosted CI results still need verification. A limited independent synthetic privacy/HTTP check and local regression run have been completed; comprehensive security review and cross-platform UI acceptance are still gaps. No package registry release, hosted service, star-count prediction, or claim of universal agent-format compatibility. Public API/schema are versioned but may change before 1.0.

Useful contributions: a permitted small native-format reproducer, exact producer version, expected coverage, and a failing structural case. Never attach secrets or private raw sessions. Prefer the bundle workflow above.

## Verification boundaries (0.1.1)

`verify` now reports separate `checks` for projected transcript hash, structural
signature, parser version, export-time projection declaration consistency, and
source-line map shape. `bundleChecksPassed` is true only when these local checks
pass, the producer parser version matches, and the saved projection declaration
is true. A different parser version requires review even if its aggregate output
matches. The legacy `verified` field remains **signature match only** for API
compatibility; do not use it as an overall pass. CLI exit 2 uses
`bundleChecksPassed`.

A map shape check requires one increasing positive line number per projected
record. It cannot prove those were the original line numbers. The saved original
summary and projection declaration are claims supplied by the exporter, not an
independently authenticated source. Hashes detect accidental changes against the
saved value, not forgery: an editor can replace data and recompute them. Neither
success nor the presence of a hash proves who created a bundle, the original
execution, root cause, or that it is safe to share. **Imported bundle privacy is
not verified**; an externally constructed bundle can still contain raw content.

The UI labels legacy report status `trusted` as **coverage-complete**. The API
value is retained for compatibility and means only discriminator coverage, not
full field/schema validation, accurate diagnosis, or successful execution.

## Small public regression suite

Run `python -m unittest discover -v` from this directory. Tests use synthetic
records and cover correlation, parser unknowns, malformed input, allowlist
projection, slices and verification boundaries. They contain no private raw
sessions. `.github/workflows/tests.yml` defines a cross-platform CI matrix;
configuration is not evidence of successful CI runs. This small suite is not
cross-version producer validation or a comprehensive security audit.
