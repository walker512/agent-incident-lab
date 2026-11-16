# Source-backed regression evidence

This corpus tests structural parsing, not root-cause diagnosis. Counts are by
independent source run, never by error row, slice, or derived artifact. The initial
corpus has **one upstream-described public real run and two upstream fixtures**.
Three separately supplied controlled-session projections are reviewed below;
they are not part of the public-source denominator. Existing invented cases remain synthetic.
A passing corpus is not an accuracy estimate or cross-version certification.

## Reproduce

```sh
python -m unittest discover -s tests -v
node tests/test_web.cjs
# Optional network audit: fetch only four fixed public MIT sources into memory.
python scripts/audit_public_sources.py
```

Default CI is offline and uses only structural projections. The optional audit
imports no incidentlab code. It checks original hashes, counts, correlation IDs,
explicit flags, opaque result types, and version metadata against the committed
manifest. It never discovers session directories, executes transcript commands,
writes raw logs, or prints original prose. Network failure is a failure, not a skip.
The manifest records source hashes, transformations, license notices, reviewed
pair annotations and expected results. Tests compare actual parser output with
these fixed labels, not with a newly generated expected signature.

## Reviewed labels and observations

Entire revision: `76f1b5129b974afdf8e59e4ae3755083c10ff8ff`.
The Claude source contains version `2.1.85`; the Codex rollout fixture declares
`0.118.0` without demonstrating an actual producer installation. The Codex exec
fixture has no producer version: **unknown**.

| Input | Expected / observed | Limits |
| --- | --- | --- |
| Claude full2 | 349 recognized records; 92 calls/results; 5 explicit failures; gate false | One run, not five incidents; task outcome unknown |
| Codex rollout fixture | 27 records; 2 calls/results with unknown outcomes; line 27 unknown; gate false | Opaque output text is not structured exit status; `task_completed` unsupported |
| Codex exec fixture | 6 recognized records; 1 successful command; gate true | Negative control, not proof of real task success |

The five Claude error results were individually inspected in the original public
source before annotating these call/result pairs:

| Call / result line | Raw observation summarized | Structural expected label |
| --- | --- | --- |
| 42 / 44 | Exit 126; runtime version configuration missing | failed |
| 43 / 45 | Parallel sibling cancelled after another tool errored | failed, not independent root cause |
| 52 / 53 | Exit 128; requested Git object path absent | failed |
| 312 / 313 | Exit 1 from test command | failed |
| 333 / 334 | Exit 1 from test suite | failed |
| 18 / 19 | Result without an error flag | success negative control under parser semantics |

Call/result ID equality was checked on source fields; only the ID SHA-256 is
stored in annotations. These labels describe explicit tool observations, not
confirmed causality. Aggregate counts were cross-checked by a separate raw-field
scanner. Model-assisted review is not an independent human annotation panel.

## Privacy and licensing

Sources are pinned public Entire repository files under MIT; the existing notice
is retained at `examples/LICENSE-entire.txt`. The maintainer's real-session claim
is linked in [PROVENANCE.md](PROVENANCE.md). This is provenance evidence, not proof
that every upstream participant consented or that the original run was witnessed.
Only allowlisted structural derivatives are distributed: original prose, commands,
outputs, paths, timestamps and IDs are omitted. Source hashes allow local checks
without shipping raw content. Structural information remains information: do not
extend this policy to private user logs. No private user sessions were accessed.

## Public issue candidates excluded from the corpus

Reviewed 2026-11-16. Links are research leads, not imported datasets; no issue
body or snippet is redistributed as a fixture. Public visibility and a code
repository license do not establish redistribution rights for arbitrary issue logs.

