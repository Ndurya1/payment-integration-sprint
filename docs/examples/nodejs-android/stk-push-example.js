
/**
 * Safaricom Daraja STK Push - Node.js Reference Example
 *
 * Based on Appendix A of the Daraja Technical Report.
 *
 * This example demonstrates:
 * 1. OAuth access-token acquisition
 * 2. STK password generation
 * 3. STK Push payload construction
 * 4. STK Push request submission
 *
 * This is an educational reference implementation.
 * It is NOT a complete production payment server.
 *
 * Requires:
 *   Node.js 18+
 *
 * Environment variables:
 *
 * DARAJA_BASE_URL=https://sandbox.safaricom.co.ke
 * DARAJA_CONSUMER_KEY=your_consumer_key
 * DARAJA_CONSUMER_SECRET=your_consumer_secret
 * DARAJA_SHORTCODE=your_shortcode
 * DARAJA_PASSKEY=your_passkey
 * DARAJA_CALLBACK_URL=https://your-public-url.example/api/daraja/callback
 */

// ------------------------------------------------------------
// Utility functions
// ------------------------------------------------------------

function requiredEnv(name) {
  const value = process.env[name];

  if (!value) {
    throw new Error(
      `Missing required environment variable: ${name}`
    );
  }

  return value;
}

/**
 * Returns the current Nairobi time in:
 *
 * YYYYMMDDHHmmss
 *
 * This is the timestamp format required when generating
 * the STK Push password.
 */
function getNairobiTimestamp() {
  const formatter = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Africa/Nairobi",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });

  const parts = formatter.formatToParts(new Date());

  const values = Object.fromEntries(
    parts
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value])
  );

  return (
    values.year +
    values.month +
    values.day +
    values.hour +
    values.minute +
    values.second
  );
}

// ------------------------------------------------------------
// OAuth
// ------------------------------------------------------------

async function getAccessToken(baseUrl) {
  const consumerKey = requiredEnv("DARAJA_CONSUMER_KEY");
  const consumerSecret = requiredEnv("DARAJA_CONSUMER_SECRET");

  const credentials = Buffer.from(
    `${consumerKey}:${consumerSecret}`
  ).toString("base64");

  const response = await fetch(
    `${baseUrl}/oauth/v1/generate?grant_type=client_credentials`,
    {
      method: "GET",
      headers: {
        Authorization: `Basic ${credentials}`,
      },
    }
  );

  if (!response.ok) {
    const body = await response.text();

    throw new Error(
      `OAuth request failed (${response.status}): ${body}`
    );
  }

  const data = await response.json();

  if (!data.access_token) {
    throw new Error(
      "Daraja did not return an access token"
    );
  }

  return data.access_token;
}

// ------------------------------------------------------------
// STK Push
// ------------------------------------------------------------

async function initiateStkPush({
  phoneNumber,
  amount,
  accountReference,
  transactionDescription,
}) {
  const baseUrl = requiredEnv("DARAJA_BASE_URL");
  const shortcode = requiredEnv("DARAJA_SHORTCODE");
  const passkey = requiredEnv("DARAJA_PASSKEY");
  const callbackUrl = requiredEnv("DARAJA_CALLBACK_URL");

  // 1. Obtain OAuth access token
  const token = await getAccessToken(baseUrl);

  // 2. Generate timestamp
  const timestamp = getNairobiTimestamp();

  // 3. Generate STK Push password
  //
  // Password = Base64(
  //   BusinessShortCode + Passkey + Timestamp
  // )
  //
  const password = Buffer.from(
    `${shortcode}${passkey}${timestamp}`
  ).toString("base64");

  // 4. Construct STK Push payload
  const payload = {
    BusinessShortCode: shortcode,
    Password: password,
    Timestamp: timestamp,

    TransactionType: "CustomerPayBillOnline",

    /*
     * IMPORTANT:
     *
     * In a real application, this amount should come from
     * trusted backend order data rather than directly from
     * an Android/client request.
     */
    Amount: amount,

    PartyA: phoneNumber,
    PartyB: shortcode,
    PhoneNumber: phoneNumber,

    CallBackURL: callbackUrl,

    AccountReference: accountReference,
    TransactionDesc: transactionDescription,
  };

  // 5. Submit STK Push request
  const response = await fetch(
    `${baseUrl}/mpesa/stkpush/v1/processrequest`,
    {
      method: "POST",

      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },

      body: JSON.stringify(payload),
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      `STK Push request failed (${response.status}): ${JSON.stringify(result)}`
    );
  }

  return result;
}

// ------------------------------------------------------------
// Example execution
// ------------------------------------------------------------

async function main() {
  const result = await initiateStkPush({
    /*
     * Replace this with a valid sandbox test number when
     * testing against the Daraja sandbox.
     */
    phoneNumber: "2547XXXXXXXX",

    /*
     * Example amount.
     *
     * A production system should load this from the trusted
     * order/payment record.
     */
    amount: 1,

    /*
     * Keep the account reference within the limits defined
     * by the current Daraja STK Push documentation.
     */
    accountReference: "TEST001",

    transactionDescription: "Order payment",
  });

  console.log(
    "Daraja STK Push response:"
  );

  console.log(
    JSON.stringify(result, null, 2)
  );

  /*
   * IMPORTANT:
   *
   * A successful STK Push response does NOT mean that the
   * customer has completed the payment.
   *
   * The backend should persist identifiers such as:
   *
   *   MerchantRequestID
   *   CheckoutRequestID
   *
   * and mark the local payment as:
   *
   *   PENDING
   *
   * The final payment state should be determined from the
   * asynchronous Daraja callback.
   */
}

// ------------------------------------------------------------
// Start
// ------------------------------------------------------------

main().catch((error) => {
  console.error(
    "Payment integration error:",
    error.message
  );

  process.exit(1);
});