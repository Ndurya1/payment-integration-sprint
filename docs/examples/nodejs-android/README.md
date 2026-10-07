# Node.js and FastAPI Integration Comparison

This directory contains a compact Node.js reference implementation of the
Safaricom Daraja STK Push flow described in the technical report.

The main project in this repository is implemented using **Python,
FastAPI, PostgreSQL, SQLAlchemy and HTTPX**. The Node.js example is
therefore a comparative implementation pattern rather than a replacement
for the existing FastAPI backend.

Both implementations communicate with the same Daraja HTTP APIs. The
main difference is the programming language, framework and supporting
libraries used to implement the backend.

## 1. High-Level Comparison

The payment architecture remains the same:

```text
Android / Web Client
        |
        | HTTPS
        v
Business Backend
        |
        | OAuth + STK Push
        v
Safaricom Daraja
        |
        | Callback
        v
Business Backend
        |
        v
Database