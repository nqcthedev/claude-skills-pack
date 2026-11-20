# Default code review checklist

Copy this file to `.code-review-checklist.md` in your repository root and edit it to make it your team's checklist. Keep the item ids stable so reviews can be compared over time. Mark a whole section `(n/a)` in its heading to skip it.

## Security

- **SEC-1** No secrets, keys, tokens or passwords in code, config or tests; secrets come from the environment or a secret manager.
- **SEC-2** All external input (HTTP params, headers, files, env, message payloads) is validated before use.
- **SEC-3** Database queries, shell commands and HTML output use parameterisation or escaping - no string-built SQL, shell or markup from user input.
- **SEC-4** Authentication and authorisation are enforced on every new endpoint or action, including object-level ownership checks.
- **SEC-5** Security-sensitive randomness (tokens, ids, passwords) uses a cryptographically secure generator; tokens expire and are single-use where appropriate.
- **SEC-6** Sensitive data (passwords, tokens, personal data) is not logged or returned in errors.
- **SEC-7** New dependencies are maintained, pinned by the lockfile and justified.

## Correctness

- **COR-1** The change does what the PR description says, and nothing the description does not mention.
- **COR-2** Edge cases are handled: empty, null/None, zero, very large, duplicates, unicode, time zones.
- **COR-3** Errors are handled deliberately: no swallowed exceptions, failures surface with useful messages, partial work is rolled back.
- **COR-4** Concurrency and ordering are safe: no race conditions on shared state, idempotent where retries are possible.
- **COR-5** Public interfaces (APIs, schemas, CLI flags, events) stay backward compatible or the breaking change is called out with a migration path.
- **COR-6** Database migrations are reversible or the risk is documented, and are safe on a populated table.

## Tests

- **TST-1** New or changed logic has tests that would fail without the change.
- **TST-2** Tests cover the failure paths and edge cases from COR-2, not only the happy path.
- **TST-3** Tests are deterministic: no reliance on wall-clock time, network, ordering or shared state without control.
- **TST-4** Bug fixes include a regression test reproducing the bug.

## Performance

- **PERF-1** No N+1 queries or per-item network calls inside loops over unbounded collections.
- **PERF-2** Work on request paths is bounded: pagination, limits, timeouts on external calls.
- **PERF-3** Expensive work is not repeated unnecessarily (caching, memoisation, batching where it matters).
- **PERF-4** New indexes exist for new query patterns on large tables.

## Maintainability

- **MNT-1** Names say what things are; functions do one job and are small enough to read in one screen.
- **MNT-2** No dead code, commented-out code, debug prints or stray TODOs without a ticket reference.
- **MNT-3** Duplicated logic is extracted when it appears a third time; existing helpers are reused.
- **MNT-4** Comments explain why, not what; docs and README are updated for behaviour changes.
- **MNT-5** Configuration values are not hardcoded where they differ between environments.
