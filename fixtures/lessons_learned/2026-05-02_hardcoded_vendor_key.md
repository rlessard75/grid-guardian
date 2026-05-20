# Post-mortem: Hardcoded vendor API key (INC-45612)
**Date:** 2026-05-02
**Severity:** Sev-1
**Services:** payments-api, auth-service

## Summary
A vendor API key was committed directly into `payments-api/integrations/vendor_client.py` in 2024 and never migrated to the secrets manager. The vendor rotated the key as part of their own security policy. Payments-api began returning 502 on all vendor-dependent flows.

## Root cause
- Hardcoded credential survived multiple PR reviews because the surrounding code rarely changed.
- No periodic scan of the repo for high-entropy strings or credential patterns.

## Lessons learned
- **All PRs must be scanned for credential patterns (AWS keys, generic API key headers, bearer tokens, private keys, connection strings with embedded passwords) regardless of whether the PR itself adds them — a PR that merely touches a file containing a pre-existing hardcoded secret should surface it.**
- Secrets belong in the secrets manager. Period.
- Vendor key rotation should be a known operational event, not a surprise outage.

## Keywords for future detection
hardcoded, secret, api key, AKIA, bearer, password, credential, vendor, secrets manager
