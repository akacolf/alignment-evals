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


def _parse_reset_time(header_val: Optional[str], error_text: Optional[str] = None) -> float:
    # First check error_text for "try again in X.Xs"
    if error_text:
        import re
        match = re.search(r"try again in (\d+(?:\.\d+)?)(ms|s|m)?", error_text, flags=re.IGNORECASE)
        if match:
            num = float(match.group(1))
            unit = match.group(2) or "s"
            if unit == "ms":
                return min(8.0, max(0.5, num / 1000.0))
            elif unit == "m":
                return min(8.0, max(1.0, num * 60.0))
            return min(8.0, max(0.5, num))

    if not header_val:
        return 2.0
    val = header_val.strip()
    try:
        if "h" in val:
            return 3.0
        if val.endswith("ms"):
            return min(8.0, max(0.2, float(val[:-2]) / 1000.0))
        if val.endswith("s"):
            return min(8.0, max(0.5, float(val[:-1])))
        if val.endswith("m"):
            return min(8.0, max(1.0, float(val[:-1]) * 60.0))
        return min(8.0, float(val))
    except ValueError:
        return 2.0


class LLMClient:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = (provider or os.getenv("DEFAULT_PROVIDER", "groq")).lower()
        self.model = model or self._default_model(self.provider)
        self.http_client = httpx.AsyncClient(timeout=45.0)

    def _default_model(self, provider: str) -> str:
        defaults = {
            "groq": "qwen/qwen3.8-27b",
            "gemini": "gemini-1.5-flash",
            "ollama": "llama3.1:8b",
            "anthropic": "claude-3-5-haiku-20241022",
            "openai": "gpt-4o-mini",
            "mock": "mock-safety-model",
        }
        return defaults.get(provider, "qwen/qwen3.8-27b")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 350,
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

        max_retries = 8
        for attempt in range(max_retries):
            try:
                response = await self.http_client.post(cfg["url"], headers=headers, json=payload)
                if response.status_code == 429:
                    raw_reset = (
                        response.headers.get("x-ratelimit-reset-tokens")
                        or response.headers.get("retry-after")
                    )
                    err_text = response.text
                    wait_time = min(10.0, max(_parse_reset_time(raw_reset, err_text) + 0.3, 1.5 * (attempt + 1)))
                    await asyncio.sleep(wait_time)
                    continue
                response.raise_for_status()
                data = response.json()
                msg = data["choices"][0]["message"]
                res_text = msg.get("content") or msg.get("reasoning") or ""
                await asyncio.sleep(0.3)
                return res_text
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    raw_reset = e.response.headers.get("x-ratelimit-reset-tokens") or e.response.headers.get("retry-after")
                    err_text = e.response.text
                    wait_time = min(10.0, max(_parse_reset_time(raw_reset, err_text) + 0.3, 1.5 * (attempt + 1)))
                    await asyncio.sleep(wait_time)
                    continue
                raise
            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                raise
        raise RuntimeError("Failed to complete request after maximum retries.")

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
