# MWFG Engagement FAQ

**Maintained by:** Accenture PMO  
**Last updated:** Q3 2025  
**Classification:** Internal — Engagement Team Only (Fictional — for training purposes)

---

## General Engagement Questions

**Q: What is the total value of the MWFG engagement?**  
A: $4.2M total contract value covering all three workstreams over 12 months (Q1–Q4 2025).

**Q: How many Accenture staff are on this engagement?**  
A: 14 FTEs across three pillars: Strategy, Data & AI, and Technology.

**Q: Who is the Accenture Engagement Lead?**  
A: Sarah Chen, Managing Director, Midwest Financial Services practice.

**Q: Who is the client sponsor?**  
A: James Kowalski, Chief Digital Officer at MidWest Financial Group.

---

## Workstream Questions

**Q: What is the current status of Workstream 1 (AI-Assisted Loan Underwriting)?**  
A: Pilot is live as of Q3 2025. 62% of pilot applications are completing in under 48 hours. Underwriter override rate is 18%, within the <25% target. Full production rollout planned for Q1 2026.

**Q: Why is Workstream 2 (Intelligent Call Center Agent) delayed?**  
A: The primary blocker is PII handling approval from MWFG's legal team. The integration with the Genesys telephony platform has also revealed higher complexity than originally scoped. Go/no-go decision expected October 15, 2025.

**Q: Workstream 3 sounds like it's already done — what happened?**  
A: Workstream 3 (Compliance Reporting Automation) was completed ahead of schedule in Q2 2025. It reduced quarterly compliance reporting time from 20 analyst-days to 1.2 analyst-days — a 94% reduction. All reports passed external audit review.

---

## Technical Questions

**Q: What LLMs are being used in production?**  
A: 
- WS1 (Underwriting): Claude claude-haiku-4-5-20251001 on AWS SageMaker
- WS2 (Call Center, in dev): GPT-4o-mini with ChromaDB vector store
- WS3 (Compliance): Claude Sonnet in an internal reporting pipeline

**Q: Why different models for different workstreams?**  
A: Model selection is based on latency requirements, cost, and accuracy thresholds per workstream. Underwriting needs fast turnaround at scale (Haiku). Compliance reporting benefits from Sonnet's stronger long-document comprehension. Call center is optimized for cost (GPT-4o-mini).

**Q: Does MWFG own the models?**  
A: No. The build vs. buy analysis concluded that LLM APIs are commodity and there is no competitive advantage in training a foundation model. MWFG owns the RAG pipeline, the prompts, and the evaluation framework.

---

## Budget & Financial Questions

**Q: Are we on track with the budget?**  
A: Yes — we are projecting an underspend of approximately $535K (12.7% under budget) by engagement end. Primary drivers: faster-than-expected WS3 completion and the WS2 legal delay pushing costs into Q4/Q1.

**Q: What happens to the contingency budget?**  
A: The $650K contingency has only $125K drawn as of Q3. If WS2 integration complexity increases, contingency will be drawn down. Current forecast is $200K used.

**Q: Can we start Phase 2 scoping before this engagement closes?**  
A: Yes — preliminary Phase 2 scoping conversations are scheduled for Q1 2026. Formal SOW development will follow WS1 production rollout and WS2 go-live.

---

## Risk & Issue Questions

**Q: What is our highest risk right now?**  
A: Two High-severity risks are active: (R1) PII approval blocking WS2, and (R2) AI model accuracy falling below the 0.85 AUC-ROC threshold in production. Both are being actively managed.

**Q: What happens if the model accuracy falls below threshold?**  
A: Per the AI Governance Framework, a model performing below 0.85 AUC-ROC triggers an immediate review by the AI Governance Committee. Deployment may be paused pending retraining or recalibration.

**Q: Is there a plan if the legal team does not approve WS2?**  
A: Yes — a contingency plan is in place to redesign the call center agent to handle only non-PII interactions (product information, branch hours, general FAQs) if full PII approval is not granted. This reduces the projected deflection rate from 30% to approximately 12%.
