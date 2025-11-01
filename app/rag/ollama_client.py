# app/rag/ollama_client.py
from __future__ import annotations
import os, json, urllib.request
from typing import List, Dict, Any, Sequence


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 30,
    ):
        self.base_url = (
            base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
        ).rstrip("/")
        self.model = model or os.getenv("OLLAMA_EMBED_MODEL") or "nomic-embed-text"
        self.timeout = int(timeout)

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        """
        Chama /api/embeddings do Ollama.
        - API espera "input": str | [str]
        - Pode responder {"embeddings":[...]} (batch) ou {"embedding":[...]} (single)
        - Fallback item-a-item se a resposta vier vazia/inconsistente
        """
        if not isinstance(texts, (list, tuple)):
            texts = [str(texts)]
        payload = {"model": self.model, "input": list(texts)}
        data = self._post("/api/embeddings", payload)

        # Caminhos felizes
        if isinstance(data, dict):
            if (
                "embeddings" in data
                and isinstance(data["embeddings"], list)
                and data["embeddings"]
            ):
                return data["embeddings"]
            if (
                "embedding" in data
                and isinstance(data["embedding"], list)
                and data["embedding"]
            ):
                # normaliza para lista de listas
                return [data["embedding"]]

        # Fallback robusto: tenta um a um
        out: List[List[float]] = []
        bad: List[int] = []
        for i, t in enumerate(texts):
            single = self._post("/api/embeddings", {"model": self.model, "input": t})
            vec = None
            if isinstance(single, dict):
                if (
                    "embedding" in single
                    and isinstance(single["embedding"], list)
                    and single["embedding"]
                ):
                    vec = single["embedding"]
                elif (
                    "embeddings" in single
                    and isinstance(single["embeddings"], list)
                    and single["embeddings"]
                ):
                    vec = single["embeddings"][0]
            if vec and isinstance(vec, list) and len(vec) > 0:
                out.append(vec)
            else:
                bad.append(i)

        if out and not bad and len(out) == len(texts):
            return out

        meta = {
            "model": self.model,
            "base_url": self.base_url,
            "requested": len(texts),
            "ok": len(out),
            "failed_indexes": bad,
            "raw_first": data,
        }
        raise RuntimeError(
            f"Ollama embeddings vazios/inconsistentes: {json.dumps(meta)[:800]}"
        )
