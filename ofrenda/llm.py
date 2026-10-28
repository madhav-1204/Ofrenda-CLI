"""
Thin wrapper around the Ollama /api/chat endpoint.

Only knows how to send a list of messages and get a reply back.
Nothing else lives here.
"""
from __future__ import annotations

import httpx

from ofrenda.config import Config

# How long to wait for the model to start producing tokens.
# Generous because small models on CPU can be slow to warm up.
_CONNECT_TIMEOUT = 10.0
_READ_TIMEOUT = 300.0


class OllamaError(RuntimeError):
    """Raised when the Ollama server is unreachable or returns an error."""


def chat(messages: list[dict], cfg: Config) -> str:
    """
    Send a conversation history to Ollama and return the assistant reply.

    messages: list of {"role": "system"|"user"|"assistant", "content": str}
    """
    url = f"{cfg.ollama_url}/api/chat"
    payload = {
        "model": cfg.model,
        "messages": messages,
        "stream": False,
    }

    try:
        response = httpx.post(
            url,
            json=payload,
            timeout=httpx.Timeout(_READ_TIMEOUT, connect=_CONNECT_TIMEOUT),
        )
    except httpx.ConnectError:
        raise OllamaError(
            f"Could not connect to Ollama at {cfg.ollama_url}.\n"
            "Make sure Ollama is running: https://ollama.com\n"
            f"Then pull the model:  ollama pull {cfg.model}"
        )
    except httpx.TimeoutException:
        raise OllamaError(
            f"Ollama did not respond in time (model: {cfg.model}).\n"
            "The model may still be loading. Try again in a moment."
        )

    if response.status_code != 200:
        raise OllamaError(
            f"Ollama returned HTTP {response.status_code}:\n{response.text}"
        )

    data = response.json()
    return data["message"]["content"].strip()
