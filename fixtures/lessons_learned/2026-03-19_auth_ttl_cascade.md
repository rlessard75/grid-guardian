# Post-mortem: Auth TTL cascade (INC-44877)
**Date:** 2026-03-19
**Severity:** Sev-1
**Services:** auth-service, payments-api, checkout-web

## Summary
Reducing JWT TTL on auth-service from 60 minutes to 5 minutes — intended as a security hardening — caused a re-authentication storm across all downstream consumers. Token endpoint load went from baseline ~200 rps to ~8,000 rps within 4 minutes of deploy. Auth-service degraded, which cascaded into payments-api timeouts.

## Root cause
Breaking change to a Tier-1 shared service shipped without:
1. A downstream consumer impact analysis (CMDB lists 4 direct consumers).
2. A gradual rollout / dark launch.
3. Notification to consumer teams.

## Lessons learned
- **Any change to auth-service config that affects token lifetime, scope, or signature must trigger a downstream review.** The CMDB's `downstream_consumers` for auth-service is the authoritative list.
- Config values for cross-cutting concerns (TTLs, timeouts, rate limits) on Tier-1 services should be feature-flagged for gradual rollout.
- PRs that change `auth-service` constants related to TTL, expiry, or token lifetime should be flagged automatically.

## Keywords for future detection
jwt, token, ttl, expiry, auth-service config, cross-service breaking change
