# Payment Integration Lab

A backend learning project for implementing and understanding **Safaricom Daraja M-Pesa payment integration** using **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **HTTPX**.

The project is being built incrementally so that each part of the M-Pesa payment lifecycle is understood before moving to the next integration feature.

> **Current scope:** Milestones M1–M4.

---

## Project Goal

The goal of this project is not just to make an STK Push work.

It is to understand the complete backend flow involved in integrating an external payment provider:

```text
Client
   |
   v
FastAPI API
   |
   v
Payment Service
   |
   +------> Safaricom Daraja API
   |
   v
PostgreSQL
```

The project currently focuses on **Lipa na M-Pesa Online (STK Push)** and the surrounding backend responsibilities:

- Daraja OAuth authentication
- STK Push initiation
- payment persistence
- public callback handling
- transaction status updates
- STK Query
- asynchronous HTTP requests
- external payment identifiers
- error handling and debugging

---

# Tech Stack

| Component | Technology |
|---|---|
| API framework | FastAPI |
| Language | Python |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| PostgreSQL driver | asyncpg |
| HTTP client | HTTPX |
| Validation | Pydantic |
| Configuration | pydantic-settings |
| Payment API | Safaricom Daraja |
| Local callback exposure | ngrok / HTTPS tunnel |

---

# Payment Flow

The current integration follows this lifecycle:

```text
                    +----------------------+
                    |        Client        |
                    +----------+-----------+
                               |
                               | POST /payments/stk-push
                               v
                    +----------------------+
                    |       FastAPI        |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   Payment Service    |
                    +----------+-----------+
                               |
                     Get OAuth Access Token
                               |
                               v
                    +----------------------+
                    |   Safaricom Daraja   |
                    +----------+-----------+
                               |
                           STK Push
                               |
                               v
                       Customer Phone
                               |
                               | PIN / response
                               v
                    +----------------------+
                    |   Safaricom Daraja   |
                    +----------+-----------+
                               |
                         Async Callback
                               |
                               v
                    POST /payments/callback
                               |
                               v
                    +----------------------+
                    |   Payment Service    |
                    +----------+-----------+
                               |
                     Find CheckoutRequestID
                               |
                               v
                    +----------------------+
                    |      PostgreSQL      |
                    +----------------------+
                               |
                        Update payment
                               |
                      +--------+--------+
                      |                 |
                   SUCCESS            FAILED
```

---

# Milestones

## M1 — Project Foundation

The first milestone established the backend application and development environment.

### Completed

- FastAPI project initialization
- Python virtual environment
- dependency installation
- environment-variable configuration
- PostgreSQL connection
- SQLAlchemy setup
- async database sessions
- basic payment module structure

The project separates responsibilities between routes, schemas, services, models, and database configuration.

A simplified structure looks like:

```text
server/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── database/
│   │   └── database.py
│   │
│   └── payments/
│       ├── models.py
│       ├── schemas.py
│       ├── routes.py
│       └── service.py
│
├── docs/
│   └── errors.md
│
├── .env
└── requirements.txt
```

> The exact directory structure may evolve as the project grows.

---

## M2 — Daraja Authentication

The second milestone implemented authentication with the Safaricom Daraja API.

Daraja requires an OAuth access token before protected payment endpoints can be called.

### Authentication flow

```text
Consumer Key + Consumer Secret
              |
              v
      Base64 / Basic Auth
              |
              v
     Daraja OAuth Endpoint
              |
              v
        Access Token
              |
              v
Authorization: Bearer <token>
```

The access token is then used by subsequent Daraja requests.

### Key lesson

External API credentials are configuration and should not be hardcoded into service logic.

They are loaded from environment variables through the application's settings layer.

Example configuration:

```env
DARAJA_CONSUMER_KEY=...
DARAJA_CONSUMER_SECRET=...
DARAJA_SHORTCODE=...
DARAJA_PASSKEY=...
DARAJA_CALLBACK_URL=...
```

The `.env` file must not be committed.

---

## M3 — STK Push

Milestone three implemented **Lipa na M-Pesa Online / STK Push**.

The API receives payment information from a client and asks Daraja to initiate an STK request on the customer's phone.

### Endpoint

```http
POST /payments/stk-push
```

### Example request

```json
{
  "phone_number": "2547XXXXXXXX",
  "amount": 1,
  "account_reference": "test-009",
  "transaction_desc": "Payment test"
}
```

