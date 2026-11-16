# Bring a permitted native record

## Install and first launch

This source release needs **Python 3.10+**, not an agent subscription. Download Python from [python.org](https://www.python.org/downloads/) if needed. Extract the ZIP before launching; do not run from the archive viewer.

- Windows: open a terminal in the extracted `agent-incident-lab` folder. Run `py -3 --version`, then `py -3 -m incidentlab serve`. `start.cmd` uses `python`; if that alias is unavailable, use the `py -3` command instead.
- macOS/Linux: `python3 --version`, then `python3 -m incidentlab serve` from the extracted folder.
- Open `http://127.0.0.1:8765`. If the port is occupied, use `python -m incidentlab serve --port 8766` and open that port.
- Run `python -m incidentlab --version` when reporting a problem.

No dependency installer, model login, or file upload is necessary to try the bundled projected Claude sample. This sample is described in [PROVENANCE.md](PROVENANCE.md). Do not install an agent merely to view it.

## Locate an existing file manually

The application deliberately **does not auto-discover or read session folders**. A home-directory scan can expose unrelated projects. Use your file manager and explicitly select one file you are permitted to analyze. Do not copy a whole sessions folder into an issue or repository.

### Codex

The upstream CLI uses its configured Codex home for session storage. On a conventional installation this is `~/.codex/sessions`; a configured `CODEX_HOME` changes it. On Windows the equivalent conventional location is `%USERPROFILE%\.codex\sessions`. These are guidance for your own computer, not locations the application scans. Runtime packaging, managed deployments, and future versions can differ.

Choose the intended JSONL using session identity and modification time, not simply the newest file. A saved rollout begins with native types such as `session_meta`, `turn_context`, `response_item`, or `event_msg`. Choose **Codex session**. A stdout stream beginning with `thread.started` / `item.*` uses **Codex exec**. TUI debug event captures, JSON arrays, and compressed/archived formats are not interchangeable.

Source for the storage convention: [official Codex source](https://github.com/openai/codex/tree/95946faafcd8f068e28610e8ae6a4c03060c1448/codex-rs), including the CLI session inventory and rollout code. Do not infer that every record emitted by that version is supported: unknown variants are reported explicitly.

### Claude Code

A conventional native installation keeps project session JSONL under `~/.claude/projects/<project>/<session>.jsonl`, or the equivalent home folder on Windows. Configuration overrides may relocate it. Check your installed CLI's configuration directory and documentation rather than changing permissions or searching other users' folders. The [official CLI reference](https://code.claude.com/docs/en/cli-reference) describes configuration/auth status commands and their version limits.

Choose a native transcript with `assistant` / `user` records and message content blocks. The selected real-session demo validates one producer sample, not all Claude versions or all streaming/API formats. `--output-format json` output is not automatically the same as saved native JSONL.

## Capture a new Codex exec stream yourself (optional)

This step **runs an agent** using your installed Codex and account; it may consume your plan or billed usage. Incident Lab does not run it for you. Use an empty throwaway folder, never a private project, and review your installed CLI's `codex exec --help` first. Do not disable sandboxing or approvals to make this example work.

The [official non-interactive documentation](https://developers.openai.com/codex/noninteractive) describes JSONL stdout via `--json`. For a no-tools smoke capture:

```sh
codex exec --json --sandbox read-only --skip-git-repo-check "Do not read files or use tools. Reply only: INCIDENTLAB_CAPTURE_OK." > capture.jsonl
```

Run that command **inside the empty throwaway folder**. Note the absolute path to `capture.jsonl`. Incident Lab is source-only, not globally installed: **open a second terminal in the extracted `agent-incident-lab` folder**, then inspect the capture using its absolute path. Replace the example path below with your actual path:

```sh
# Working directory: the extracted agent-incident-lab folder, not the capture folder.
python -m incidentlab inspect "/absolute/path/to/throwaway/capture.jsonl" --format codex-exec
```

On Windows, use `py -3` instead of `python` if needed, and a quoted Windows path such as `"C:\Users\your-name\capture-folder\capture.jsonl"`. If your CLI supports `--ephemeral`, you can add it to avoid saving a session; version-specific flags may differ. Redirect stdout only: mixing stderr into JSONL produces malformed records. Older Windows PowerShell redirection may produce UTF-16; save as UTF-8 before import.

A no-tool capture is expected to produce `no_tool_activity` and fail the conservative gate. That is not a bug: a successful chat response does not establish tool execution. To validate tool correlation, use a permitted throwaway task that actually invokes a tool, then inspect what the agent really emitted; never fabricate call/result rows and call them a live run.

**Current verification boundary:** native Codex exec and rollout support has been exercised on public upstream test fixtures. A fresh successful live Codex run has not yet been validated for this release. No live-Codex success claim is made. If initialization/authentication fails, keep that separate from the parser's behavior; do not submit an empty output file as a successful fixture.

## When inspection is incomplete

- **Unsupported:** check format, JSONL versus JSON array, and producer. Metrics are null.
- **Partial:** use the unknown/malformed ledger filter. Record the CLI version and unknown discriminator. Counts can be lower bounds.
- **Missing result:** confirm the process ended and the file copy is complete. A running or truncated session is not successful.
- **Unknown outcome:** inspect source output privately. An opaque string is not a structured success flag.
- **Tool failed:** distinguish an expected nonzero command, cancellation, test failure, and root cause in the original environment. The tool only reports explicit observed failure.

Each finding in the UI has **What to check next** guidance. When sharing, use a finding-focused structural bundle and review it. Include producer version manually in your issue; the export deliberately removes original metadata. See [the maintainer handoff](TRIAGE.md).
