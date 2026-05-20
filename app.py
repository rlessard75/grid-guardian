"""
Capstone: MWFG Engagement Intelligence Agent
Full-capability agent: RAG + memory + skills + MCP tools
"""

import os
import re
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "07_MCPs_and_Skills"))

load_dotenv(ROOT.parent / ".env")

from agent.harness import Agent, Tool
from agent.memory import Memory
from agent.rag import RAGIndex
from agent.skills import load_skills
from mcp_server import get_workstream_status, get_risks

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="MWFG Intelligence Agent", page_icon="🔷", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #1a1a2e; }
    h1, h2, h3 { color: #A100FF; }
    .tool-call { background-color: #0f3460; border-left: 3px solid #A100FF;
                 padding: 0.5rem 1rem; margin: 0.25rem 0; border-radius: 4px;
                 font-family: monospace; font-size: 0.82rem; }
    .memory-badge { background: #A100FF22; border: 1px solid #A100FF55;
                    border-radius: 4px; padding: 0.2rem 0.5rem; font-size: 0.8rem; }
    .stButton > button { background-color: #A100FF; color: white; border: none; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

DATA_DIR = ROOT / "data"
MEMORY_FILE = DATA_DIR / "memory.json"

with st.sidebar:
    st.markdown("## 🔷 MWFG Intelligence Agent")
    st.caption("RAG · Memory · Skills · MCP")
    st.divider()

    model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "claude-haiku-4-5-20251001"], index=0)

    api_key_input = st.text_input("API Key (optional)", type="password", placeholder="overrides .env")
    if api_key_input:
        if model.startswith("claude"):
            os.environ["ANTHROPIC_API_KEY"] = api_key_input
        else:
            os.environ["OPENAI_API_KEY"] = api_key_input

    st.divider()
    st.markdown("**Capabilities:**")
    st.markdown("- 📄 RAG over engagement docs")
    st.markdown("- 🧠 Persistent memory")
    st.markdown("- 🔧 Skills library")
    st.markdown("- 🔌 MCP server tools")

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.agent = None
        st.rerun()

    st.divider()
    st.markdown("**Memory (long-term):**")
    mem = Memory(MEMORY_FILE)
    facts = mem.all_facts()
    if facts:
        for k, v in facts.items():
            st.markdown(f'<span class="memory-badge">{k}: {v}</span>', unsafe_allow_html=True)
    else:
        st.caption("No facts stored yet")

# ---------------------------------------------------------------------------
# Initialise components
# ---------------------------------------------------------------------------

@st.cache_resource
def get_rag():
    return RAGIndex(DATA_DIR)

@st.cache_resource
def get_tools():
    rag = get_rag()
    memory = Memory(MEMORY_FILE)
    skills = load_skills()
    return skills + [
        Tool(name="rag_search", description="Search engagement docs for detailed information.",
             parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
             handler=rag.search),
        Tool(name="remember", description="Store a fact for future sessions.",
             parameters={"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}}, "required": ["key", "value"]},
             handler=lambda key, value: memory.set(key, value)),
        Tool(name="recall", description="Search memory for related facts.",
             parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
             handler=lambda query: "\n".join(memory.recall(query)) or "Nothing found."),
        Tool(name="get_workstream_status", description="Get workstream status (ws1, ws2, ws3).",
             parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
             handler=get_workstream_status),
        Tool(name="get_risks", description="Get risks by severity (High, Medium, Low).",
             parameters={"type": "object", "properties": {"severity": {"type": "string", "enum": ["High", "Medium", "Low"]}}, "required": ["severity"]},
             handler=get_risks),
    ]

BASE_SYSTEM = """You are the MWFG Engagement Intelligence Agent — an AI assistant for the
Accenture team on the MidWest Financial Group AI transformation engagement.
Use rag_search for detailed document questions, get_workstream_status/get_risks for structured data,
search_engagement for quick factsheet lookups, calculate for math, remember/recall for memory."""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state or st.session_state.get("last_model") != model:
    mem = Memory(MEMORY_FILE)
    system = BASE_SYSTEM
    st.session_state.agent = Agent(system=system, tools=get_tools(), model=model)
    st.session_state.last_model = model

# ---------------------------------------------------------------------------
# Chat UI
# ---------------------------------------------------------------------------

st.title("🔷 MWFG Engagement Intelligence Agent")
st.caption("RAG · Persistent Memory · Skills · MCP — everything combined")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        parts = re.split(r"(\[tool:.*?\] → .*?\n)", msg["content"], flags=re.DOTALL)
        for part in parts:
            if part.startswith("[tool:"):
                st.markdown(f'<div class="tool-call">{part.strip()}</div>', unsafe_allow_html=True)
            elif part.strip():
                st.markdown(part)

if prompt := st.chat_input("Ask about the MWFG engagement…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full = ""
        placeholder = st.empty()
        for token in st.session_state.agent.stream(prompt):
            full += token
            parts = re.split(r"(\[tool:.*?\] → .*?\n)", full, flags=re.DOTALL)
            rendered = ""
            for part in parts:
                if part.startswith("[tool:"):
                    rendered += f'\n<div class="tool-call">{part.strip()}</div>\n'
                else:
                    rendered += part
            placeholder.markdown(rendered, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": full})
    st.rerun()  # refresh memory panel in sidebar
