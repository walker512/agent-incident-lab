# A maintainer-ready handoff

## What you can prove

A bundle can prove that this parser version produces a particular structural diagnostic signature on the bundled, content-stripped JSONL. It cannot prove the original agent's environment, actual command semantics, root cause, or whether a model solved the user's task.

For the bundled Claude example:

```text
INPUT                         INSPECT                      EVIDENCE SLICE             VERIFY
349 projected records   ->   92 calls / 92 results   ->   10 records / 5 pairs   ->   signature matches
                             5 explicit failures          tool_failed only            no agent executed
```

The five result source lines are 44, 45, 53, 313 and 334. The slice's `sourceLines` maps compacted record positions back to the original file. Selecting a slice discards unrelated context. It is not a delta-debugged mathematical minimum.

## Suggested issue body (copy and complete)

```text
Producer and version:
Incident Lab version:
Input family (native Claude / Codex exec / Codex session):
Observed diagnostic:
Expected parser behavior:
Full file or evidence slice:
projectionVerified result:
bundleChecksPassed and individual checks:
Known truncation, merges, or missing earlier segments:

Attached: reviewed structural-parser-case bundle only.
No claim of original command/environment reproduction.
```

Do not attach a raw session to fill in a missing field. If source output is required to diagnose the execution failure, obtain permission and share it separately through the appropriate private channel. The parser bundle is intended for adapter/correlation debugging, not as a replacement for a conventional software reproducer.

## Reproducibility without publishing private tests

The source includes a small synthetic regression suite and a CI configuration. Private validation scripts and raw verification fixtures remain excluded. Run `python -m unittest discover -v` locally. CI configuration does not establish a passing hosted run, and these tests do not prove compatibility with every producer version.

A recipient can still perform this public, deterministic acceptance loop without installing an agent or using credentials:

```sh
python -m incidentlab inspect examples/claude-structural.jsonl --gate --out report.json
# Expected exit 2: five explicit tool failures. Not a parser crash.
python -m incidentlab bundle examples/claude-structural.jsonl --focus tool_failed --out case.json
python -m incidentlab verify case.json
# Expected bundleChecksPassed=true, ten records, five calls/results/failures.
# Inspect individual checks; source authenticity and imported privacy remain unverified.
python -m incidentlab compare examples/claude-structural.jsonl examples/claude-structural.jsonl
# Expected comparable imports and all metric deltas zero; not an agent experiment.
```

The CLI can be integrated into existing private CI using its documented exit codes. Do not publish raw logs or report source hashes from confidential runs as CI artifacts. The project owner authorized the small public synthetic regression suite. Additional real-session fixtures still need explicit sharing permission and provenance review.

## Before treating this as a long-term platform

Important unclosed work: live Codex producer validation; multiple versions and diverse real sessions; formal schema/version contracts; verified hosted CI runs and broader authorized real-session regression coverage; installation packaging and signed releases; external maintainer feedback; and stronger controlled experiments if execution-regression claims are ever added. A polished local workflow is not evidence of product-market fit or future stars.

Verification checks local consistency only. The legacy `verified` field is signature match only; use `bundleChecksPassed` and `checks`. Source identity and actual source line accuracy cannot be established without the original source. Imported bundle privacy is not checked.
