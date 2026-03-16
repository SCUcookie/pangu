"""
OpenAI-compatible JSON request helper with Chat Completions -> Responses fallback.
"""
import json
import re
from typing import Any, Dict

import requests


def request_json_response(
    *,
    api_base: str,
    api_key: str,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    timeout: int = 120,
) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    errors = []

    chat_payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    try:
        response = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=chat_payload,
            timeout=timeout,
        )
        response.raise_for_status()
        response_json = response.json()
        parsed = _parse_json_payload(response_json["choices"][0]["message"]["content"])
        return {
            "request": chat_payload,
            "response": response_json,
            "parsed": parsed,
            "api_mode": "chat_completions",
        }
    except Exception as error:
        errors.append(f"chat_completions: {error}")

    responses_payload = {
        "model": model_name,
        "instructions": system_prompt,
        "input": user_prompt,
        "text": {
            "format": {
                "type": "json_object",
            }
        },
    }
    try:
        response = requests.post(
            f"{api_base}/responses",
            headers=headers,
            json=responses_payload,
            timeout=timeout,
        )
        response.raise_for_status()
        response_json = response.json()
        parsed = _parse_json_payload(_extract_responses_text(response_json))
        return {
            "request": responses_payload,
            "response": response_json,
            "parsed": parsed,
            "api_mode": "responses",
        }
    except Exception as error:
        errors.append(f"responses: {error}")
        hint = _provider_hint(api_key)
        if hint:
            errors.append(hint)
        raise RuntimeError(" ; ".join(errors)) from error


def probe_openai_compatible_api(
    *,
    api_base: str,
    api_key: str,
    timeout: int = 20,
) -> Dict[str, Any]:
    api_base = api_base.rstrip("/")
    if not api_key:
        return {
            "ok": False,
            "api_base": api_base,
            "models_url": f"{api_base}/models",
            "error": "missing GPT5_API_KEY",
            "hint": "set GPT5_API_KEY or GPT5_API_KEY_FILE before running the judge",
        }

    headers = {"Authorization": f"Bearer {api_key}"}
    models_url = f"{api_base}/models"
    try:
        response = requests.get(models_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        model_count = len(payload.get("data", [])) if isinstance(payload, dict) else None
        return {
            "ok": True,
            "api_base": api_base,
            "models_url": models_url,
            "model_count": model_count,
        }
    except Exception as error:
        result = {
            "ok": False,
            "api_base": api_base,
            "models_url": models_url,
            "error": str(error),
        }
        hint = _provider_hint(api_key)
        if hint:
            result["hint"] = hint
        return result


def _extract_responses_text(response_json: Dict[str, Any]) -> str:
    if response_json.get("output_text"):
        return str(response_json["output_text"])

    chunks = []
    for item in response_json.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            content_type = content.get("type")
            if content_type in {"output_text", "text"}:
                chunks.append(str(content.get("text", "")))
    text = "\n".join(chunk for chunk in chunks if chunk).strip()
    if text:
        return text
    raise ValueError("responses API returned no text output")


def _parse_json_payload(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if fenced:
            return json.loads(fenced.group(1))
        object_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if object_match:
            return json.loads(object_match.group(1))
        raise


def _provider_hint(api_key: str) -> str:
    if api_key.startswith("sk-ant-"):
        return "configured GPT5_API_KEY looks like an Anthropic key (sk-ant-), not an OpenAI-compatible key"
    return ""
