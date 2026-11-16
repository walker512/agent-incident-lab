# Public synthetic regression tests

Run from the repository root with Python 3.10+:

```sh
python -m unittest discover -s tests -v
```

Only Python's standard library is required. Every input is invented in the test
code. No session-directory discovery, private transcript, account, model call,
network request, or agent execution is used. Synthetic canaries test selected
export boundaries; they are not credentials.

These tests cover parser correlation, explicit unknowns and malformed records,
structural projection, focused slices, and verification checks. They do not
establish compatibility with every producer version, prove complete privacy,
reproduce an original agent failure, or measure diagnostic accuracy on real runs.
The CI matrix exercises the tests, not full GUI or OS installer acceptance.
