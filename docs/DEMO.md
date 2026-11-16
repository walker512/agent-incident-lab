# A 90-second incident handoff

**Pitch:** when an agent tool fails, give the maintainer inspectable evidence instead of an unreviewed transcript dump. The differentiator is the handoff: native records → explicit coverage gaps → correlated observations → content-stripped case → offline consistency check.

## Before presenting

Run `python -m unittest discover -v`, then `python -m incidentlab serve` and open http://127.0.0.1:8765. No account, API key, internet, or private transcript is required. The bundled sample is a licensed structural projection of an upstream-described real Claude session; see PROVENANCE.md. Do not describe it as a live agent run.

## Demonstration

- **0–15 seconds:** click **Try the sample →**. The heading says **5 explicit tool failures observed** while coverage is 100%. Explain: accounting for records is different from a successful tool or task.
- **15–40 seconds:** click a finding's **Open incident evidence →**. Show the tool state, paired call/result lines and their record dispositions. These are source pointers, not a root-cause conclusion. Original prose is deliberately not shown.
- **40–65 seconds:** choose **Prepare evidence slice →**. This includes every `tool_failed` occurrence: 349 records reduce to 10 records preserving all 5 failed pairs. Inspect the structure and ordinalized identifiers. The slice is not a proven minimal reproduction.
- **65–80 seconds:** click **Verify this preview locally**. The actual parser re-runs on that exact projection. Green consistency checks are distinct from amber source authenticity, actual line numbers and privacy, which cannot be verified here.
- **80–90 seconds:** review and download. The recipient uses **Verify saved bundle** or `python -m incidentlab verify incident-diagnostic.json`. No agent or shell command is replayed.

## Answers to likely questions

**Why not ask an LLM?** The exported artifact and parser signature are deterministic and inspectable offline, with unknowns and limitations explicit. This is not a replacement for investigating command semantics privately.

**Does it fix the agent?** No. It identifies structural observations and creates a reproducible parser case, not an environment replay or causal diagnosis.

**Is the export anonymous?** No. Content allowlisting removes specified text fields, but structure, ordering, counts and source-line mapping can be sensitive. The owner reviews the exact artifact before sharing.

**What is new for this demonstration?** Clickable incident evidence, category-scoped handoff from that evidence, and verification check cards in the preview. Existing parser and projection behavior is retained. Follow the event's rules on pre-existing work and disclose the repository's prior history; eligibility has not been established.

**Does this prove market demand or superiority?** No. The next useful evidence is whether a maintainer can resolve an actual parser report using the bundle, not a star prediction. See COMPARISON.md for narrowly scoped measurements, not a broad product-ranking claim.
