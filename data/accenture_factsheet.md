# Accenture AI Enablement Program — Client Engagement Factsheet

> This is a fictional factsheet used for demo and training purposes only.

## Engagement Overview

**Client:** MidWest Financial Group (MWFG)  
**Engagement type:** AI Strategy & Implementation  
**Duration:** 12 months (Q1–Q4 2025)  
**Accenture team size:** 14 FTEs across Strategy, Data & AI, and Technology pillars  
**Total contract value:** $4.2M  

---

## Client Background

MidWest Financial Group is a regional bank holding company headquartered in Chicago, Illinois. They serve 2.3 million retail customers and 18,000 commercial clients across the Midwest. 2024 revenue: $1.1B. Their primary technology stack is a mix of legacy mainframe systems (COBOL, IBM DB2) and a partially modernized cloud infrastructure on AWS.

**Pain points identified at engagement kickoff:**
- Manual loan underwriting process taking 8–12 days per application
- High call center volume (1.2M calls/month) with 40% classified as "routine inquiry"
- No unified customer data platform; customer data siloed across 7 legacy systems
- Compliance reporting taking 3–4 analyst-weeks per quarter

---

## Workstreams

### Workstream 1: AI-Assisted Loan Underwriting
**Status:** Pilot live (Q3 2025)  
**Objective:** Reduce underwriting time from 8–12 days to under 48 hours for 80% of applications  
**Approach:** Fine-tuned risk scoring model + LLM-assisted document extraction and narrative summary for underwriters  
**Current results:** 62% of pilot applications completed in <48 hours; underwriter override rate 18% (target: <25%)  
**Tech stack:** Claude claude-haiku-4-5-20251001, AWS SageMaker, internal document store  

### Workstream 2: Intelligent Call Center Agent
**Status:** In development (Q4 2025 target)  
**Objective:** Deflect 30% of routine inquiries to AI agent, reducing call center costs by $2.8M/year  
**Approach:** RAG-based agent grounded in MWFG product knowledge base; escalation routing to human agent  
**Blockers:** PII handling approval pending from MWFG legal; integration with Genesys telephony platform  
**Tech stack:** GPT-4o-mini, ChromaDB, custom Python harness  

### Workstream 3: Compliance Reporting Automation
**Status:** Complete (Q2 2025)  
**Objective:** Reduce quarterly compliance reporting from 3–4 analyst-weeks to <3 analyst-days  
**Approach:** LLM-powered report generation from structured data exports; human-in-the-loop review step  
**Outcome:** 94% reduction in analyst time; 100% of reports passed external audit review  
**Tech stack:** Claude Sonnet, internal reporting pipeline  

---

## Key Metrics (as of Q3 2025)

| Metric | Baseline | Current | Target |
|--------|---------|---------|--------|
| Loan processing time (median) | 10.2 days | 3.8 days | <2 days |
| Call center AI deflection rate | 0% | n/a (WS2 in dev) | 30% |
| Compliance report prep time | 20 analyst-days/quarter | 1.2 analyst-days/quarter | <1 day |
| Underwriter override rate | n/a | 18% | <25% |
| Model accuracy (underwriting risk score) | n/a | 0.84 AUC-ROC | >0.85 |

---

## Budget & Financials

| Category | Budget | Spent (Q1–Q3) | Forecast to Complete |
|----------|--------|---------------|----------------------|
| Strategy & Architecture | $480K | $460K | $480K |
| Data & AI Development | $2.1M | $1.4M | $2.05M |
| Change Management | $320K | $210K | $315K |
| Infrastructure & Licensing | $650K | $380K | $620K |
| Contingency | $650K | $125K | $200K |
| **Total** | **$4.2M** | **$2.575M** | **$3.665M** |

**Projected underspend:** ~$535K (12.7% under budget), primarily due to faster-than-expected Workstream 3 completion and delayed WS2 start from legal review.

---

## Risks & Issues

| # | Risk | Severity | Status | Owner |
|---|------|----------|--------|-------|
| R1 | PII handling approval delays WS2 launch | High | Active | MWFG Legal + Accenture PMO |
| R2 | Model accuracy falls below 0.85 AUC threshold in production | High | Monitoring | Accenture Data & AI |
| R3 | Genesys integration complexity underestimated | Medium | Active | Accenture Technology |
| R4 | Underwriter adoption slower than planned | Medium | Mitigated | MWFG Change Management |
| R5 | LLM provider pricing changes affect budget | Low | Monitoring | Accenture Finance |

---

## Team Structure

**Accenture Engagement Lead:** Sarah Chen (Managing Director, Midwest FS)  
**Client Sponsor:** James Kowalski (Chief Digital Officer, MWFG)  
**Key Contacts:**
- Maria Torres — Accenture Data & AI Lead
- Derek Osei — Accenture Technology Lead  
- Lisa Nakamura — MWFG Project Manager

---

## Upcoming Milestones

- **2025-10-15:** WS2 legal approval (PII handling) — go/no-go decision
- **2025-11-01:** WS2 integration testing kickoff (contingent on legal approval)
- **2025-12-15:** Q4 compliance report automation (WS3 — steady state handoff)
- **2026-01-31:** WS1 full production rollout (all loan types)
- **2026-03-31:** WS2 go-live target (30% deflection rate by end of Q1 2026)
