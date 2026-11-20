# Code review: Add cancel-by-link to SMS reminders (`feature/cancel-link`)

**Verdict: Request changes**

The branch adds day-before SMS reminders with a one-tap cancel link. The feature is well scoped, but the cancel endpoint is open to SQL injection, its tokens are guessable and never expire, and a live SMS API key is committed - together these would let anyone cancel any patient's appointment. Fix the three blockers and add tests before merging; the rest are quick follow-ups.

| | |
|---|---|
| Scope | 6 files, +75 / -0, 1 commit against `main` |
| Checklist | `skills/code-review-checklist/references/default-checklist.md` (no `.code-review-checklist.md` in the repo) |
| Findings | 3 blocker · 5 major · 4 minor · 1 nit |

## Findings

### 1. [blocker] SQL injection in the cancel endpoint - `app/routes/cancel.py:26` (SEC-3, SEC-2)

The token from the URL is interpolated into SQL with an f-string. A request to `/c/x' OR '1'='1` matches the first token in the table and cancels that appointment; crafted tokens can read other data. **Why it matters:** the endpoint is public and unauthenticated by design.

**Suggested fix:** parameterise, and reject anything that is not a well-formed token before touching the database.

```python
if not re.fullmatch(r"[A-Za-z0-9_-]{20,64}", token):
    abort(404)
row = db.execute("SELECT appointment_id FROM cancel_tokens WHERE token = ?", (token,)).fetchone()
```

### 2. [blocker] Live SMS API key committed - `app/config.py:4` (SEC-1, MNT-5)

`SMS_API_KEY = "tnn_live_..."` is in source. **Why it matters:** anyone with repository access can send SMS billed to BrightSmile under its sender name, and the key stays in git history even after it is removed.

**Suggested fix:** rotate the key with the provider now, then read it from the environment and fail fast when it is missing:

```python
SMS_API_KEY = os.environ["SMS_API_KEY"]  # KeyError at startup is better than silently sending nothing
```

### 3. [blocker] Cancel tokens are guessable, never expire and can be reused - `app/routes/cancel.py:15`, `migrations/003_cancel_tokens.sql:1` (SEC-5, PERF-4)

`random.random()` is not a cryptographic generator, and 12 digits is a small space for an unauthenticated action. The table has no expiry, no "used" marker and no unique index, so a token works forever and every lookup scans the whole table, which grows by one row per reminder per day.

**Suggested fix:**

```python
token = secrets.token_urlsafe(16)  # 22 characters; the SMS still fits in one 160-character segment
```

```sql
CREATE TABLE cancel_tokens (
    token TEXT PRIMARY KEY,
    appointment_id INTEGER NOT NULL REFERENCES appointments (id),
    expires_at TEXT NOT NULL,          -- appointment start time
    used_at TEXT
);
```

and in the handler require `expires_at > now` and `used_at IS NULL`, setting `used_at` in the same transaction as the cancellation.

### 4. [major] Opening the link cancels immediately (state change on GET) - `app/routes/cancel.py:23` (SEC-4, COR-2)

Messaging apps, SMS link previews and security scanners fetch links automatically. With a cancelling `GET`, an appointment can be cancelled without the patient ever tapping the link. **Why it matters:** silent cancellations mean empty chairs and confused patients the day before their visit.

**Suggested fix:** `GET /c/<token>` shows the appointment and a "Cancel appointment" button; the button sends `POST /c/<token>`, which performs the cancellation.

### 5. [major] Any appointment can be cancelled, whatever its state or time - `app/routes/cancel.py:29` (COR-2)

The update does not check that the appointment is still `booked` or in the future, so an old link cancels a completed visit and a second tap "cancels" twice. **Suggested fix:**

```python
cur = db.execute(
    "UPDATE appointments SET status = 'cancelled' WHERE id = ? AND status = 'booked' AND starts_at > ?",
    (row["appointment_id"], now_iso),
)
if cur.rowcount == 0:
    return render_already_handled_page()
```

### 6. [major] Tokens and patient phone numbers written to logs - `app/routes/cancel.py:19`, `app/reminders.py:28` (SEC-6, MNT-2)

`log.info(... token ...)` puts a working cancel credential in the logs, and the `print` writes each patient's phone number and full message to stdout (cron mail or log files). **Why it matters:** log access becomes cancel access, and phone numbers are personal data. **Suggested fix:** remove the `print`; log the appointment id and a short hash of the token only.

### 7. [major] SMS sending can hang, fails silently, and reruns send duplicates - `app/reminders.py:12`, `app/reminders.py:29` (COR-3, COR-4, PERF-2)

`requests.post` has no timeout, so one slow provider response can stall the whole cron run; the response status is never checked, yet `sent` is incremented anyway; and if the job is re-run (after a crash or a manual retry), every patient gets a second SMS with a second token. **Suggested fix:**

```python
resp = requests.post(..., timeout=10)
resp.raise_for_status()
```

