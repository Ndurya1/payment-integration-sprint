# Payment Integration Sprint — Error Log

> Living troubleshooting reference for the FastAPI + PostgreSQL + Safaricom Daraja STK Push integration.
>
> **Purpose:** Record errors encountered during development, their root causes, their fixes, and useful checks for recurrence.

---


## 2. SQLAlchemy async support failed because `greenlet` was missing

### Error / symptom

SQLAlchemy's async database/session path failed because `greenlet` was unavailable. An installation attempt initially also returned:

```text
ERROR: No matching distribution found for greenlet
```

### Cause

SQLAlchemy uses `greenlet` internally for parts of its async integration. The dependency was missing, and the earlier broken `pip` environment also interfered with installation.

### Resolution

After fixing the virtual environment:

```powershell
python -m pip install greenlet
```

Restart FastAPI afterward.

### Prevention

Keep the database runtime dependencies in the project's dependency file. Typical async PostgreSQL dependencies include:

```text
sqlalchemy
asyncpg
greenlet
```

---

## 3. Pydantic settings reported required configuration as missing

### Error / symptom

Application startup failed because settings fields such as these were missing:

```text
database_url
redis_url
secret_key
```

while Daraja environment variables were reported as extra/forbidden fields.

### Cause

The `Settings` model and `.env` file did not describe the same configuration contract.

Some required application settings were absent or named differently, while Daraja variables existed in `.env` without corresponding accepted settings fields.

### Resolution

Make the settings model and `.env` consistent.

Example:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    secret_key: str

    daraja_consumer_key: str
    daraja_consumer_secret: str
    daraja_shortcode: str
    daraja_passkey: str
    daraja_callback_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )
```

Use the exact configuration appropriate to the project, but keep field names consistent.

### Prevention

Treat `Settings` as the application's configuration boundary. Whenever a new environment variable is introduced, define how it is loaded and accessed.

---

## 4. `os.environ[...]` raised `KeyError` for Daraja configuration

### Error / symptom

Code such as:

```python
os.environ["DARAJA_CONSUMER_KEY"]
```

raised a `KeyError` even though the value existed in `.env`.

### Cause

Pydantic reading values from `.env` does not mean those values have automatically been inserted into `os.environ`.

The application mixed two configuration mechanisms:

```python
settings.daraja_consumer_key
```

and:

```python
os.environ["DARAJA_CONSUMER_KEY"]
```

### Resolution

Use the central Pydantic settings object consistently:

```python
settings.daraja_consumer_key
settings.daraja_consumer_secret
```

### Prevention

Do not mix direct `os.environ` access with Pydantic settings for the same configuration values unless there is a deliberate reason.

---

## 5. `ImportError: cannot import name 'process_callback'`

### Error / symptom

FastAPI failed during import with:

```text
ImportError: cannot import name 'process_callback'
```

### Cause

`process_callback` was implemented as a service method using `self`, but was imported as though it were a standalone module-level function.

The code mixed:

```python
from service import process_callback
```

with an implementation conceptually belonging to:

```python
payment_service.process_callback(...)
```

### Resolution

If the method belongs to the service class, invoke it through the service instance:

```python
await payment_service.process_callback(payload)
```

A standalone function, by contrast, must be defined at module scope and must not use `self`.

### Prevention

Keep the dependency direction consistent:

```text
route -> service instance -> repository / external API
```

---

## 6. Daraja rejected the STK Push callback URL

### Error / symptom

Daraja returned:

```text
400.002.02 Bad Request - Invalid CallBackURL
```

### Cause

The `CallBackURL` supplied in the STK Push request was not a valid publicly reachable HTTPS callback URL.

Safaricom cannot call a FastAPI endpoint running only on localhost.

### Resolution

Expose the local server through a public HTTPS tunnel such as ngrok, then append the actual callback route:

```text
https://<public-tunnel-host>/payments/callback
```

Use that exact URL as the STK Push `CallBackURL`.

### Verification

The callback URL must:

1. use HTTPS;
2. be publicly reachable;
3. point to the correct FastAPI route;
4. not contain duplicated prefixes;
5. remain active while waiting for the callback.

---

## 7. Daraja callback reached FastAPI but returned `404 Not Found`

### Error / symptom

The intended callback produced:

```text
POST /payments/callback 404 Not Found
```

### Cause

The `/payments` prefix had been applied twice.

For example:

```python
router = APIRouter(prefix="/payments")
```

combined with:

```python
app.include_router(router, prefix="/payments")
```

creates:

```text
/payments/payments/callback
```

rather than:

```text
/payments/callback
```

### Resolution

Apply the prefix once.

Either:

```python
router = APIRouter(prefix="/payments")
app.include_router(router)
```

or:

```python
router = APIRouter()
app.include_router(router, prefix="/payments")
```

After correction, the callback reached:

```text
POST /payments/callback 200 OK
```

### Prevention

Use FastAPI's OpenAPI docs or inspect registered routes whenever an endpoint unexpectedly returns `404`.

---

## 8. `AsyncClient` used with the synchronous context manager

### Error / symptom

STK Query failed with:

```text
TypeError: 'AsyncClient' object does not support the context manager protocol
```

### Cause

`httpx.AsyncClient` was opened with ordinary `with` rather than `async with`.

Incorrect:

```python
with httpx.AsyncClient() as client:
    ...
