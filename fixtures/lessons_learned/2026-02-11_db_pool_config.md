# Post-mortem: Payments DB connection pool exhaustion (INC-44218)
**Date:** 2026-02-11
**Severity:** Sev-1
**Services:** payments-api, ledger-db

## Summary
A config PR reduced `max_connections` on the payments-api DB pool from 200 to 50 as part of a "right-sizing" effort. Within 30 minutes of deploy, payment authorization requests began timing out as the pool was exhausted under normal load.

## Root cause
- Pool sizing was changed without referencing observed peak connection usage (which was ~140).
- No staged rollout.

## Lessons learned
- **Changes to resource-pool, timeout, or rate-limit configs on Tier-1 services should require evidence of headroom analysis.**
- Numeric config changes deserve more scrutiny than they typically get — a one-line diff can be a Sev-1.

## Keywords for future detection
connection pool, max_connections, timeout, rate limit, config change, tier-1, payments
