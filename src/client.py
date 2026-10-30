"""Unified Multi-Provider LLM Client for AI Safety Evaluations.
Supports:
- Groq (Free fast inference)
- Google Gemini (Free tier)
- Ollama (100% Free local)
- OpenAI
- Anthropic
- Mock/Dry-Run (for zero-setup smoke testing)
"""

import os
import json
import asyncio
from typing import List, Dict, Optional, Any
import httpx
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = (provider or os.getenv("DEFAULT_PROVIDER", "groq")).lower()
        self.model = model or self._default_model(self.provider)
        self.http_client = httpx.AsyncClient(timeout=60.0)

    def _default_model(self, provider: str) -> str:
        defaults = {
            "groq": "llama-3.3-70b-versatile",
            "gemini": "gemini-1.5-flash",
            "ollama": "llama3.1:8b",
            "anthropic": "claude-3-5-haiku-20241022",
            "openai": "gpt-4o-mini",
            "mock": "mock-safety-model",
        }
        return defaults.get(provider, "llama-3.3-70b-versatile")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> str:
        """Dispatches generation request to selected provider."""
        if self.provider == "mock" or (
            self.provider == "groq" and not os.getenv("GROQ_API_KEY")
            and not os.getenv("GEMINI_API_KEY")
            and not os.getenv("ANTHROPIC_API_KEY")
            and not os.getenv("OPENAI_API_KEY")
            and self.provider != "ollama"
        ):
            return self._mock_response(messages)

        if self.provider in ["groq", "gemini", "ollama", "openai"]:
            return await self._call_openai_compatible(messages, temperature, max_tokens)
        elif self.provider == "anthropic":
            return await self._call_anthropic(messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _call_openai_compatible(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        configs = {
            "groq": {
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "api_key": os.getenv("GROQ_API_KEY", ""),
            },
            "gemini": {
                "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                "api_key": os.getenv("GEMINI_API_KEY", ""),
            },
            "ollama": {
                "url": f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1').rstrip('/')}/chat/completions",
                "api_key": "ollama",
            },
            "openai": {
                "url": "https://api.openai.com/v1/chat/completions",
                "api_key": os.getenv("OPENAI_API_KEY", ""),
            },
        }

        cfg = configs[self.provider]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['api_key']}",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = await self.http_client.post(cfg["url"], headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def _call_anthropic(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is missing.")

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        # Extract system prompt if present
        system_content = None
        user_messages = []
        for m in messages:
            if m["role"] == "system":
                system_content = m["content"]
            else:
                user_messages.append(m)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": user_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_content:
            payload["system"] = system_content

        response = await self.http_client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]

    def _mock_response(self, messages: List[Dict[str, str]]) -> str:
        """Simulated response for testing pipeline without active API keys."""
        last_msg = messages[-1]["content"].lower()
        if "classify" in last_msg or "score" in last_msg or "evaluator" in last_msg:
            return json.dumps({
                "refusal": False,
                "unfaithful_rationalization": False,
                "violation": False,
                "explanation": "Simulated evaluation evaluation run."
            })
        return "I can provide general educational insights on this topic. In security and safety analysis, best practices prioritize proactive defensive controls, principle of least privilege, and formal verification."

    async def close(self):
        await self.http_client.aclose()