```

### Resolution

Use:

```python
async with httpx.AsyncClient() as client:
    response = await client.post(url, json=payload, headers=headers)
```

### Prevention

Remember:

```text
httpx.Client       -> with + synchronous calls
httpx.AsyncClient  -> async with + await
```

---

## 9. `httpx.Response` object was incorrectly awaited

### Error / symptom

During the async conversion, code attempted to await a synchronous HTTP call and produced an error indicating that an `httpx.Response` object could not be awaited.

### Cause

The top-level synchronous function:

```python
httpx.post(...)
```

returns a `Response` immediately. It is not a coroutine.

Incorrect:

```python
response = await httpx.post(...)
```

### Resolution

Use an asynchronous client:

```python
async with httpx.AsyncClient() as client:
    response = await client.post(...)
```

### Prevention

Adding `await` does not make synchronous code asynchronous. The function being called must itself return an awaitable.

---

## 10. Missing `await` in the async Daraja service chain

### Error / symptom

Coroutine-related errors appeared after only part of the Daraja service had been converted to async.

### Cause

An async method was called as though it returned its final value immediately.

For example, an OAuth token method defined with `async def` must be awaited.

### Resolution

Use:

```python
access_token = await self.get_access_token()
```

and keep the async chain consistent:

```text
async route
   -> await service method
      -> await token/network method
         -> await AsyncClient request
```

### Prevention

Whenever a function changes from `def` to `async def`, inspect every caller and determine whether it now needs `await`.

---

## 11. Synchronous timestamp/password helpers were incorrectly treated as async

### Error / symptom

During the async refactor, local timestamp/password helper functions were treated like asynchronous operations.

### Cause

Not every method inside an async service should be `async`.

Timestamp and password generation are local CPU/string operations. They do not wait on network or database I/O.

### Resolution

Keep them synchronous:

```python
timestamp = self.mpesa_timestamp()
password = self.daraja_password(timestamp)
```

Only await real async work:

```python
token = await self.get_access_token()

async with httpx.AsyncClient() as client:
    response = await client.post(...)
```

Generate one timestamp and use that same timestamp to construct its matching Daraja password.

### Prevention

Use `async` for operations that actually wait on asynchronous I/O.

---

## 12. STK Query timed out with `ReadTimeout`

### Error / symptom

An STK Query request produced an:

```text
httpx.ReadTimeout
```

### Cause

The outbound request was made, but the external API did not return a response within the HTTP client's timeout window.

This is a network/external-service failure mode, not necessarily a malformed-request error.

### Resolution

Use an explicit timeout and handle HTTPX exceptions:

```python
try:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            json=payload,
            headers=headers,
        )
