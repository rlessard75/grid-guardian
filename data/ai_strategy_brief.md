# AI Strategy Brief: MidWest Financial Group

**Prepared by:** Accenture Strategy & Consulting  
**Date:** Q2 2025  
**Classification:** Client Confidential (Fictional — for training purposes)

---

## Executive Summary

MidWest Financial Group (MWFG) has committed to becoming an AI-first financial institution by 2027. This brief outlines the strategic rationale, priority investment areas, and governance framework for MWFG's AI transformation, as agreed with the Accenture engagement team.

---

## Strategic Context

The regional banking sector faces compounding pressure from three directions:

1. **Digital-native competitors** (neobanks, fintech lenders) operating with dramatically lower cost structures
2. **Regulatory complexity** increasing compliance overhead by an estimated 12% per year
3. **Customer experience expectations** set by consumer tech companies, not banks

MWFG's leadership recognizes that AI is not a feature to add — it is the operating model for the next decade. The goal is not to automate existing processes but to redesign them around AI capabilities.

---

## Priority Investment Areas

### 1. AI-Augmented Underwriting

**Thesis:** The 8–12 day loan processing cycle is a competitive liability. Digital lenders approve in minutes. AI can close this gap while improving risk precision.

**Investment:** $2.1M (primary AI development workstream)  
**Expected ROI:** 3.2x over 3 years from reduced cycle time, lower operational cost, and improved risk-adjusted returns  
**Key risk:** Model accuracy must maintain or exceed current human underwriting AUC-ROC of 0.82. Current pilot at 0.84.

### 2. Conversational Banking

**Thesis:** 40% of call center volume is routine inquiry (balance checks, payment due dates, product information). AI deflection at 30% saves $2.8M/year with no customer experience degradation if properly designed.

**Investment:** ~$800K (WS2 technology + integration)  
**Expected ROI:** 4.1x over 3 years primarily from cost avoidance  
**Key risk:** PII handling in voice/text channels requires explicit legal sign-off. Currently blocking.

### 3. Compliance Automation

**Thesis:** Regulatory reporting is labor-intensive, repetitive, and low-judgment — a high-value AI target.

**Investment:** ~$640K (completed Q2 2025)  
**Outcome:** 94% reduction in analyst time. $1.1M in annual savings. Already delivered.

---

## Governance Framework

MWFG has established an AI Governance Committee with the following structure:

- **Chair:** Chief Digital Officer (James Kowalski)
- **Members:** CRO, Chief Compliance Officer, Chief Data Officer, VP of Customer Experience
- **Meeting cadence:** Bi-weekly during active implementation, monthly in steady state

**Key policies established:**

| Policy | Summary |
|--------|---------|
| Human-in-the-Loop | Any AI decision above $250K loan value requires human review |
| Explainability | All AI decisions must produce human-readable rationale |
| Audit Trail | All AI-assisted decisions logged for 7 years |
| Model Risk | AI models classified as MRM Category 2 (significant), requiring quarterly review |

---

## Build vs. Buy Analysis

| Capability | Decision | Rationale |
|-----------|---------|-----------|
| LLM API | Buy (OpenAI/Anthropic) | Commodity; no competitive advantage in training own foundation model |
| Vector Database | Build (ChromaDB/custom) | Simple enough to own; avoids vendor lock-in on data |
| RAG Pipeline | Build | Core IP differentiator; customized for MWFG document types |
| Monitoring/Observability | Buy (TBD vendor) | Specialized tooling; cost of build exceeds benefit |

---

## 2026 Roadmap (Preview)

Following current engagement completion, MWFG and Accenture have agreed in principle to a Phase 2 engagement covering:

1. **Agentic Workflows** — multi-step AI processes for complex loan restructuring and fraud investigation
2. **Synthetic Data Generation** — creating training data for edge cases that rarely appear in historical records
3. **Advanced Retrieval** — improving accuracy of conversational banking via re-ranking and hybrid search
4. **Production Guardrails** — hallucination detection, PII redaction, and output validation at scale

Phase 2 scoping is scheduled for Q1 2026.
