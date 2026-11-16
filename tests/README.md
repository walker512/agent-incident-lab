# Public regression tests

Run from the repository root with Python 3.10+:

```sh
python -m unittest discover -s tests -v
```

Only Python's standard library is required. `test_core.py` inputs are invented in the test
code. `test_corpus.py` additionally checks reviewed structural derivatives of
pinned public sources; see [source-backed evidence](../docs/REGRESSION.md). Controlled Codex projections are checked separately in `test_controlled_corpus.py`,
which also runs the supplied benign fixture programs in a temporary directory.
No session-directory discovery, private transcript, account, model call,
network request, or agent execution is used. Synthetic canaries test selected
export boundaries; they are not credentials.

These tests cover parser correlation, explicit unknowns and malformed records,
structural projection, focused slices, and verification checks. They do not
establish compatibility with every producer version, prove complete privacy,
reproduce an original agent failure, or measure diagnostic accuracy on real runs.
The CI matrix exercises the tests, not full GUI or OS installer acceptance.

Optional UI contract checks require Node.js (no packages):

```sh
node tests/test_web.cjs
```

These use a minimal synthetic DOM to check failure/coverage separation, evidence
selection, verification check cards and stale-response handling. They do not
replace real-browser layout, accessibility, file-download or import acceptance.
