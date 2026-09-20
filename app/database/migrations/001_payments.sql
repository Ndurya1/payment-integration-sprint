CREATE TABLE IF NOT EXISTS payments(
    id UUID PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    account_reference VARCHAR(100),
    checkout_request_id VARCHAR(100),
    merchant_request_id VARCHAR(100),
    mpesa_receipt_number VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    result_code INTEGER,
    result_description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);