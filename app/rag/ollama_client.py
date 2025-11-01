# app/rag/ollama_client.py
from __future__ import annotations
import os, json, urllib.request

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


class OllamaClient:
    def __init__(self, base: str = OLLAMA_BASE, model: str = EMBED_MODEL):
        self.base = base.rstrip("/")
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        payload = {"model": self.model, "input": texts}
        req = urllib.request.Request(
            f"{self.base}/api/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # compat: alguns builds retornam {"embeddings":[...]} outros {"data":[{"embedding":...}]}
        if "embeddings" in data:
            return data["embeddings"]
        if "data" in data:
            return [item["embedding"] for item in data["data"]]
        raise RuntimeError(f"Unexpected embed response: {data}")
