"""Re-export harness from Module 05 so the capstone imports cleanly."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "05_Agent_Harness"))
from harness import Agent, Tool, DEFAULT_MODEL, MAX_TURNS  # noqa: F401