The service:

1. validates the request;
2. retrieves a Daraja OAuth token;
3. generates the M-Pesa timestamp;
4. generates the Daraja password;
5. builds the STK Push payload;
6. sends the request to Daraja;
7. receives `MerchantRequestID` and `CheckoutRequestID`;
8. stores the payment locally as `PENDING`.

### Important distinction

A successful STK Push initiation does **not** mean that money has been paid.

For example:

```text
ResponseCode = 0
```

means the request was successfully accepted for processing.

Therefore the local transaction begins as:

```text
PENDING
```

and waits for the asynchronous callback.

---

# Payment Persistence

An initiated transaction is stored before its final payment result is known.

The payment record currently captures information such as:

```text
id
phone_number
amount
account_reference
merchant_request_id
checkout_request_id
mpesa_receipt_number
status
result_code
result_desc
created_at
updated_at
```

The most important external identifier during the STK lifecycle is:

```text
CheckoutRequestID
```

It links:

```text
STK Push
   |
   v
local payment row
   |
   v
Daraja callback
   |
   v
STK Query
```

---

## M4 — Callback Handling and Transaction Status

Milestone four completed the asynchronous side of the STK Push lifecycle.

After the customer interacts with the M-Pesa prompt, Safaricom sends the result to the application's callback URL.

### Endpoint

```http
POST /payments/callback
```

Because Safaricom cannot reach:

```text
localhost
```

during local development, FastAPI must be exposed through a public HTTPS tunnel.

Example:

```text
https://<public-tunnel>/payments/callback
```

That URL is supplied to Daraja as:

```text
CallBackURL
```

---

# Callback Processing

The callback handler extracts:

```text
MerchantRequestID
CheckoutRequestID
ResultCode
ResultDesc
```

The application then locates the existing payment using:

```text
CheckoutRequestID
```

and updates its state.

### Successful payment

When:

```text
ResultCode = 0
```

the callback can contain metadata such as:

```text
Amount
MpesaReceiptNumber
TransactionDate
PhoneNumber
```

The payment becomes:

```text
SUCCESS
```

### Unsuccessful payment

When:

```text
ResultCode != 0
```

the transaction is mapped to an unsuccessful state such as:

```text
FAILED
```

or another application-specific state where appropriate.

Failed callbacks may not contain `CallbackMetadata`, so callback parsing must not assume that metadata is always present.

---

# Confirmed End-to-End Result

The M4 flow has been successfully tested.

A transaction moved through:

```text
STK Push
    |
    v
PENDING
    |
    v
Daraja Callback
    |
    v
SUCCESS
```

One successful test produced:

```text
CheckoutRequestID:
ws_CO_200920261521213714531306

MpesaReceiptNumber:
TEST123456

ResultCode:
0

Status:
SUCCESS

ResultDesc:
The service request is processed successfully.
```

This confirms that the application can:

- initiate an STK Push;
- persist the initial transaction;
- receive the asynchronous callback;
- locate the correct transaction;
- persist callback information;
- update the final transaction state.

---

# STK Query

The project also includes work on the Daraja **STK Query** endpoint.

STK Query allows the backend to ask Safaricom for the status of an STK transaction.

Conceptually:

```text
Application
    |
    | CheckoutRequestID
    v
Daraja STK Query
    |
    v
Transaction Status
```

The query requires:

```text
BusinessShortCode
Password
Timestamp
CheckoutRequestID
```

along with a valid OAuth bearer token.

### Important

The exact `CheckoutRequestID` returned by the original STK Push must be used.

Do not substitute:

```text
MerchantRequestID
internal payment UUID
MpesaReceiptNumber
```

for `CheckoutRequestID`.

STK Query is useful for reconciliation or explicit status checks, but the callback remains the primary completion mechanism for the normal STK Push flow.

---

# Async HTTP Design

Daraja calls are network I/O, so the integration uses HTTPX's asynchronous client.

Correct pattern:

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        url,
        json=payload,
        headers=headers,
    )
```

Async operations include network calls such as:

```python
token = await get_access_token()
```

Local helpers such as timestamp and password generation remain synchronous:

```python
timestamp = mpesa_timestamp()
password = daraja_password(timestamp)
```

---

# Environment Setup

## 1. Clone the repository

```bash
git clone <repository-url>
cd payment-intergration-lab/server
```

## 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

## 3. Verify Python and pip

```powershell
where.exe python
python -m pip --version
```

Both should resolve to the virtual environment.

If `pip` is missing:

```powershell
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