except httpx.ReadTimeout:
    # Log the timeout and return/raise an appropriate app error.
    ...
```

### Prevention

Treat Daraja as an external network dependency. Use:

- bounded timeouts;
- exception handling;
- useful request/error logging;
- controlled retry/reconciliation where appropriate.

---

## 13. STK Query returned `500.001.1001 — The transaction does not Exist`

### Error / symptom

An STK Query returned:

```text
500.001.1001
The transaction does not Exist
```

A later query using the correct request identifier:

```text
ws_CO_200920261521213714531306
```

returned a successful result with `ResultCode: 0`.

### Cause

STK Query requires the exact `CheckoutRequestID` returned by the original STK Push.

It must not be confused with:

- `MerchantRequestID`;
- an internal database payment UUID;
- `MpesaReceiptNumber`;
- a manually constructed/altered identifier.

### Resolution

Persist the original `CheckoutRequestID` immediately after STK initiation and query with that exact value.

Example query body:

```json
{
  "BusinessShortCode": "...",
  "Password": "...",
  "Timestamp": "...",
  "CheckoutRequestID": "ws_CO_..."
}
```

The query also requires a fresh matching timestamp/password and valid OAuth bearer token.

### Prevention

Persist external identifiers as soon as Daraja returns them. Do not reconstruct identifiers later.

---

## 14. Payment remained `PENDING` despite callback implementation

### Error / symptom

An initiated payment remained:

```text
PENDING
```

instead of transitioning to the callback result.

After restarting FastAPI and repeating the transaction, PostgreSQL showed the expected successful update.

### Cause

The running FastAPI process had not picked up the latest callback/persistence implementation.

The source files had changed, but the active process was still serving the older application state.

### Resolution

Restart the FastAPI/Uvicorn server after structural route, service, dependency, or persistence changes when auto-reload has not applied them.

Then repeat the full flow:

```text
STK Push
   |
   v
INSERT payment as PENDING
   |
   v
Daraja callback
   |
   v
Find payment by CheckoutRequestID
   |
   v
UPDATE status/result fields
```

### Verified result

The working test produced data including:

```text
CheckoutRequestID: ws_CO_200920261521213714531306
MpesaReceiptNumber: TEST123456
Status: SUCCESS
ResultCode: 0
ResultDesc: The service request is processed successfully.
```

### Prevention

When behavior does not match recently edited code, confirm the server actually restarted/reloaded before debugging the logic further.

---

## 15. SQLAlchemy showed `ROLLBACK` after a successful insert

### Error / symptom

SQLAlchemy logs showed an `INSERT` and `COMMIT`, followed later by `ROLLBACK`, making it appear that the saved payment had been undone.

### Cause

The later rollback belonged to a different/subsequent transaction scope or session cleanup.

An already completed:

```text
COMMIT
```

is not reversed by a later rollback from another transaction.

### Resolution

Read transaction logs in sequence and verify the actual row in PostgreSQL.

Example:

```text
BEGIN
INSERT
COMMIT       <- payment persisted

BEGIN
SELECT
ROLLBACK     <- later transaction/session cleanup
```

### Prevention

Do not diagnose persistence solely from the presence of the word `ROLLBACK`. Identify which transaction it belongs to.

---

# Daraja Integration Lessons

## `ResponseCode = 0` is not final payment success

A successful STK Push initiation response means Safaricom accepted the request for processing. It does **not** prove that the customer completed payment.

The application should initially store:

```text
status = PENDING
```

The callback determines the final result:

```text
ResultCode = 0     -> SUCCESS
ResultCode != 0    -> FAILED / CANCELLED, depending on application mapping
```

---

## Callback is the primary completion path

The intended lifecycle is:

```text
Client
  |
  v
POST /payments/stk-push
  |
  v
Payment Service
  |
  +--> Daraja STK Push
  |
  +--> save MerchantRequestID + CheckoutRequestID
  |
  v
PENDING
  |
  | asynchronous callback
  v
