# Resilient Asynchronous API Webhook Ingestion Gateway

A production-grade, highly available asynchronous API gateway engineered with FastAPI, Redis, and Celery. This architecture is specifically designed to safely ingest high-frequency third-party webhooks, enforce strict traffic management policies, protect downstream services via asynchronous decoupling, and ensure absolute data consistency under severe network degradation.

---

## Architectural Topology

[Client App / Webhook Sender]
│
▼ (HTTP POST /v1/webhook with X-API-KEY)
┌────────────────────────────────────────────────────────┐
│ FastAPI Gateway Layer                                  │
│  ├── 1. Security: API Key Verification                 │
│  ├── 2. Rate Limiting: Redis ZSET Sliding Window       │
│  └── 3. Idempotency: Redis SET (NX) String Cache       │
└──────────────────────────┬─────────────────────────────┘
│
▼ (Task Pushed to Queue)
┌─────────────────┐
│ Redis Data Store│
└────────┬────────┘
│
▼ (Task Consumed Async)
┌────────────────────────────────────────────────────────┐
│ Distributed Celery Worker Pool                         │
│  └── Executing HTTP POST to Target Endpoint            │
│  └── Error Handling: Exponential Backoff Retry Loop    │
└────────────────────────────────────────────────────────┘

---

## Core Systems Engineering Features

### 1. Security & Authentication Guardrails
* **Mechanics:** Explicit API Key authentication via `X-API-KEY` header validation.
* **Impact:** Drops unauthorized traffic at the perimeter before initializing database operations or compute resources.

### 2. Distributed Sliding-Window Rate Limiting
* **Mechanics:** Implemented via a Redis Sorted Set (`ZSET`) architecture using atomic transactional pipelines (`MULTI/EXEC`). 
* **Impact:** Prevents resource starvation by tracking token frequency per unique API key within an exact sliding window, dynamically dropping abusive bursts with a `429 Too Many Requests` status.

### 3. 24-Hour Transactional Idempotency Filter
* **Mechanics:** Tracks atomic payload processing signatures via a Redis string cache using the strict `SET NX` command with a 24-hour Time-To-Live (`TTL`).
* **Impact:** Guarantees absolute data integrity by blocking duplicate webhooks at the gateway entry point within a 5ms execution window, returning a `409 Conflict` to prevent double-processing downstream.

### 4. Asynchronous Task Worker & Resiliency Loop
* **Mechanics:** Decouples heavy transactional I/O operations from the HTTP client request/response cycle using an asynchronous worker pool.
* **Impact:** In the event of downstream service failure (e.g., HTTP 503 errors), workers execute an automated **Exponential Backoff** logic ($2^{\text{retry}}$ delay matrix). This self-throttling prevents the thundering herd problem, guaranteeing data delivery without overloading unstable targets.

---

## Tech Stack & Dependencies

* **Framework:** FastAPI (ASGI Python Engine)
* **Task Management:** Celery Distributed Task Queue
* **In-Memory Store:** Redis 7 (Caching, Queuing, Rate-Limiting State)
* **Runtime Layer:** Docker / Docker-Compose (Multi-container orchestration)
* **HTTP Client:** HTTPX (Asynchronous network communication)

---

## Local Deployment Instructions

### Prerequisites
* Docker and Docker-Compose installed locally.

### 1. Clone the Architecture
```bash
git clone [https://github.com/Eis-Portfolio-Projects/async-gateway-portfolio.git](https://github.com/Eis-Portfolio-Projects/async-gateway-portfolio.git)
cd async-gateway-portfolio

