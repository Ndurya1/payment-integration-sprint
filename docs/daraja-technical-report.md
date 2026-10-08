SAFARICOM DARAJA API
TECHNICAL REPORT: PLATFORM, INTEGRATION AND ENGINEERING PRACTICE
A practical guide to Safaricom and M-PESA API integration for web and Android applications
Course: SOEN 255 API DESIGN AND IMPLEMENTATION
Prepared by
MOSES THOMAS MUTINDA — IN16/00030/24
FANCY NATEKU MEGIRI — IN16/00060/24
NDURYA MUHAMMAD — IN16/00142/24
KIPTOO BRIAN — IN16/00054/24
ORESI CRISPUS — IN16/00095/24
CECILIA KIIRU — IN16/00003/24
MOHAMED KHAMISI MOHAMED — IN16/00132/24
ABISHAI KYALO - IN16/00036/24
KISII UNIVERSITY  
School of Information Science and Technology  
Department of Computing
Date: 7 October 2026
Abstract
Safaricom Daraja is the developer platform through which web and mobile applications can access Safaricom and M-PESA services. This report explains the platform’s API model and major service families, then develops a practical engineering view of authentication, payment initiation, asynchronous callbacks, Android-to-backend communication, testing, security, reliability and production readiness. M-PESA Express (also called Lipa na M-PESA Online or STK Push) is used as the main integration example because it demonstrates the central design challenge: a payment request is submitted synchronously, while the customer’s final decision is reported later. The report emphasizes that secrets belong on a protected backend and that an accepted request is not proof of payment. It is intended as a technically useful foundation for a student team and as a guide to the official product documentation, which developers must re-check because endpoints, test data and onboarding requirements can change. [1] [2] [3] [4]
1. Introduction and purpose
Modern applications often need to collect mobile-money payments, make business disbursements, or reconcile transaction records. Daraja provides documented HTTP APIs that allow an authorized system to request these services rather than implementing a direct connection to the M-PESA core. Safaricom describes Daraja 3.0 as a platform that bridges Safaricom and M-PESA APIs with web and mobile applications. [1]
The purpose of this report is to give software engineers a working mental model of Daraja, explain a secure implementation architecture, and identify the operational details that commonly determine whether an integration is reliable. The examples focus on Kenya and sandbox development. They are not a substitute for the current product-specific Safaricom API specification or business approval for live transactions.
By the end, a developer should be able to distinguish application authentication from transaction authorization, design the Android/backend boundary, submit an STK Push, process the eventual result safely, test failure cases, and prepare for a production review.
2. Daraja platform and API concepts
Daraja is both a developer portal and an API gateway. The portal supports developer registration, application setup, product discovery, testing and live onboarding. The APIs use HTTP methods such as GET and POST and exchange JSON request and response data. Integrations can be tested using the portal’s simulator, API clients such as Postman, or a backend written in a supported language. [1] [2]
Term	Engineering meaning
API	A defined interface through which one software system requests a service from another.
Daraja application	A portal-managed app configuration with credentials and selected API products.
Consumer Key / Consumer Secret	Application credentials exchanged for a short-lived access token; secrets must remain server-side.
Access token	A time-limited bearer credential attached to permitted API calls.
Short code	The PayBill, Till or other business identifier used by a product’s transaction flow.
Callback	An HTTP notification delivered later by Safaricom after asynchronous processing.
Sandbox	A controlled development environment for simulated requests and test credentials; it is separate from production.
Idempotency	A design property that makes repeat processing of the same event safe and prevents duplicate business effects.
3. API families and common use cases
Daraja groups products under areas such as Security, Payments, Disbursement and Experience. Product availability and requirements are specific to each app and business arrangement, so the portal’s current catalogue is authoritative. The following are representative API families rather than a claim that every account has access to every product. [1] [7]
API family	Typical purpose	Typical integration concern
Authorization	Obtain an OAuth access token before calling protected APIs.	Protect consumer credentials and manage token lifetime.
M-PESA Express / STK Push	Ask a customer’s phone to present an M-PESA payment prompt.	Asynchronous customer decision and callback correlation.
C2B	Receive customer-initiated payments to a business PayBill or Till.	Register and maintain validation/confirmation URLs where supported.
B2C	Send business-to-customer disbursements, such as supported salary or promotion payments.	Business permissions, encrypted security credentials and result callbacks.
B2B	Support defined business-to-business payment use cases.	Command-specific account eligibility and operational controls.
Transaction status / reversal / account balance	Query or act on eligible transactions and business account information. [6]	Asynchronous results, unique request identifiers and strict authorization.
Dynamic QR / Pull Transactions	Support QR-led payment initiation or transaction retrieval/reconciliation use cases.	Product-specific data formats, access and reconciliation rules.
The STK Push route is merchant-initiated: the business asks M-PESA to prompt a customer. C2B is generally customer-initiated: the customer pays through an M-PESA menu or supported flow. These patterns are not interchangeable, and the chosen product determines which business shortcode, permissions, callbacks and test setup are required. [4] [5]
4. Integration architecture
A production-style mobile integration has three trust zones: the customer-facing application, the organization’s backend, and Safaricom’s Daraja/M-PESA services. The Android app collects inputs and displays status. The backend authenticates to Daraja, validates business rules, submits API requests, receives callbacks, persists payment state and exposes a safe status endpoint to the app.
Flow:
```text
Customer Android app → Organization backend → Daraja / M-PESA
                           ↑                    │
                           └──── callback ──────┘

Android app ← backend payment status / order state
```
The app must not call Daraja using the Consumer Secret or Passkey. An Android package can be inspected, so embedding secrets in source code, resources or compiled assets does not protect them. Backend mediation is a security boundary, not merely an architectural preference.
The backend should create or locate an order before payment initiation. It should associate that order with a unique internal reference and, after Daraja returns identifiers, store at least the MerchantRequestID and CheckoutRequestID against the pending order. The callback can then be joined to the correct order even if the customer closes the app or loses connectivity.
5. Getting started: account, app and environments
A sensible development sequence is:
Create or sign in to a Daraja developer account and review the current Getting Started and product documentation.
Create a sandbox application and enable the API product required by the project.
Use the sandbox credentials and product-specific test data supplied through the portal. Do not rely on stale credentials copied from tutorials.
Implement and test a backend endpoint locally, then make callback routes reachable to the sandbox using a method permitted by current Safaricom guidance.
Test success, cancellation, validation errors, timeouts and callback delivery before considering production onboarding.
For live use, complete the product-specific Go Live process, confirm business-account eligibility and configure production credentials and callback URLs separately. [2] [5]
Sandbox and production must have separate configuration, credentials, data stores or clear environment separation, callback endpoints, and monitoring. A sandbox success is not authorization to process real money. Safaricom’s Getting Started guide describes business account and M-PESA portal access as part of its live requirements; the exact requirements depend on the selected product and organization. [2]
6. Authentication and credentials
The Authorization API documents OAuth 2.0 client credentials. The backend sends a GET request to the environment’s token endpoint with HTTP Basic authentication constructed from the Consumer Key and Consumer Secret, and the query parameter `grant_type=client_credentials`. The sandbox route is shown below. The response contains an `access_token` and `expires_in`; Safaricom currently documents a lifetime of approximately 3,600 seconds. Subsequent protected requests send the token as `Authorization: Bearer <token>`. [3]
```text
GET https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials
Authorization: Basic base64(CONSUMER_KEY:CONSUMER_SECRET)
Response: { "access_token": "…", "expires_in": 3599 }
```
Cache the access token on the backend and refresh it shortly before expiry rather than fetching a new token for every transaction. Safaricom’s current Authorization guide notes that token requests may invalidate the previous token, which makes uncontrolled token generation especially undesirable. Do not log authorization headers or return credentials to the Android client. [3]
Some disbursement and administrative APIs require an additional SecurityCredential generated by encrypting an initiator password with the correct Safaricom public certificate. The sandbox and production certificates differ. Follow that API’s current instructions exactly; do not assume the STK Push password procedure applies to every API. [2]
7. M-PESA Express (STK Push): end-to-end flow
STK Push, also known as Lipa na M-PESA Online, asks M-PESA to present a payment prompt on the customer’s phone. The customer checks the request and enters the M-PESA PIN within the M-PESA prompt. The merchant application must never request or store the customer’s PIN. The API returns an initial acknowledgement and identifiers; Safaricom later sends the final result to the callback URL. [4]
The customer selects Pay and the Android app sends the order identifier, phone number and other permitted user input to the organization’s backend over HTTPS.
The backend authenticates the caller, verifies the order amount and status, normalizes the phone number, and obtains a valid Daraja access token.
The backend generates the request timestamp and STK password, then submits the documented JSON payload to the M-PESA Express endpoint.
If the request is accepted, the backend stores the returned request IDs and marks the order PENDING. It tells the app only that the prompt was initiated.
The customer approves, cancels or does not complete the prompt. Safaricom sends a callback containing the result.
The backend validates the expected callback structure, correlates the checkout request to the pending order, records the terminal outcome once, and makes the status available to the app.
The sandbox endpoint documented by Safaricom is `POST https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest`. The production host and configuration must be taken from the current live product documentation. The request includes a `BusinessShortCode`, `Password`, `Timestamp`, `TransactionType`, `Amount`, `PartyA`, `PartyB`, `PhoneNumber`, `CallBackURL`, `AccountReference` and optionally `TransactionDesc`. The STK password is `Base64(Shortcode + Passkey + Timestamp)`. For the documented PayBill example, `TransactionType` is `CustomerPayBillOnline`; a Till flow may use `CustomerBuyGoodsOnline` and can use different PartyB/shortcode values. [4]
Safaricom’s current M-PESA Express reference describes `AccountReference` as limited to 12 characters and `TransactionDesc` as limited to 13 characters. Validate such limits on the backend and confirm the product’s live specification before deployment. A sample acceptance response with `ResponseCode 0` means the request was accepted for processing; it does not establish that money was received. The final callback’s `ResultCode` is the relevant outcome, and successful callbacks may include amount, M-PESA receipt number, transaction time and phone number. [4]
8. Node.js backend implementation pattern
Node.js can implement a small Express service with separate routes for payment initiation, callbacks and status retrieval. Node’s built-in fetch is available in modern Node releases; an HTTP client library may also be used. Keep configuration in protected environment variables or a secrets manager, exclude local `.env` files from version control, and never place real secrets in source code, screenshots, logs or submitted coursework.
A compact backend design would expose `POST /api/orders/{id}/payment` to start payment, `POST /api/daraja/callback` to receive the callback, and `GET /api/orders/{id}/payment` to let an authenticated app retrieve status. The app should not be allowed to choose an arbitrary amount for an existing order: the backend should load the expected amount from trusted order data.
The essential STK request construction can be expressed as follows. This is illustrative integration logic, not a complete production server; real implementations also need authorization, persistence, validation, monitoring, retry controls and callback processing.
9. Android application integration
The Android client needs only the organization’s backend base URL and a narrow application API. For example, it can submit an order ID and phone number, then show a pending state while it refreshes an authenticated status endpoint or receives a suitable server-driven update. The UI should distinguish ‘request sent’, ‘waiting for customer’, ‘paid’, ‘cancelled/failed’ and ‘status unknown’ rather than collapsing them into a single success message.
Android’s official networking guide requires the INTERNET manifest permission for network access, recommends secure network communication, and warns against running network operations on the main UI thread. A repository plus Retrofit or another supported HTTP client and Kotlin coroutines is a common maintainable structure. [8]
```xml
<uses-permission android:name="android.permission.INTERNET" />
```
```kotlin
interface PaymentService {
    @POST("api/orders/{id}/payment")
    suspend fun startPayment(
        @Path("id") orderId: String,
        @Body request: StartPaymentRequest
    ): StartPaymentResponse
}
```
During Android Emulator development, Android documents `10.0.2.2` as the special alias to the development computer’s loopback interface. It is not a production address and does not apply unchanged to a physical phone. Use HTTPS for deployed services; if temporary cleartext is enabled to test a local HTTP backend, confine that setting to a development build and remove it for release. [9] [8]
10. Callback processing and transaction state
Callbacks are essential because many M-PESA operations are asynchronous. Safaricom’s Getting Started guide says the organization must run an HTTP listener for responses. Its guide warns that if the server is unavailable, a callback may not be delivered; developers therefore need an operationally reliable endpoint and a reconciliation plan. [2]
For STK Push, the callback is commonly shaped as `Body.stkCallback` and includes `MerchantRequestID`, `CheckoutRequestID`, `ResultCode` and `ResultDesc`. A successful result can include `CallbackMetadata` items. Do not assume metadata exists for a failed/cancelled request. Store the original request identifiers and correlate them to the callback rather than trusting a customer-supplied reference alone. [4]
A robust order lifecycle might use `CREATED → PAYMENT_PENDING → PAID` or `PAYMENT_FAILED`, with a separate `UNKNOWN/RECONCILIATION_REQUIRED` state for ambiguous delivery. A valid `ResultCode` of zero can transition a pending payment to paid only after the callback has been associated with the correct order and checked against expected business conditions. A late or duplicate callback should not create a second fulfilment, refund, receipt or accounting entry.
Implement idempotency with a database uniqueness constraint or processed-event record keyed by a stable Daraja transaction identifier. Commit the payment status and any fulfilment event atomically where practical, or use a transactional outbox. Acknowledge callbacks promptly after durable receipt; move slow work to a queue. Retain a safe copy of callback data for troubleshooting while minimizing personal and payment data.
11. Security, privacy and data protection
Keep Consumer Secrets, Passkeys, initiator passwords, SecurityCredentials and access tokens on the server. Restrict access, rotate exposed credentials, and use a managed secret store in production.
Use HTTPS/TLS between the Android app and backend and for public production callback endpoints. Safaricom’s FAQs specify publicly accessible URLs and HTTPS for production callback URLs. [5] [8]
Validate all user input and order authorization on the backend. Apply server-side amount limits, phone normalization, rate limits, CSRF protections where relevant, and abuse monitoring.
Treat the callback as an external input. Check its structure, identifiers and expected transaction state. Use Safaricom’s current callback/IP-whitelisting guidance where network controls require it, and do not treat source IP alone as a substitute for application-level validation. [2]
Do not collect an M-PESA PIN in the application. The customer authorizes the payment through the M-PESA prompt. Avoid logging tokens, passkeys, full phone numbers or unnecessary personal data.
Store only the data needed for transaction operations, accounting and legal obligations. Define retention, access controls, backups and audit logging consistent with applicable law and organizational policy.
Separate test and production networks, configuration and credentials. Do not test live credentials on an unauthenticated public development tunnel.
Safaricom’s portal FAQ cautions that callback URL requirements matter and that production URL registration may be difficult to change. Confirm URL names, TLS, reachability, firewall rules and ownership before registering a live URL. Sandbox callback techniques can differ from production policy; use the current Safaricom guidance rather than assuming every public tunnel is suitable. [5]
12. Reliability, errors and troubleshooting
Troubleshooting should inspect the environment, API product permissions, HTTP method, Content-Type, token validity, request fields, shortcode, transaction type, callback reachability and server logs. Safaricom’s M-PESA Express reference lists errors for invalid request fields, invalid access tokens, wrong endpoint or method, merchant configuration, rate limits and temporary server problems. [4]
Symptom	Checks and response
Invalid/expired token	Confirm correct app credentials and environment; fetch a fresh token and check Bearer header.
Bad request / invalid field	Check exact JSON property names, required fields, content type, phone format, shortcode and field-length limits.
Method or endpoint error	Use the documented HTTP verb and current endpoint for the selected product and environment.
No callback	Verify public reachability, HTTPS in production, route method/path, server health and firewall; reconcile unresolved payments.
Duplicate or conflicting request	Use internal idempotency and order locks; avoid resubmitting blindly when the result is ambiguous.
Throttle/quota or busy response	Apply bounded backoff where the API supports retry, avoid retrying non-idempotent payment requests blindly, and respect product limits.
Use structured logs with correlation identifiers such as internal order ID and Daraja request IDs, but redact secrets and minimize customer data. Track token-refresh failures, API latency, initial submission outcomes, callback volume, callback processing lag and unresolved pending transactions. A user-facing timeout should not automatically be reported as payment failure: the backend may need to query status or reconcile through the available operational channel.
13. Testing strategy
Testing should exercise both request submission and final transaction outcomes. Use Safaricom-provided sandbox test data and the simulator documented for the product. A local callback requires a publicly reachable development endpoint; tunnels are for controlled sandbox testing only and should not be used to expose live credentials or production data. [2] [5]
Successful STK request and successful callback, including receipt metadata.
Customer cancellation, timeout or failure result where the simulator supports it.
Missing, malformed and out-of-range fields, including phone, amount, reference and description.
Expired/invalid token, incorrect environment configuration, invalid shortcode and malformed callback payload.
Callback arriving before the app polls, delayed callback, duplicate callback and callback after a retry.
Backend restart, database outage, network interruption and app process death while payment is pending.
Security tests for unauthorized order IDs, altered amount, repeated start-payment requests and secret leakage in logs or APK contents.
A useful automated test separates unit tests for validation and state transitions, integration tests against sandbox or a mock Daraja adapter, and end-to-end checks using the official simulator. Use a deterministic fake callback for repeat-delivery tests. Test that the same success callback twice fulfils an order only once and that a failure callback never marks it paid.
14. Sandbox-to-production readiness
Production readiness is not a matter of replacing the sandbox hostname. The organization must have the appropriate live M-PESA business setup and permissions, complete the Daraja Go Live process for the chosen API, configure production credentials and certificates where applicable, and verify callback configuration. Safaricom lists M-PESA account and portal administrator/business-manager access among live prerequisites; details vary by product and entity. [2]
Obtain written business approval for the product, shortcode, payment flow, settlement and support ownership.
Complete the Daraja live application and product onboarding steps and obtain production credentials through authorized channels.
Configure secrets in a production secret manager; confirm production endpoint, shortcode, Passkey and certificate match the environment.
Deploy a stable HTTPS backend with monitoring, backups, least-privilege access, firewall controls and a tested recovery plan.
Verify callback delivery and transaction reconciliation in an approved pre-production plan; confirm escalation and support contacts.
Set transaction limits, fraud controls, rate limits, alerting and financial reconciliation before accepting customer payments.
Do not use production transactions for coursework demonstrations unless the institution and business account owner have explicitly authorized the integration. Keep live credentials out of academic reports and source repositories.
15. Engineer’s implementation checklist
Product chosen from the current Daraja catalogue; product-specific documentation reviewed.
Sandbox app, credentials, test data and callback route configured without exposing secrets.
Android app calls only the business backend; all Daraja authentication occurs server-side.
Backend loads price and order state from trusted data and validates phone, amount and access rights.
Access token is cached safely and renewed before expiry; logs redact credentials.
STK submission response is treated as pending, not paid.
Callback is correlated by Daraja request ID, persisted, processed idempotently and reconciled if missing.
UI clearly distinguishes pending, success, failure and unknown outcomes.
Tests cover errors, delays, duplicate notifications, app/network interruption and security boundaries.
Production go-live, HTTPS callback, monitoring, business authorization and reconciliation are complete before live use.
Conclusion
Safaricom Daraja provides a documented path for web and mobile systems to use M-PESA services, but a successful integration depends on more than a correct HTTP request. Engineers must select the right API product, protect credentials on a backend, understand each API’s business prerequisites, and handle transaction outcomes that arrive asynchronously. STK Push makes this especially clear: request acceptance only starts the payment flow; the verified and correlated callback determines the final result. A disciplined sandbox workflow, secure Android/backend separation, idempotent callback handling, meaningful failure tests and product-specific production onboarding form the foundation of a dependable implementation. Developers should consult the live Daraja portal before coding or going live because the official product documentation is the source of truth for current endpoints, parameters, limits and onboarding rules. [1] [2] [3] [4]
Appendix A. Compact Node.js request example
This illustration shows token acquisition and STK payload construction for sandbox use. Store the values referenced through `process.env` in protected configuration. Use the exact values and product instructions associated with the Daraja app; never copy secrets into this report or an Android project.
```javascript
const base = process.env.DARAJA_BASE_URL; // sandbox while testing
const basic = Buffer.from(
  `${process.env.DARAJA_CONSUMER_KEY}:${process.env.DARAJA_CONSUMER_SECRET}`
).toString("base64");

const auth = await fetch(
  `${base}/oauth/v1/generate?grant_type=client_credentials`,
  {
    headers: {
      Authorization: `Basic ${basic}`
    }
  }
);

if (!auth.ok) throw new Error("Token request failed");

const { access_token: token } = await auth.json();

const timestamp = getNairobiTimestamp(); // YYYYMMDDHHmmss
const shortcode = process.env.DARAJA_SHORTCODE;

const password = Buffer.from(
  `${shortcode}${process.env.DARAJA_PASSKEY}${timestamp}`
).toString("base64");

const payload = {
  BusinessShortCode: shortcode,
  Password: password,
  Timestamp: timestamp,
  TransactionType: "CustomerPayBillOnline",
  Amount: trustedOrder.amount,
  PartyA: normalizedPhone,
  PartyB: shortcode,
  PhoneNumber: normalizedPhone,
  CallBackURL: process.env.DARAJA_CALLBACK_URL,
  AccountReference: trustedOrder.reference,
  TransactionDesc: "Order payment"
};

const response = await fetch(
  `${base}/mpesa/stkpush/v1/processrequest`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  }
);

const result = await response.json();

if (!response.ok) throw new Error("STK Push request failed");

// Persist request IDs. Keep the order PENDING until a valid callback is processed.
```
In a complete application, `getNairobiTimestamp` should return a correctly formatted timestamp in the timezone and format required by the API. Persist the initial response identifiers. The callback handler must parse the documented callback structure, locate the associated pending order, commit the result idempotently and acknowledge the request according to Safaricom’s current callback instructions. [4]
References
[1] Safaricom Daraja Developer Portal
[2] Safaricom, Getting Started (M-PESA APIs)
[3] Safaricom, Authorization API
[4] Safaricom, M-PESA Express (STK Push) API
[5] Safaricom Daraja Developer Portal, Frequently Asked Questions
[6] Safaricom, Account Balance API
[7] Safaricom Daraja APIs catalogue
[8] Android Developers, Connect to the network
[9] Android Developers, Network address space (Android Emulator)