# Measured scope, not universal superiority

## Motivation

- [`vercel-labs/agent-eval` #216](https://github.com/vercel-labs/agent-eval/issues/216) reports a custom agent's parser alias not being respected in saved-result parsing, leaving transcript-derived metrics at zero. This is an upstream report, not a claim that Incident Lab fixes the agent-eval runner.
- [#190](https://github.com/vercel-labs/agent-eval/issues/190) raises a possible Codex session-fallback / exec-schema mismatch. The reporter explicitly could not verify it with a real Codex run. Our fixture experiment below is a narrower finding, not proof that the production fallback currently fails.

## Direct experiment

We executed unmodified exported `parseClaudeCodeTranscript` and `parseCodexTranscript` functions from agent-eval revision **`9ff2ea3e9f14c14e5123b215c3f695d3b4f9955d`**, using Node's TypeScript stripping and a resolver mapping the source's `.js` imports to their `.ts` files. Only module resolution was adapted; parser source was not changed. No agent execution, model call, sandbox infrastructure, or benchmark score was involved. The package declares MIT; no competitor source code is copied into this project.

Inputs are the fixed Entire revision documented in [PROVENANCE.md](PROVENANCE.md).

| Input | agent-eval parser observed | Incident Lab observed |
|---|---|---|
| Real-session-described Claude fixture, 349 records | 322 events; 92 calls; 92 results; no parse errors | 349 classified records; same 92 calls / 92 results; 5 explicit failures with source lines; gate fails |
| Codex native rollout **test fixture**, 27 records | 0 events; no parse errors | 2 calls / 2 results; 2 unknown outcomes; 1 unsupported native event; partial coverage; gate fails |
| Codex exec **test fixture**, 6 records | 6 events; 1 call / 1 result; no parse errors | 6 classified records; 1 call / 1 result; no findings; gate passes |

Event counts are not record counts, so 322 versus 349 is **not** an accuracy score. The Claude result shows parity for tool extraction. The rollout result demonstrates one practical need for explicit format selection and unknown/partial diagnostics. It does not establish performance, robustness across all versions, or inferiority of agent-eval's full workflow. Cursor was not included in this comparison because its native parser would be a separate experiment.

To reproduce: check out the exact agent-eval revision, load those parser exports through the repository's TypeScript toolchain, read each fixture as UTF-8, and inspect `events`, event type counts and `errors`. For Incident Lab, run `python -m incidentlab inspect downloaded-fixture.jsonl`. The cases' source hashes are in the provenance document.

## What existing tools still do better

Agent-eval runs controlled coding-agent experiments and assertions. Generic trace/replay tools can provide richer execution visualization, storage, diff/fork experiences and integrations. Incident Lab does not replace those capabilities. Its narrow proposition is **native-format coverage → source evidence → content-stripped structural case → deterministic parser verification**, with explicit unknowns. The real value of that proposition still needs feedback from upstream maintainers and users; GitHub stars are not guaranteed.
