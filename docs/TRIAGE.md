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
verify result:
Known truncation, merges, or missing earlier segments:

Attached: reviewed structural-parser-case bundle only.
No claim of original command/environment reproduction.
```

Do not attach a raw session to fill in a missing field. If source output is required to diagnose the execution failure, obtain permission and share it separately through the appropriate private channel. The parser bundle is intended for adapter/correlation debugging, not as a replacement for a conventional software reproducer.

## Reproducibility without publishing private tests

The downloadable source intentionally excludes the private validation suite and raw verification fixtures. This limits independent contributor confidence; it is not the normal ideal for a mature open-source library. No CI badge or public-test coverage claim is made.

A recipient can still perform this public, deterministic acceptance loop without installing an agent or using credentials:

```sh
python -m incidentlab inspect examples/claude-structural.jsonl --gate --out report.json
# Expected exit 2: five explicit tool failures. Not a parser crash.
python -m incidentlab bundle examples/claude-structural.jsonl --focus tool_failed --out case.json
python -m incidentlab verify case.json
# Expected verified=true, ten records, five calls/results/failures.
python -m incidentlab compare examples/claude-structural.jsonl examples/claude-structural.jsonl
# Expected comparable imports and all metric deltas zero; not an agent experiment.
```

The CLI can be integrated into existing private CI using its documented exit codes. Do not publish raw logs or report source hashes from confidential runs as CI artifacts. A future public contribution test suite and automation require an explicit project-owner decision; this release does not silently publish them.

## Before treating this as a long-term platform

Important unclosed work: live Codex producer validation; multiple versions and diverse real sessions; formal schema/version contracts; visible public regression tests and CI when authorized; installation packaging and signed releases; external maintainer feedback; and stronger controlled experiments if execution-regression claims are ever added. A polished local workflow is not evidence of product-market fit or future stars.
