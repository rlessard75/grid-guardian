# PR Governance Agent

A pull-request review system built on top of the capstone agent harness.
Scans PRs for secrets/PII (governance sweep) and risky historical patterns
(CMDB + incident + lessons-learned lookups), then presents results in a
React reviewer dashboard.

---

## Architecture

```
Input: PR fixture JSON
   │
   ▼
agent/orchestrator.py  ← Python router (parse → governance → pattern → aggregate)
   │
   ├─► agent/subagents/governance.py   Agent(scan_diff_for_secrets)
   │                                   prompts/governance_sweep.md
   │
   └─► agent/subagents/pattern.py      Agent(query_cmdb, query_incident_management,
                                             query_lessons_learned)
                                        prompts/pattern_recognition.md
   │
   ▼
output/reviews/<pr_id>.json   ← Step 5 output contract

   │
   ▼
dashboard/server/server.py    ← FastAPI thin server
   │
   ▼
dashboard/src/                ← Vite + React SPA
```

Both subagents are independent `Agent` instances (same `Agent` class from
`05_Agent_Harness/harness.py`), each with their own system prompt and tool
subset. The main orchestrator is a plain Python router — no LangGraph/CrewAI.

---

## Prerequisites

- Python 3.11+  (litellm, chromadb, fastapi, uvicorn, python-dotenv)
- Node 18+  (npm / Vite / React)
- An **`ANTHROPIC_API_KEY`** (or `OPENAI_API_KEY`) in the `.env` file at the
  **repo root** (`LLMGenAITitaniumEngineering/.env`)

Set the model with `LLM_MODEL` in `.env` (default: `claude-sonnet-4-6`).

---

## (a) Run the agent on a single fixture from the CLI

```bash
# from: 08_Capstone_Deep_Agent - Rob/
python run_review.py fixtures/pull_requests/pr_clean.json
python run_review.py fixtures/pull_requests/pr_secret_leak.json
python run_review.py fixtures/pull_requests/pr_risky_pattern.json
```

Each run writes `output/reviews/<pr_id>.json`.

---

## (b) Run all three fixtures at once

```bash
python run_all_fixtures.py
```

Produces:
- `output/reviews/PR-1041.json`  — status: **clean**
- `output/reviews/PR-1042.json`  — status: **issues_found** (critical: AWS key, DB password, PII in log)
- `output/reviews/PR-1043.json`  — status: **issues_found** (high: auth TTL + DB pool pattern matches)

Run this first so the dashboard has content on first open.

---

## (c) Start the backend server

```bash
# from: 08_Capstone_Deep_Agent - Rob/dashboard/server/
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```

API available at `http://localhost:8000`. Health check: `GET /api/health`.

---

## (d) Start the React dashboard

```bash
# from: 08_Capstone_Deep_Agent - Rob/dashboard/
npm install
npm run dev
```

Dashboard at `http://localhost:5173`.

---

## (e) One command: start backend + dashboard together

Install `concurrently` once:

```bash
cd dashboard && npm install && npm install --save-dev concurrently
```

Then from the **project root** (`08_Capstone_Deep_Agent - Rob/`):

```bash
npm --prefix dashboard run start:all
```

This requires adding the `start:all` script (see below). Alternatively use
the provided PowerShell helper:

```powershell
.\start_dev.ps1
```

---

## (f) Demo walk-through

1. Run all fixtures:
   ```bash
   python run_all_fixtures.py
   ```

2. Start backend + dashboard (one command):
   ```bash
   .\start_dev.ps1
   ```

3. Open `http://localhost:5173` in a browser.

4. **Left pane** shows the three pre-seeded reviews. Click each to inspect.

5. Click **Submit PR for Review** (top-right button).

6. In the modal:
   - Drag `dashboard/public/sample_uploads/sample_pii_logging.diff` into the
     drop zone, fill in a title (e.g. *"Debug logging in charge handler"*),
     click **Run Review**.
   - Or drag `sample_timeout_change.diff` for a pattern-only finding.

7. Watch **Parse → Governance Sweep → Pattern Recognition → Report** light
   up live as the agent runs.

8. When the modal closes the new review auto-loads in the right pane.