wrap each send in `try/except requests.RequestException` (log the appointment id, continue with the next patient), and record `reminder_sent_at` on the appointment so the query can skip patients already reminded.

### 8. [major] No tests for the new behaviour (TST-1, TST-2)

No test files changed. At minimum: token creation is unique and unguessable in format; a valid token cancels exactly one booked future appointment; an unknown, expired, used or malformed token returns 404 and changes nothing; `send_reminders` builds the right language and skips failed or already-reminded appointments (mock `send_sms`). The existing `tests/test_bookings.py` fixture already applies all migrations, so these fit in a new `tests/test_cancel.py`.

### 9. [minor] One patient query per appointment - `app/reminders.py:21` (PERF-1)

Fine at today's volume (one query per appointment per day), but a join removes it entirely:

```sql
SELECT a.*, p.language FROM appointments a
LEFT JOIN patients p ON p.phone = a.patient_phone
WHERE a.starts_at >= ? AND a.starts_at < ? AND a.status = 'booked'
```

### 10. [minor] "Tomorrow" depends on the server's time zone - `app/reminders.py:17` (COR-2, PERF-4)

`date.today()` uses the server's local zone. On a UTC server the 18:00 cron and the date calculation disagree with Vietnam time. Use `datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()`. The range query in #9 also lets SQLite use `idx_appointments_starts_at`, which a `LIKE` pattern does not, and it skips cancelled appointments (the current query reminds them too).

### 11. [minor] `requests` is not pinned - `requirements.txt:3` (SEC-7)

Every other dependency is pinned; pin this one too (for example `requests==2.32.5`) so builds are reproducible.

### 12. [minor] Confirmation page is English-only - `app/routes/cancel.py:11` (COR-2)

Most patients receive the Vietnamese SMS but land on an English page. Render the page in the patient's language (`patients.language` is already available).

### 13. [nit] Document the new cron job and settings (MNT-4)

Note in the README that `send_reminders` must run daily at 18:00 Vietnam time, and list `SMS_API_KEY`, `SMS_SENDER` and `PUBLIC_BASE_URL`.

## Checklist coverage

| Item | Status | Notes |
|---|---|---|
| SEC-1 | issue #2 | Live key in `config.py`. |
| SEC-2 | issue #1 | URL token is not validated. |
| SEC-3 | issue #1 | f-string SQL. |
| SEC-4 | issue #4 | Public endpoint by design; the token is the authorisation, so #3 and #4 carry the risk. |
| SEC-5 | issue #3 | `random.random`, no expiry, reusable. |
| SEC-6 | issue #6 | Token and phone numbers logged. |
| SEC-7 | issue #11 | `requests` unpinned. |
| COR-1 | pass | Matches the commit message; nothing unrelated changed. |
| COR-2 | issue #4, #5, #10, #12 | |
| COR-3 | issue #7 | Send failures ignored. |
| COR-4 | issue #7 | Re-running the job duplicates SMS. |
| COR-5 | pass | Only additions; existing routes unchanged. |
| COR-6 | pass | Additive migration (new table), safe on a populated database; no down migration, consistent with 001-002. |
| TST-1 | issue #8 | No tests. |
| TST-2 | issue #8 | |
| TST-3 | n/a | No tests added. |
| TST-4 | n/a | Not a bug fix. |
| PERF-1 | issue #9 | |
| PERF-2 | issue #7 | No timeout on the SMS call. |
| PERF-3 | pass | Nothing repeated unnecessarily. |
| PERF-4 | issue #3, #10 | Token lookups unindexed; `LIKE` date filter. |
| MNT-1 | pass | Clear names, small functions. |
| MNT-2 | issue #6 | Debug `print`. |
| MNT-3 | pass | Reuses `get_db` and the blueprint pattern. |
| MNT-4 | issue #13 | |
| MNT-5 | issue #2 | |
| *Calendar sync* | not verifiable | This repository has no Google Calendar code. Confirm that whatever syncs the dentists' calendars treats `status = 'cancelled'` as a free slot; otherwise cancelled slots stay blocked. |

## Automated risk flags

All 7 flags from `gather_diff.py` were checked:

| Flag | Location | Outcome |
|---|---|---|
| possible_secret | `app/config.py:4` | Confirmed as #2. |
| debug_statement | `app/reminders.py:28` | Confirmed as #6. |
| weak_random_or_hash | `app/routes/cancel.py:15` | Confirmed as #3. |
| possible_sql_injection | `app/routes/cancel.py:26` | Confirmed as #1. |
| migration | `migrations/003_cancel_tokens.sql` | Reviewed: additive and safe; schema problems in #3. |
| dependency_change | `requirements.txt` | Confirmed as #11. |
| source_without_tests | 5 source files | Confirmed as #8. |

## What's good

- Choosing the SMS language from `patients.language` is a thoughtful touch, and both messages fit in a single SMS segment - keep that true when the token gets longer.
- The change follows the existing structure (blueprint, `get_db`, numbered migrations), so it will be easy to fix in place.