## 4. Install dependencies

If the repository has a requirements file:

```powershell
python -m pip install -r requirements.txt
```

Core dependencies include:

```text
fastapi
uvicorn
sqlalchemy
asyncpg
greenlet
httpx
pydantic
pydantic-settings
```

## 5. Configure environment variables

Create:

```text
.env
```

and configure the required application, database, and Daraja values.

Example:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/DATABASE

DARAJA_CONSUMER_KEY=your_consumer_key
DARAJA_CONSUMER_SECRET=your_consumer_secret
DARAJA_SHORTCODE=your_shortcode
DARAJA_PASSKEY=your_passkey
DARAJA_CALLBACK_URL=https://your-public-url/payments/callback
```

Never commit real secrets.

## 6. Start PostgreSQL

Ensure the configured database exists and PostgreSQL is running.

## 7. Start FastAPI

```powershell
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

to inspect and test the API.

---

# Local Callback Development

Daraja callbacks require a public HTTPS endpoint.

Start FastAPI locally, then expose its port using the tunnel configured for the project.

The resulting public callback should point to:

```text
/payments/callback
```

For example:

```text
https://<tunnel-host>/payments/callback
```

Whenever the tunnel URL changes, update the configured Daraja callback URL before initiating another STK Push.

---

# API Summary

Current payment endpoints through M4 include:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/payments/stk-push` | Initiate an M-Pesa STK Push |
| `POST` | `/payments/callback` | Receive the asynchronous Daraja result |
| `POST` | `/payments/stk-query` | Query the status of an STK transaction |

Endpoint names may be refined as the API evolves.

---

# Transaction State

The central state transition currently looks like:

```text
             STK initiated
                  |
                  v
               PENDING
                  |
             callback received
             /             \
            /               \
           v                 v
       SUCCESS             FAILED
```

The database—not the immediate STK Push response—is the application's durable record of the payment lifecycle.

---

# Error Handling

External payment integrations can fail at several boundaries:

```text
Configuration
     |
Authentication
     |
Network
     |
Daraja validation
     |
Callback delivery
     |
Database persistence
```

Known errors encountered during development, their causes, and their resolutions are documented separately in:

```text
docs/errors.md
```

That file should remain a living troubleshooting reference as new integration cases are discovered.

---

# Key Lessons So Far

### 1. Payment initiation and payment completion are separate events

An accepted STK request is not proof of payment.

### 2. External IDs must be persisted

`CheckoutRequestID` is essential for correlating callbacks and queries with the local transaction.

### 3. Callbacks are asynchronous

The initial HTTP request cannot wait for the customer to complete the entire payment lifecycle.

### 4. External APIs require defensive handling

Timeouts, invalid requests, missing callback metadata, and external API errors are normal integration concerns.

### 5. Async must be consistent

An async FastAPI service should use asynchronous network/database operations correctly rather than mixing synchronous and asynchronous clients.

### 6. Database state is the source of truth for the application

The application persists the lifecycle:

```text
PENDING -> SUCCESS / FAILED
```

rather than relying only on transient API responses.

---

# Documentation

```text
docs/
├── errors.md       # Errors encountered, causes, fixes and debugging notes
└── ...
```

As the integration progresses, additional documentation can cover API contracts, payment lifecycle decisions, security considerations, and later milestones.

---

# Current Status

**Completed through M4.**

```text
[✓] FastAPI project setup
[✓] PostgreSQL + async SQLAlchemy
[✓] Daraja configuration
[✓] OAuth access token
[✓] STK Push
[✓] Persist initiated payment
[✓] Public callback endpoint
[✓] Callback processing
[✓] Payment status update
[✓] Successful end-to-end callback persistence
[✓] STK Query implementation/testing
```

The current baseline is a functioning backend STK Push lifecycle from initiation through callback-based persistence.

---

## Development Note

This repository is a learning/integration lab. Sandbox credentials and test transactions should be used while developing against Safaricom's sandbox environment.

Real credentials, passkeys, database passwords, access tokens, and other secrets must never be committed to source control.

Don't worry, your sandbox shillings are reversed  some minutes after making the stk push. sometimes the callback delays, query safaricom with the checkout_request_id to get the final status. 
