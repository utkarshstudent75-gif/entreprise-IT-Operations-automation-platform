# Sprint 2: Complete OTP Storage Migration to Redis

## Overview

In Sprint 2, the password reset OTP storage and validation workflow was completely migrated from PostgreSQL to Redis. Redis is now the **single source of truth** for all temporary password reset OTP lifecycles across the entire platform.

All legacy OTP storage implementations — including the legacy in-memory OTP store (`OTPService`/`OTPRepository`) and the legacy PostgreSQL OTP store (`PasswordResetRepository`/`password_reset_requests` table) — have been **completely removed**. There is now **exactly one OTP implementation** in the codebase.

To maintain enterprise security compliance and system integrity:
* **Never store plaintext OTPs:** OTPs are hashed using **SHA-256** prior to Redis storage.
* **Audit Logging:** Permanent audit logging of all password reset events (`forgot_password`, `otp_verification`, `password_reset`) remains in PostgreSQL in the `audit_logs` table.
* **API & Frontend Compatibility:** External REST API contracts, FastAPI schemas, status codes, and frontend portal interactions remain 100% unchanged.

---

## Architecture

### Former Architecture (Legacy Dual Implementations)

```text
[Forgot Password Request]
           │
           ├──► Legacy In-Memory OTP Store (app/database/otp_repository.py) [DELETED]
           │
           └──► Legacy PostgreSQL Store (app/repositories/password_reset_repository.py) [DELETED]
```

### Current Single-Source Architecture (Redis)

```text
[Forgot Password API Request]
           │
           ▼
  PasswordResetService ──► RedisService ──► Redis (Key-Value & Hashes)
           │                                 │
           │                                 ├─► otp:<email>      (Active OTP Hash & Attempts)
           │                                 ├─► otp:meta:<email> (TTL Expiry Metadata)
           │                                 └─► otp:used:<email> (Anti-Replay Tracker)
           │
  (Audit Event Recorded)
           │
           ▼
    AuditService ──► AuditRepository ──► PostgreSQL (Table: audit_logs)
```

---

## Why PostgreSQL is No Longer Used for OTP Storage

1. **Transient State vs. Permanent Storage:** Temporary reset codes are inherently short-lived (5-10 minute lifespan). Storing transient state in PostgreSQL causes table bloat, requires background vacuuming/cleanup jobs, and increases disk I/O load.
2. **Native Key Expiration (TTL):** Redis handles expiration automatically at the engine level without requiring cron jobs or scheduled delete queries (`delete_expired_requests`).
3. **Sub-Millisecond Performance:** Password verification and rate limiting operate in memory with sub-millisecond response latency.
4. **Permanent Audit Preservation:** All permanent compliance audit logs are retained in PostgreSQL (`audit_logs`), eliminating the need to preserve transactional OTP rows in SQL once verified or expired.

---

## Redis Key Design & Lifecycle

All Redis keys are namespaced centrally to prevent key collision:

### 1. Active OTP Hash (`otp:<email>`)
* **Type:** Redis Hash
* **Expiry (TTL):** `settings.OTP_EXPIRY_MINUTES * 60` seconds (default 5 minutes)
* **Fields:**
  * `otp_hash` (string): SHA-256 hash of the 6-digit OTP code.
  * `attempts` (integer): Count of failed verification attempts.

### 2. Expiry Metadata Tracker (`otp:meta:<email>`)
* **Type:** Redis String (`"1"`)
* **Expiry:** `settings.OTP_EXPIRY_MINUTES * 60 * 24` seconds
* **Behavior:** Allows distinguishing between an expired OTP (meta key present, active key expired) and an invalid/non-existent request (neither key present).

### 3. Consumed Anti-Replay Guard (`otp:used:<email>`)
* **Type:** Redis String (`otp_hash`)
* **Expiry:** `settings.OTP_EXPIRY_MINUTES * 60` seconds
* **Behavior:** Prevents replay attacks by rejecting attempts to reuse a consumed OTP within its original expiry window.

---

## Security Controls

1. **One-Way Hashing:** OTP values are never stored or logged in plaintext. Hashes are compared securely using constant-time string comparison (`secrets.compare_digest`).
2. **Attempt Limits & Lockout:** Verification attempts are tracked atomically (`hincrby`). If attempts reach `settings.OTP_MAX_ATTEMPTS`, the OTP key is immediately deleted from Redis and the user is locked out.
3. **Immediate Consumption:** Upon successful password reset, the active OTP key is deleted immediately and recorded in the anti-replay tracker.
4. **No Scheduled Cleanup:** Expired OTP keys are automatically purged by Redis TTL eviction.
