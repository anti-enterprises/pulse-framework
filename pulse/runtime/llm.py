"""Claude API wrapper with logging and retry.

Wraps the anthropic SDK with:
- Auto API key loading from config
- Exponential backoff on rate limits
- Request metadata logging to RunLogger
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import yaml

from pulse.utils.paths import config_path

if TYPE_CHECKING:
    from pulse.runtime.runs import RunLogger


@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    stop_reason: str | None = None


@dataclass
class LLMConfig:
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    api_key_env: str = "ANTHROPIC_API_KEY"
    api_key: str | None = None


def _load_llm_config() -> LLMConfig:
    """Load LLM config from config.yaml."""
    cfg = config_path()
    if not cfg.exists():
        return LLMConfig()

    with open(cfg) as f:
        data = yaml.safe_load(f) or {}

    llm_data = data.get("llm", {})
    return LLMConfig(
        provider=llm_data.get("provider", "anthropic"),
        model=llm_data.get("model", "claude-sonnet-4-20250514"),
        api_key_env=llm_data.get("api_key_env", "ANTHROPIC_API_KEY"),
        api_key=llm_data.get("api_key"),
    )


def _get_api_key(config: LLMConfig) -> str:
    """Resolve the API key from config or environment."""
    if config.api_key:
        return config.api_key

    key = os.environ.get(config.api_key_env, "")
    if not key:
        raise RuntimeError(
            f"E010: No API key found. Set the {config.api_key_env} environment variable "
            f"or provide api_key in config.yaml."
        )
    return key


class LLMClient:
    """Client for Claude API calls with retry and logging."""

    def __init__(
        self,
        config: LLMConfig | None = None,
        run_logger: RunLogger | None = None,
    ) -> None:
        self.config = config or _load_llm_config()
        self.run_logger = run_logger
        self._client: object | None = None

    def _get_client(self) -> object:
        """Lazy-init the anthropic client."""
        if self._client is None:
            import anthropic
            api_key = _get_api_key(self.config)
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def call(
        self,
        system: str,
        user_message: str,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Make a single Claude API call with retry on rate limits.

        Returns the response content and metadata.
        """
        import anthropic

        client = self._get_client()
        use_model = model or self.config.model

        # Log the request (not full prompt content by default)
        if self.run_logger:
            self.run_logger.log_event({
                "event": "llm_call_start",
                "model": use_model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "system_length": len(system),
                "user_message_length": len(user_message),
            })

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                start = time.monotonic()
                response = client.messages.create(  # type: ignore[attr-defined]
                    model=use_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=[{"role": "user", "content": user_message}],
                )
                latency_ms = int((time.monotonic() - start) * 1000)

                result = LLMResponse(
                    content=response.content[0].text,
                    model=response.model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    latency_ms=latency_ms,
                    stop_reason=response.stop_reason,
                )

                if self.run_logger:
                    self.run_logger.log_event({
                        "event": "llm_call_end",
                        "model": result.model,
                        "input_tokens": result.input_tokens,
                        "output_tokens": result.output_tokens,
                        "latency_ms": result.latency_ms,
                        "stop_reason": result.stop_reason,
                    })

                return result

            except anthropic.RateLimitError as e:
                last_error = e
                wait = 2 ** attempt
                if self.run_logger:
                    self.run_logger.log_event({
                        "event": "llm_rate_limit",
                        "attempt": attempt + 1,
                        "wait_seconds": wait,
                    })
                time.sleep(wait)

            except anthropic.APIError as e:
                if self.run_logger:
                    self.run_logger.log_event({
                        "event": "llm_call_error",
                        "error": str(e),
                    })
                raise RuntimeError(
                    f"E008: Claude API call failed: {e}"
                ) from e

        raise RuntimeError(
            f"E008: Claude API call failed after 3 retries: {last_error}"
        )
