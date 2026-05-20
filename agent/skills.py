"""
Capstone skills loader — re-uses skills from Module 07.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent.parent / "07_MCPs_and_Skills" / "skills"


def load_skills() -> list:
    """Load all skills from 07_MCPs_and_Skills/skills/. Returns list of Tool."""
    # Import Tool from the re-exported harness
    from agent.harness import Tool  # noqa: PLC0415

    sys.path.insert(0, str(SKILLS_DIR))
    tools = []
    for path in SKILLS_DIR.glob("*.py"):
        if path.name.startswith("_"):
            continue
        try:
            module = importlib.import_module(path.stem)
            if not hasattr(module, "SKILL_META") or not hasattr(module, "run"):
                continue
            meta = module.SKILL_META
            tools.append(Tool(
                name=meta["name"],
                description=meta["description"],
                parameters=meta["parameters"],
                handler=module.run,
            ))
        except Exception as e:
            print(f"Warning: could not load skill {path.name}: {e}")
    return tools
