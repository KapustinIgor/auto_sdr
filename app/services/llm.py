import json
import os
import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def ollama_generate(prompt: str, schema: dict | None = None) -> dict:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": schema or "json",
    }
    resp = httpx.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=60)
    resp.raise_for_status()
    text = resp.json().get("response", "{}")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}
