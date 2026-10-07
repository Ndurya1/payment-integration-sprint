# Daraja Payment Integration Architecture

## 1. Overview

The payment integration follows a layered architecture in which the
client application communicates with the organization's backend rather
than directly with Safaricom Daraja.

The backend acts as the security and business-logic boundary between
the client and the external payment provider.

The high-level architecture is:

```mermaid
flowchart TD
    A[Customer] --> B[Android / Web Client]

    B -->|HTTPS| C[FastAPI Backend]

    C --> D[Payment Service]

    D -->|OAuth / STK Push| E[Safaricom Daraja]

    D --> F[(PostgreSQL)]

    E -->|STK Prompt| G[Customer M-PESA Phone]

    G -->|Customer PIN / Decision| E

    E -->|Asynchronous Callback| C

    C --> D

    D -->|Update Payment| F

    F --> C

    C -->|Payment Status| B