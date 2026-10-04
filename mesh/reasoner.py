"""The 'AI' in each agent: turns a structured result into a decision rationale.

RuleReasoner runs offline. OllamaReasoner calls Ollama Cloud and is used
automatically when OLLAMA_API_KEY is set. Both share one interface, so agents
never change.
"""
import json
import os
from typing import Protocol
from dotenv import load_dotenv

load_dotenv()

class Reasoner(Protocol):
    async def explain(self, role: str, task: str, facts: dict) -> str: ...

class RuleReasoner:
    async def explain(self, role: str, task: str, facts: dict) -> str:
        return f"{role} {task}: " + ", ".join(f"{k}={v}" for k, v in facts.items())

class OllamaReasoner:
    def __init__(self, model: str | None = None, host: str = "https://ollama.com"):
        from ollama import AsyncClient
        self._model = model or os.getenv("OLLAMA_MODEL", "gpt-oss:120b")
        self._client = AsyncClient(
            host=host,
            headers={"Authorization": f"Bearer {os.environ['OLLAMA_API_KEY']}"},
        )

    async def explain(self, role: str, task: str, facts: dict) -> str:
        response = await self._client.chat(
            model=self._model,
            messages=[
                {"role": "system",
                 "content": f"You are the {role} agent of a consumer goods company. "
                            "Explain the decision in two sentences for a business reader."},
                {"role": "user", "content": f"Task: {task}\nFacts: {json.dumps(facts)}"},
            ],
        )
        return response.message.content

def default_reasoner() -> Reasoner:
    return OllamaReasoner() if os.getenv("OLLAMA_API_KEY") else RuleReasoner()
