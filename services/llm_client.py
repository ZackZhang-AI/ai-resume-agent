"""
Unified LLM client factory.

The agents use this module instead of constructing provider clients directly.
When no configured provider has a usable API key, callers receive None and can
fall back to the deterministic rule-based path.
"""
import json
import re
import urllib.error
import urllib.request
from typing import Optional, Dict, Any

from app_config import config
from services.minimax_client import MiniMaxClient


class BaseLLMClient:
    provider: str
    model: str

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        raise NotImplementedError

    async def generate_async(self, prompt: str, system: Optional[str] = None) -> str:
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.generate(prompt, system))

    def generate_json(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        text = self.generate(prompt, system)
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
        return json.loads(text)


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": config.TEMPERATURE,
            "max_tokens": 12000,
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            raise Exception(f"{self.provider} API HTTP Error {exc.code}: {body}")

        choices = result.get("choices") or []
        if not choices:
            raise Exception(f"{self.provider} API returned no choices")
        return choices[0]["message"]["content"]


class OpenAIClient(OpenAICompatibleClient):
    provider = "openai"

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(
            api_key=api_key,
            model=model or "gpt-4o",
            base_url="https://api.openai.com/v1",
        )


class GeminiClient(BaseLLMClient):
    provider = "gemini"

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or "gemini-1.5-pro"

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": config.TEMPERATURE,
                "maxOutputTokens": 12000,
            },
        }
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            raise Exception(f"Gemini API HTTP Error {exc.code}: {body}")

        candidates = result.get("candidates") or []
        if not candidates:
            raise Exception("Gemini API returned no candidates")
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts)


def create_llm_client(provider: Optional[str] = None) -> Optional[BaseLLMClient]:
    selected = (provider or config.LLM_PROVIDER or "").strip().lower()
    model = config.LLM_MODEL

    if selected:
        return _create_selected_client(selected, model)

    if config.OPENAI_API_KEY:
        return OpenAIClient(config.OPENAI_API_KEY, model)
    if config.GEMINI_API_KEY:
        return GeminiClient(config.GEMINI_API_KEY, model)
    if config.MINIMAX_API_KEY:
        return MiniMaxClient(
            api_key=config.MINIMAX_API_KEY,
            base_url=config.MINIMAX_BASE_URL,
            model=model or config.MINIMAX_MODEL,
            temperature=config.MINIMAX_TEMPERATURE,
        )
    return None


def _create_selected_client(provider: str, model: Optional[str]) -> Optional[BaseLLMClient]:
    if provider == "openai":
        if not config.OPENAI_API_KEY:
            return None
        return OpenAIClient(config.OPENAI_API_KEY, model)
    if provider == "gemini":
        if not config.GEMINI_API_KEY:
            return None
        return GeminiClient(config.GEMINI_API_KEY, model)
    if provider == "minimax":
        if not config.MINIMAX_API_KEY:
            return None
        return MiniMaxClient(
            api_key=config.MINIMAX_API_KEY,
            base_url=config.MINIMAX_BASE_URL,
            model=model or config.MINIMAX_MODEL,
            temperature=config.MINIMAX_TEMPERATURE,
        )
    raise ValueError("LLM_PROVIDER must be one of: minimax, openai, gemini")


def get_quality_mode(llm_client: Optional[BaseLLMClient]) -> str:
    return "llm" if llm_client else "rule_based"
