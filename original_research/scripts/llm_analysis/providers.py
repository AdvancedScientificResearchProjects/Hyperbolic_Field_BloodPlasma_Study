"""Vision LLM provider initialization and async call wrapper.

Adapted from asrp.science-llm/app/images/providers.py for standalone use.
Supports 8 providers: OpenAI, Google, Anthropic, xAI, Groq, Mistral, Qwen, Bedrock.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "results" / "api_logs"
_LOG_FILE: Path | None = None


def _get_log_file() -> Path:
    """Return the JSONL log file for today, creating dir if needed."""
    global _LOG_FILE
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = _LOG_DIR / f"{today}.jsonl"
    if _LOG_FILE != path:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        _LOG_FILE = path
    return path


def _extract_prompt_text(message: HumanMessage) -> str:
    """Extract text portion of the message (skip base64 image data)."""
    if isinstance(message.content, str):
        return message.content
    parts = []
    img_count = 0
    for block in message.content:
        if isinstance(block, dict):
            if block.get("type") == "text":
                parts.append(block["text"])
            elif block.get("type") == "image_url":
                img_count += 1
                parts.append(f"[image_{img_count}]")
    return "\n".join(parts)


def _log_api_call(
    provider: str,
    model_id: str,
    prompt_text: str,
    response_text: str | None,
    error: str | None,
    latency_ms: int,
    image_count: int,
):
    """Append one API call record to the daily JSONL log."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model_id,
        "prompt_text": prompt_text[:500],
        "prompt_len": len(prompt_text),
        "image_count": image_count,
        "response_text": response_text,
        "response_len": len(response_text) if response_text else 0,
        "error": error,
        "latency_ms": latency_ms,
    }
    try:
        with open(_get_log_file(), "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning("Failed to write API log: %s", e)

PROVIDER_CONFIGS = {
    "openai": {
        "model": "openai:gpt-5",
        "timeout": 300,
        "api_key_env": "OPENAI_API_KEY",
        "key_param": "api_key",
    },
    "google": {
        "model": "google_genai:gemini-2.5-flash",
        "timeout": 90,
        "api_key_env": "GOOGLE_API_KEY",
        "key_param": "google_api_key",
    },
    "anthropic": {
        "model": "anthropic:claude-sonnet-4-6",
        "timeout": 60,
        "api_key_env": "ANTHROPIC_API_KEY",
        "key_param": "api_key",
    },
    "xai": {
        "model": "xai:grok-2-vision-1212",
        "timeout": 60,
        "api_key_env": "XAI_API_KEY",
        "key_param": "api_key",
    },
    "groq": {
        "model": "groq:meta-llama/llama-4-scout-17b-16e-instruct",
        "timeout": 90,
        "api_key_env": "GROQ_API_KEY",
        "key_param": "api_key",
    },
    "mistral": {
        "model": "pixtral-large-2411",
        "timeout": 60,
        "api_key_env": "MISTRAL_API_KEY",
        "model_type": "openai_shim",
        "base_url": "https://api.mistral.ai/v1",
    },
    "qwen": {
        "model": "qwen3-vl-plus",
        "timeout": 90,
        "api_key_env": "DASHSCOPE_API_KEY",
        "model_type": "openai_shim",
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    },
    "perplexity": {
        "model": "sonar-pro",
        "timeout": 90,
        "api_key_env": "PERPLEXITY_API_KEY",
        "model_type": "openai_shim",
        "base_url": "https://api.perplexity.ai",
    },
    "bedrock": {
        "model": "amazon.nova-pro-v1:0",
        "timeout": 90,
        "api_key_env": "AWS_ACCESS_KEY_ID",
        "model_type": "bedrock",
    },
}


def _has_key(config: dict) -> bool:
    if config.get("model_type") == "bedrock":
        return bool(
            os.getenv("AWS_ACCESS_KEY_ID")
            and os.getenv("AWS_SECRET_ACCESS_KEY")
        )
    return bool(os.getenv(config["api_key_env"]))


def init_providers(
    filter_names: list[str] | None = None,
) -> dict[str, object]:
    """Initialize and return available provider model instances.

    Args:
        filter_names: Optional list of provider names to include.
                      If None, all providers with API keys are included.
    """
    from langchain.chat_models import init_chat_model

    models: dict[str, object] = {}

    for name, config in PROVIDER_CONFIGS.items():
        if filter_names and name not in filter_names:
            continue
        if not _has_key(config):
            logger.info("Skipping %s — no API key", name)
            continue

        try:
            model_type = config.get("model_type")

            if model_type == "openai_shim":
                from langchain_openai import ChatOpenAI
                models[name] = ChatOpenAI(
                    model=config["model"],
                    base_url=config["base_url"],
                    api_key=os.getenv(config["api_key_env"]),
                    temperature=0,
                )
            elif model_type == "bedrock":
                from langchain_aws import ChatBedrockConverse
                region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
                models[name] = ChatBedrockConverse(
                    model_id=config["model"],
                    region_name=region,
                    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                    temperature=0,
                )
            else:
                api_key = os.getenv(config["api_key_env"])
                models[name] = init_chat_model(
                    model=config["model"],
                    temperature=0,
                    **{config["key_param"]: api_key},
                )

            logger.info("Initialized %s (%s)", name, config["model"])
        except Exception as e:
            logger.error("Failed to init %s: %s", name, e)

    return models


async def call_provider(
    name: str,
    model: object,
    message: HumanMessage,
    timeout: int | None = None,
) -> dict:
    """Call a single provider with timeout. Returns result dict."""
    cfg_timeout = timeout or PROVIDER_CONFIGS.get(name, {}).get("timeout", 60)
    model_id = PROVIDER_CONFIGS.get(name, {}).get("model", "unknown")
    prompt_text = _extract_prompt_text(message)
    image_count = sum(
        1 for b in (message.content if isinstance(message.content, list) else [])
        if isinstance(b, dict) and b.get("type") == "image_url"
    )

    start = time.monotonic()
    try:
        response = await asyncio.wait_for(
            model.ainvoke([message]),
            timeout=cfg_timeout,
        )
        elapsed = int((time.monotonic() - start) * 1000)

        content = response.content
        if isinstance(content, list):
            content = " ".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            )

        _log_api_call(name, model_id, prompt_text, content, None, elapsed, image_count)
        return {"provider": name, "analysis": content, "latency_ms": elapsed}

    except asyncio.TimeoutError:
        elapsed = int((time.monotonic() - start) * 1000)
        _log_api_call(name, model_id, prompt_text, None, f"Timeout after {cfg_timeout}s", elapsed, image_count)
        return {"provider": name, "error": f"Timeout after {cfg_timeout}s", "latency_ms": elapsed}

    except Exception as e:
        elapsed = int((time.monotonic() - start) * 1000)
        logger.error("Provider %s failed: %s", name, e)
        _log_api_call(name, model_id, prompt_text, None, f"{type(e).__name__}: {e}", elapsed, image_count)
        return {"provider": name, "error": f"{type(e).__name__}: {e}", "latency_ms": elapsed}
