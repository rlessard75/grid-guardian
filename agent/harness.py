"""
harness.py — minimal agent harness for the PR Governance Agent.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Generator

import litellm
import os

DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
DEFAULT_API_BASE = os.getenv("LLM_API_BASE") or None
DEFAULT_MAX_TOKENS = 2048
MAX_TURNS = 10


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., str]

    @property
    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class Agent:
    def __init__(
        self,
        system: str,
        tools: list[Tool] | None = None,
        model: str = DEFAULT_MODEL,
        api_base: str | None = DEFAULT_API_BASE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self.model = model
        self.api_base = api_base
        self.max_tokens = max_tokens
        self.tools = {t.name: t for t in (tools or [])}
        self.history: list[dict] = [{"role": "system", "content": system}]

    def chat(self, message: str) -> str:
        return "".join(self.stream(message))

    def stream(self, message: str) -> Generator[str, None, None]:
        self.history.append({"role": "user", "content": message})

        for _ in range(MAX_TURNS):
            text_chunks: list[str] = []
            tool_calls_acc: dict[int, dict] = {}

            kwargs: dict = dict(
                model=self.model,
                messages=self.history,
                tools=[self.tools[n].schema for n in self.tools] or None,
                stream=True,
                max_tokens=self.max_tokens,
            )
            if self.api_base:
                kwargs["api_base"] = self.api_base
            for chunk in litellm.completion(**kwargs):
                delta = chunk.choices[0].delta

                if delta.content:
                    yield delta.content
                    text_chunks.append(delta.content)

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        i = tc.index
                        if i not in tool_calls_acc:
                            tool_calls_acc[i] = {
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }
                        if tc.id:
                            tool_calls_acc[i]["id"] = tc.id
                        if tc.function.name:
                            tool_calls_acc[i]["function"]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls_acc[i]["function"]["arguments"] += tc.function.arguments

            if not tool_calls_acc:
                self.history.append({"role": "assistant", "content": "".join(text_chunks)})
                return

            tool_calls = list(tool_calls_acc.values())
            self.history.append({
                "role": "assistant",
                "content": "".join(text_chunks),
                "tool_calls": tool_calls,
            })

            for tc in tool_calls:
                name = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"] or "{}")
                result = self._call_tool(name, args)
                yield f"\n[tool: {name}] → {result[:120]}{'...' if len(result) > 120 else ''}\n"
                self.history.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

    def reset(self) -> None:
        self.history = [self.history[0]]

    def _call_tool(self, name: str, args: dict[str, Any]) -> str:
        if name not in self.tools:
            return f"Error: unknown tool '{name}'"
        try:
            return self.tools[name].handler(**args)
        except Exception as exc:
            return f"Error running {name}: {exc}"
