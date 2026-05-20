# Post-mortem: PII written to payments-api debug logs (INC-45203)
**Date:** 2026-04-08
**Severity:** Sev-2 (compliance escalation)
**Services:** payments-api

## Summary
A `log.debug(f"Request body: {request.json}")` statement was added during debugging of a different issue and merged. The request body contained cardholder email, last-4, and billing address. Logs are retained 90 days and were ingested by three downstream log systems before detection.

## Root cause
- No automated PII scanner on PRs touching services classified as PCI or PII in the CMDB.
- Reviewer did not catch the broad log statement.

## Lessons learned
- **PRs touching services with `data_classification` of `PCI` or `PII` must be scanned for log statements that emit request/response bodies, user objects, or any field matching email / phone / ID / card patterns.**
- Logging libraries should have redaction wrappers; raw `request.json` or `request.body` in a log statement is a red flag.
- Even debug-level logs are a leak — log levels are not access controls.

## Keywords for future detection
pii, logging, log.debug, request.body, request.json, payments-api, pci, redaction