- [Claude #59920](https://github.com/anthropics/claude-code/issues/59920): a narrative
  timeline about silence following tool failure, not a complete native JSONL pair
  with a verified CLI version and explicit data reuse permission.
- [Codex #32653](https://github.com/openai/codex/issues/32653): runtime error excerpts
  about missing outputs and crashes, without a complete licensed native rollout.
  It cannot support a fixture-level success/failure verdict.
- [Codex #40515](https://github.com/openai/codex/issues/40515): the author explicitly
  withholds full rollouts because of private prompts, paths and output. Desktop
  state disagreement is also outside this parser's single-file observations.

## Adding controlled runs

Use a fresh disposable project and a dedicated fresh agent data directory. Never
scan or copy an existing user's sessions or credentials into the corpus. Record
CLI version, exact invocation, OS, model if observed, authentication availability
(without secrets), intended trigger, process exit/timeout and raw artifact hash.
Capture the native stream directly; missing authentication is a blocked attempt,
not a successful tool-failure reproduction. Bound duration and cost. Exercise
nonzero exit, missing file, success, and an interrupted run separately. Do not
label each error line as a new run. An intentionally truncated derivative is
synthetic, even if its parent is real; retain its parent ID and exact edit.

Before publishing, inspect all raw events and correlate IDs independently of the
parser, review privacy and rights, export only necessary structure, retain the
notice, and compare reviewed labels against actual results. Keep `controlled-real-run`,
`public-real-run`, `upstream-fixture`, and `synthetic` separate. Unknown producer
versions and unverified outcomes stay unknown. No model run or private log is
required to execute the default suite.

## Additional captured success fragment: known coverage gap

A separate [Gas City corpus](https://github.com/gastownhall/gascity/blob/9a4b1e7181a659c6ac17400ba130e6eb27df777c/internal/worker/workertest/testdata/corpus/README.md)
describes real provider captures with mandatory sanitization. We independently
fetched its pinned `claude/edit-opus-4-8.jsonl`, capture instructions and MIT
license; hashes and review notes are in `tests/corpus/gascity-provenance.json`.
The retained notice is `tests/corpus/LICENSE-gascity.txt`.

This adds **one upstream-described sanitized success fragment**, not another
complete failure run. Producer CLI version is unknown; a model name is not a CLI
version. At raw lines 2/3, matching IDs link an Edit call to a result without an
error flag and with success prose. The top-level `tool_result` discriminator is
unsupported by Incident Lab 0.1.1. Both raw input and its structural projection
produce 2/3 recognized records, 1 pending call, 0 modeled results, `missing_result`
and `unrecognized_records`, and a false gate. This is a parser coverage gap on a
success negative control, not an actual failed Edit or proof of missing output.

The projection replaces the unsupported row with `__unknown__`; it cannot retain
the original result semantics. Regression locks the visible limitation, not a
claim of correct correlation. The independent online audit checks the original
pair separately. Supporting this variant requires a reviewed adapter change and
updated expectations; do not normalize it silently into another native schema.
The optional audit now fetches four pinned public sources. Do not include this
fragment or either Codex fixture in the full-run failure denominator.

## Local validation record (2026-11-16)

Based on main `db7c38f`; isolated branch `regression/public-provenance`.
No `.agents/skills` or `AGENTS.md` exists in that repository revision.
Python 3.12.14: **25 unittest tests passed**. Node v24.22.1: UI contract checks
passed. `git diff --check` passed. The independent network audit passed for all
four pinned public source files. A separate raw-to-projection byte comparison
passed for all four artifacts; raw/projected metrics matched, including the Gas
City coverage gap. Review of the complete projected leaf vocabulary found only
structural discriminators, tool names, local aliases and omission placeholders;
no source prose, paths, original IDs or output is shipped in these projections.
This finite review is not a comprehensive privacy/security guarantee.

Validation used separate raw-field logic and direct field review, but no second
human reviewer or independent agent reviewed the implementation. No remote CI
result is claimed for this branch. GitHub CLI authentication is unavailable in
this environment; the branch can be reviewed/cherry-picked locally. At that initial checkpoint controlled
Codex captures were not included. The subsequent review below adds three sessions.

## Controlled Codex captures reviewed separately

`tests/corpus/controlled/` adds three owner-authorized controlled session
projections, reported as Codex CLI **0.151.0**, Windows, Python **3.11.9**. These
are induced experiments, not natural user incidents. Two sessions emitted command
execution; the first emitted only messages. The successful capture invocations
report `--ephemeral --ignore-user-config --skip-git-repo-check --approve-for-me`;
exact complete invocations are not supplied. No rerun of the producer is claimed
by this review. See the capture operator's retained README and `review.json`.

| Session | Reviewed projection / actual parser result | Interpretation |
| --- | --- | --- |
| test-failure | 5 recognized records; 0 calls/results; `no_tool_activity`; gate false | Operator reports sandbox blockage from model prose; not a structured permission failure |
| test-failure-retry | 7 recognized records; call/result L4/5; exit 1, failed; gate false | One actual command according to capture operator, intentional failing unittest |
| controlled-cases | 13 recognized records; pairs L4/5, L6/7, L8/9 failed; L10/11 success; gate false | Four commands in one session, not four independent runs |

Missing-file, invalid-JSON and timeout labels are operator-reviewed experimental
conditions. The parser sees only nonzero exit/status; it does not infer exception
class or root cause. Timeout is a Python fixture subprocess timeout, not Codex
native tool timeout. The projection normalizes nonzero exits to 1. The success
pair is a negative control inside an otherwise failing session.

The Library v0 package was materialized and its exact bytes inspected. All three
projection hashes matched the supplied manifest; projected call/result IDs and
exit/status fields were reviewed independently before parser assertions. Tests
also rerun the original benign fixture programs in an empty temporary directory,
checking exception classes and a successful command. This validates fixture
behavior locally, not a fresh model execution. Only projections, benign programs
and reviewed provenance were copied; the operator's raw streams were neither
requested nor accessed. Original stream hashes and run authenticity remain
operator-attested and cannot be independently verified from these projections.
Redistribution under the project's MIT license is authorized in the supplied
README. Do not count this as multiple users, natural incidents or an accuracy
benchmark. The three controlled sessions are separate from the one full public
source run, one sanitized success fragment and two upstream fixtures.

Final integrated validation: **28 Python tests passed**, Node UI contracts passed,
and `git diff --check` passed after the controlled corpus was added. The four
original benign failure modes reproduced locally and the success control exited 0.
No fresh Claude/Codex model run or cross-platform CI execution occurred in this
review environment.

## Independent follow-up review (2026-11-16)

A separate reviewing agent inspected the changes against `db7c38f`, including
source-label logic, projection vocabulary, license notices and claim boundaries.
It reran all 28 Python tests, Node UI contracts, the four-source network audit and
`git diff --check`; all passed. This was independent implementation review, not
an independently witnessed producer run or an external human annotation panel.
The Gas City result semantics remain intentionally unavailable in the shipped
projection and are only checked against the pinned upstream source by the opt-in audit.
