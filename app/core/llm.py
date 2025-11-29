"""Centralized LLM client with cost tracking, logging, and metadata."""
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from openai import AsyncOpenAI, OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# Pricing per 1M tokens (as of late 2024, update as needed)
MODEL_PRICING = {
    "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
    "anthropic/claude-3-opus": {"input": 15.00, "output": 75.00},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "google/gemini-2.0-flash-001": {"input": 0.10, "output": 0.40},
    "google/gemini-2.0-flash-lite-001": {"input": 0.075, "output": 0.30},
    "meta-llama/llama-3.3-70b-instruct:free": {"input": 0.0, "output": 0.0},
}


@dataclass
class LLMRequest:
    request_id: str
    model: str
    prompt: str
    system_prompt: str | None
    max_tokens: int
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LLMResponse:
    request_id: str
    model: str
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: float
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "model": self.model,
            "content": self.content,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }


class LLMClient:
    """Centralized LLM client with cost tracking and logging."""

    def __init__(self):
        self._client = OpenAI(
            base_url=settings.OPENROUTER_BASE,
            api_key=settings.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "sec-tracker",
            },
        )
        self._async_client = AsyncOpenAI(
            base_url=settings.OPENROUTER_BASE,
            api_key=settings.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "sec-tracker",
            },
        )
        self._request_log: list[LLMResponse] = []

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = MODEL_PRICING.get(model, {"input": 0, "output": 0})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        max_tokens: int = 2000,
        metadata: dict | None = None,
    ) -> LLMResponse:
        """Send a completion request with full tracking."""
        request_id = str(uuid.uuid4())[:8]
        model = model or settings.OPENROUTER_MODEL
        metadata = metadata or {}

        request = LLMRequest(
            request_id=request_id,
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            metadata=metadata,
        )

        logger.info(
            f"LLM Request [{request_id}] model={model} prompt_len={len(prompt)} metadata={metadata}"
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        start_time = time.time()
        error = None
        content = ""
        input_tokens = 0
        output_tokens = 0

        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0

        except Exception as e:
            error = str(e)
            logger.error(f"LLM Request [{request_id}] failed: {error}")

        latency_ms = (time.time() - start_time) * 1000
        total_tokens = input_tokens + output_tokens
        cost_usd = self._calculate_cost(model, input_tokens, output_tokens)

        llm_response = LLMResponse(
            request_id=request_id,
            model=model,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=round(latency_ms, 2),
            metadata=metadata,
            error=error,
        )

        self._request_log.append(llm_response)

        logger.info(
            f"LLM Response [{request_id}] tokens={total_tokens} cost=${cost_usd:.6f} latency={latency_ms:.0f}ms"
        )

        return llm_response

    async def complete_async(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        max_tokens: int = 2000,
        metadata: dict | None = None,
    ) -> LLMResponse:
        """Send an async completion request with full tracking."""
        request_id = str(uuid.uuid4())[:8]
        model = model or settings.OPENROUTER_MODEL
        metadata = metadata or {}

        logger.info(
            f"LLM Request [{request_id}] model={model} prompt_len={len(prompt)} metadata={metadata}"
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        start_time = time.time()
        error = None
        content = ""
        input_tokens = 0
        output_tokens = 0

        try:
            response = await self._async_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0

        except Exception as e:
            error = str(e)
            logger.error(f"LLM Request [{request_id}] failed: {error}")

        latency_ms = (time.time() - start_time) * 1000
        total_tokens = input_tokens + output_tokens
        cost_usd = self._calculate_cost(model, input_tokens, output_tokens)

        llm_response = LLMResponse(
            request_id=request_id,
            model=model,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=round(latency_ms, 2),
            metadata=metadata,
            error=error,
        )

        self._request_log.append(llm_response)

        logger.info(
            f"LLM Response [{request_id}] tokens={total_tokens} cost=${cost_usd:.6f} latency={latency_ms:.0f}ms"
        )

        return llm_response

    async def extract_json_async(
        self,
        text: str,
        schema: dict[str, Any],
        instructions: str,
        model: str | None = None,
        metadata: dict | None = None,
    ) -> tuple[dict | None, LLMResponse]:
        """Extract structured JSON from text using a schema (async version)."""
        prompt = f"""{instructions}

Output valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Text to analyze:
{text}

Respond with ONLY valid JSON, no other text."""

        response = await self.complete_async(
            prompt=prompt,
            model=model,
            metadata={"extraction_type": "json", **(metadata or {})},
        )

        if response.error:
            return None, response

        try:
            result_text = response.content.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            parsed = json.loads(result_text)
            return parsed, response
        except json.JSONDecodeError as e:
            response.error = f"JSON parse error: {e}"
            logger.error(f"LLM Response [{response.request_id}] JSON parse failed: {e}")
            return None, response

    def extract_json(
        self,
        text: str,
        schema: dict[str, Any],
        instructions: str,
        model: str | None = None,
        metadata: dict | None = None,
    ) -> tuple[dict | None, LLMResponse]:
        """Extract structured JSON from text using a schema."""
        prompt = f"""{instructions}

Output valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Text to analyze:
{text}

Respond with ONLY valid JSON, no other text."""

        response = self.complete(
            prompt=prompt,
            model=model,
            metadata={"extraction_type": "json", **(metadata or {})},
        )

        if response.error:
            return None, response

        try:
            result_text = response.content.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            parsed = json.loads(result_text)
            return parsed, response
        except json.JSONDecodeError as e:
            response.error = f"JSON parse error: {e}"
            logger.error(f"LLM Response [{response.request_id}] JSON parse failed: {e}")
            return None, response

    def get_session_stats(self) -> dict:
        """Get aggregated stats for all requests in this session."""
        if not self._request_log:
            return {"total_requests": 0}

        total_cost = sum(r.cost_usd for r in self._request_log)
        total_tokens = sum(r.total_tokens for r in self._request_log)
        total_input = sum(r.input_tokens for r in self._request_log)
        total_output = sum(r.output_tokens for r in self._request_log)
        avg_latency = sum(r.latency_ms for r in self._request_log) / len(self._request_log)
        errors = sum(1 for r in self._request_log if r.error)

        return {
            "total_requests": len(self._request_log),
            "total_tokens": total_tokens,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_cost_usd": round(total_cost, 6),
            "avg_latency_ms": round(avg_latency, 2),
            "errors": errors,
        }

    def get_request_log(self) -> list[dict]:
        """Get full request log."""
        return [r.to_dict() for r in self._request_log]

    def clear_log(self):
        """Clear the request log."""
        self._request_log.clear()


# Global client instance
llm_client = LLMClient()