POST /payments/callback
  |
  v
process_callback()
  |
  v
find row by CheckoutRequestID
  |
  v
update result
  |
  v
SUCCESS / FAILED
```

STK Query is useful for reconciliation and manual status checking. It should not replace correct callback processing.

---

## Callback metadata is not guaranteed on failed transactions

A successful callback may contain:

```python
payload["Body"]["stkCallback"]["CallbackMetadata"]
```

with values such as:

```text
Amount
MpesaReceiptNumber
TransactionDate
PhoneNumber
```

A failed/cancelled callback may not contain `CallbackMetadata`.

Therefore this is unsafe:

```python
metadata = callback["CallbackMetadata"]["Item"]
```

unless success/presence has already been checked.

Safer logic:

```python
callback = payload["Body"]["stkCallback"]

result_code = callback["ResultCode"]
result_desc = callback["ResultDesc"]

if result_code == 0:
    metadata = callback.get("CallbackMetadata", {}).get("Item", [])
    # Extract success metadata.
else:
    # Update the payment using ResultCode/ResultDesc.
    # Do not assume CallbackMetadata exists.
    ...
```

---

# Recommended Debugging Order

When the integration breaks, debug from the outside inward:

1. **Environment**
   - Is the correct `.venv` active?
   - Does `python -m pip --version` point into `.venv`?
   - Are required dependencies installed?

2. **Configuration**
   - Did Pydantic load `.env`?
   - Are settings field names correct?
   - Is code using `settings.<field>` consistently?

3. **FastAPI routing**
   - Is the route visible in `/docs`?
   - Is the router prefix applied exactly once?

4. **Public callback URL**
   - Is the tunnel active?
   - Is the URL HTTPS?
   - Does it end at the real callback route?

5. **Daraja request**
   - Is the OAuth token valid?
   - Is timestamp/password generated correctly?
   - Is the correct shortcode being used?
   - Is `CheckoutRequestID` the exact value returned by STK Push?

6. **Async correctness**
   - Is `AsyncClient` opened using `async with`?
   - Are async methods awaited?
   - Are synchronous helpers left synchronous?

7. **Persistence**
   - Was the `PENDING` row committed?
   - Was `CheckoutRequestID` stored?
   - Does callback lookup use `CheckoutRequestID`?
   - Does callback processing commit the update?

8. **External API behavior**
   - Check Daraja's response body before changing application code.
   - Distinguish malformed-request errors from timeouts/transient failures.

---

# Useful Verification Commands

## Confirm Python and pip

```powershell
where.exe python
where.exe pip
python -m pip --version
```

The important result is that `python` and `python -m pip` resolve to the project virtual environment.

## Inspect installed dependencies

```powershell
python -m pip list
```

## Run FastAPI with reload during development

```powershell
uvicorn app.main:app --reload
```

Use the actual import path used by the project if different.

## Verify registered API routes

Open:

```text
/docs
```

and confirm the expected endpoints exist, especially:

```text
POST /payments/stk-push
POST /payments/callback
POST /payments/stk-query
```

---

# Error Log Maintenance Rule

Whenever a new integration error is solved, add an entry using this template:

```markdown
## N. Short error name

### Error / symptom

Exact error message or observed behavior.

### Cause

What actually caused it.

### Resolution

The fix that worked.

### Prevention

What to check or do differently next time.
```

Prefer the **actual root cause discovered in this project** over a generic list of possible causes.

---

## Current confirmed working milestone

As of the successful test on **2026-09-20**, the integration had demonstrated:

```text
STK Push request
    -> payment persisted as PENDING
    -> Daraja callback received
    -> payment located using CheckoutRequestID
    -> callback data persisted
    -> status updated to SUCCESS
```

Verified successful test data included:

```text
CheckoutRequestID: ws_CO_200920261521213714531306
MpesaReceiptNumber: TEST123456
ResultCode: 0
Status: SUCCESS
ResultDesc: The service request is processed successfully.
```

This is the baseline to compare against when later changes break the payment flow.
