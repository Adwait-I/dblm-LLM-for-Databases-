"""
llm/provider.py
---------------
Multi-provider LLM client supporting:
  - Ollama (local models like qwen2.5-coder:14b)
  - OpenAI (GPT-4o / GPT-4o-mini)
  - Gemini (Gemini 2.5/1.5 Pro/Flash via google-genai)
"""

from __future__ import annotations

import re
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def strip_sql_fences(text: str) -> str:
    """Remove markdown ```sql ... ``` fences if the model adds them."""
    if not text:
        return ""
    text = text.strip()
    pattern = r"^```(?:sql)?\s*\n?(.*?)\n?```$"
    match = re.match(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def _generate_ollama(system_prompt: str, user_prompt: str, model: str, temperature: float) -> str:
    import ollama
    client = ollama.Client(host=settings.ollama_base_url)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = client.chat(
        model=model,
        messages=messages,
        options={"temperature": temperature},
    )
    return response["message"]["content"]


def _generate_openai(system_prompt: str, user_prompt: str, model: str, temperature: float) -> str:
    from openai import OpenAI
    api_key = settings.openai_api_key
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model or settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def _generate_gemini(system_prompt: str, user_prompt: str, model: str, temperature: float) -> str:
    from google import genai
    from google.genai import types
    api_key = settings.gemini_api_key
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    client = genai.Client(api_key=api_key)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    response = client.models.generate_content(
        model=model or settings.gemini_model,
        contents=full_prompt,
        config=types.GenerateContentConfig(temperature=temperature),
    )
    return response.text or ""


def generate_sql(
    system_prompt: str,
    user_prompt: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
) -> str:
    """
    Generate SQL using the configured or specified LLM provider.
    """
    provider = (provider or settings.llm_provider).lower()

    logger.info(
        "Generating SQL via LLM",
        extra={"provider": provider, "prompt_len": len(user_prompt)},
    )

    try:
        if provider == "ollama":
            raw = _generate_ollama(
                system_prompt, user_prompt, model or settings.ollama_model, temperature
            )
        elif provider == "openai":
            raw = _generate_openai(
                system_prompt, user_prompt, model or settings.openai_model, temperature
            )
        elif provider == "gemini":
            raw = _generate_gemini(
                system_prompt, user_prompt, model or settings.gemini_model, temperature
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        sql = strip_sql_fences(raw)
        logger.info("SQL generated successfully", extra={"sql_len": len(sql)})
        return sql

    except Exception as exc:
        logger.error("LLM generation failed", extra={"provider": provider, "error": str(exc)})
        raise RuntimeError(f"LLM generation failed ({provider}): {exc}") from exc