9. Click **Approve PR** or **Request Changes** — the decision is written to
   `output/decisions/<pr_id>.json` and the banner appears.

---

## Expected outcomes per fixture

| PR | Governance | Pattern | Status |
|---|---|---|---|
| `pr_clean.json` (PR-1041) | none | none — marketing-site Tier-3, no matches | **clean** |
| `pr_secret_leak.json` (PR-1042) | AWS key, AWS secret, DB connection string, PII in log | INC-45612, INC-45203 · post-mortems `2026-05-02_hardcoded_vendor_key.md` + `2026-04-08_pii_in_logs.md` | **issues_found** (critical) |
| `pr_risky_pattern.json` (PR-1043) | none | INC-44877 (JWT TTL) + INC-44218 (DB pool) · auth-service has 4 downstream consumers | **issues_found** (high) |

---

## Files created vs extended

### New files (all new for this agent)

| Path | Purpose |
|---|---|
| `agent/context.py` | Shared Context dataclass — persisted to `output/context/` |
| `agent/pr_parser.py` | PR fixture normalizer |
| `agent/orchestrator.py` | Main Python router (parse → governance → pattern → aggregate) |
| `agent/subagents/governance.py` | Governance sweep subagent |
| `agent/subagents/pattern.py` | Pattern recognition subagent |
| `tools/scan_diff.py` | Regex scanner for secrets/PII |
| `tools/cmdb.py` | CMDB fixture lookup |
| `tools/incidents.py` | Incident management fixture lookup |
| `tools/lessons_learned.py` | Post-mortem keyword search |
| `prompts/governance_sweep.md` | Governance subagent system prompt |
| `prompts/pattern_recognition.md` | Pattern subagent system prompt |
| `fixtures/cmdb/cmdb.json` | 6-service CMDB fixture |
| `fixtures/servicenow/incidents.json` | 8-incident ServiceNow fixture |
| `fixtures/lessons_learned/*.md` | 4 post-mortem documents |
| `fixtures/pull_requests/*.json` | 3 PR test fixtures |
| `run_review.py` | CLI entry point |
| `run_all_fixtures.py` | Batch runner for all 3 fixtures |
| `dashboard/server/server.py` | FastAPI thin server |
| `dashboard/server/requirements.txt` | Server deps |
| `dashboard/src/` | Vite + React SPA |
| `dashboard/public/sample_uploads/` | 2 raw `.diff` files for demo |
| `start_dev.ps1` | One-command dev launcher |
| `README_PR_AGENT.md` | This file |

### Existing files — unchanged

| Path | Status |
|---|---|
| `agent/harness.py` | **Unchanged** — re-exports `Agent`, `Tool` from Module 05 |
| `agent/memory.py` | Unchanged |
| `agent/rag.py` | Unchanged |
| `agent/skills.py` | Unchanged |
| `app.py` | Unchanged (Streamlit app) |
| `data/` | Unchanged |

---

## Deviation from spec

> "Do not hardcode a linear pipeline if the reference codebase supports
> conditional routing — use its routing primitive."

The reference codebase (`05_Agent_Harness/harness.py`) has no routing
primitive — it is a single stateful `Agent` class with no state machine.
The orchestrator is therefore implemented as a plain Python function with
sequential step calls and a `progress_cb` hook. Conditional routing (e.g.,
skip pattern recognition if governance finds a critical blocker) can be
added to `agent/orchestrator.py` without touching the subagents.

---

## Prompt files

Subagent prompts live in `prompts/` and can be edited without code changes:

- `prompts/governance_sweep.md` — instructs the governance Agent on what to
  scan for and how to format findings
- `prompts/pattern_recognition.md` — instructs the pattern Agent on CMDB /
  incident / lessons-learned workflow and finding format

---

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required for Claude models |
| `OPENAI_API_KEY` | — | Required for GPT models |
| `LLM_MODEL` | `claude-sonnet-4-6` | LLM used by both subagents |
| `EMBED_MODEL` | `text-embedding-3-small` | Embedding model for lessons-learned vector search (optional — falls back to keyword search) |
| `EMBED_API_BASE` | — | Custom embedding endpoint (optional) |
