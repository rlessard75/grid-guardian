# Capstone — Deep Agent with RAG, Memory, Skills, and MCP

## 🏗️ Build | 🚢 Ship | 📤 Share

### 🏗️ Build
Complete the notebook, run the Streamlit app (`pixi run capstone`), and ask at least 10 questions that exercise different tools — RAG, MCP, memory, and calculation.

### 🚢 Ship
Use the Inspect AI tooling from the LLM-as-Judge notebooks to write a formal eval for the capstone agent. Design a scorer for "did the agent use the right tool for this question?"

### 📤 Share
Architecture diagram of the full agent system, plus 3 things you'd change for a real Accenture client deployment.

---

## What this is

The payoff module. Everything from Day 1 and Day 2 comes together in a single production-quality agent: a custom harness, RAG retrieval, persistent memory, an auto-loaded skill library, and MCP server tools — all wired into a Streamlit UI.

> **You've built every piece.** This module is assembly, not invention. The goal is to see how the pieces fit, understand the tradeoffs of combining them, and evaluate the result using the LLM-as-Judge evaluation pattern.

---

## Prerequisites

- All Day 2 notebooks completed (DeepAgents, Agent Harness, Agent Memory, MCPs & Skills)
- `OPENAI_API_KEY` (embeddings + generation) or `ANTHROPIC_API_KEY` in `.env`

---

## Running the capstone

```bash
# From repo root
pixi run capstone
```

Or directly:

```bash
uv run streamlit run 08_Capstone_Deep_Agent/app.py
```

---

## Architecture

```
User question
    │
    ▼
┌─────────────────────────────────────────────┐
│  Agent (harness.py)                          │
│  system = base_prompt + memory.context_for() │
│                                              │
│  Tools available:                            │
│  ├── rag_search(query)    ← agent/rag.py     │
│  ├── remember(key, value) ← agent/memory.py  │
│  ├── recall(query)        ← agent/memory.py  │
│  ├── search_engagement()  ← 07 skills/       │
│  ├── calculate()          ← 07 skills/       │
│  ├── get_workstream_status() ← 07 mcp_server │
│  └── get_risks()          ← 07 mcp_server    │
└─────────────────────────────────────────────┘
    │
    ▼
Streamlit UI (app.py)
  - Chat interface (same pattern as the Accenture Engagement Agent)
  - Memory panel in sidebar
  - Tool-call visualization
```

---

## The closing loop: Eval your agent

The last Activity in `Capstone.ipynb` connects back to the LLM-as-Judge evaluation pattern. You'll:
1. Run 10 test questions through the capstone agent
2. Design a judge for "did the agent use the right tool?"
3. Run the judge and score the agent
4. Identify where it fails and why

This is the full Day 1 → Day 2 arc: build an AI system → evaluate it rigorously.

---

