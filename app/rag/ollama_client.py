# app/rag/ollama_client.py
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | int = 25,
        retries: int = 2,
        backoff_s: float = 0.5,
    ):
        env_url = (
            os.getenv("OLLAMA_URL")
            or os.getenv("OLLAMA_BASE_URL")
            or "http://ollama:11434"
        )
        self.base_url = (base_url or env_url).rstrip("/")
        self.model = model or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        env_timeout = os.getenv("LLM_TIMEOUT")
        self.timeout = float(env_timeout) if env_timeout is not None else float(timeout)
        self.retries = int(retries)
        self.backoff_s = float(backoff_s)

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if not isinstance(data, dict):
                    return {"error": f"invalid-json: {type(data)}"}
                return data
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode("utf-8"))
            except Exception:
                err = {"error": f"http {e.code}"}
            return {"error": err}
        except Exception as e:
            return {"error": repr(e)}

    def _extract_vector(self, data: Dict[str, Any]) -> list[float]:
        """
        Ollama /api/embeddings costuma retornar:
          { "embedding": [ ... ] }   # unitário
        Alguns wrappers retornam:
          { "embeddings": [[...], ...] }
        """
        if not isinstance(data, dict):
            return []
        if "embedding" in data and isinstance(data["embedding"], list):
            return data["embedding"]
        if "embeddings" in data and isinstance(data["embeddings"], list):
            # pega o primeiro vetor se houver
            arr = data["embeddings"]
            if arr and isinstance(arr[0], list):
                return arr[0]
        return []

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Usa o endpoint /api/embed do Ollama para realizar embedding em lote.
        Espera resposta no formato:
          { "embeddings": [[...], ...] }
        Garante len(vetores) == len(texts).
        """
        last_resp: Dict[str, Any] | None = None

        for attempt in range(self.retries + 1):
            payload = {"model": self.model, "input": texts}
            data = self._post("/api/embed", payload)
            last_resp = data

            if "error" in data:
                time.sleep(self.backoff_s)
                continue

            if not isinstance(data, dict):
                time.sleep(self.backoff_s)
                continue

            arr = data.get("embeddings")
            if isinstance(arr, list) and len(arr) == len(texts):
                # valida se todos os vetores são listas não vazias
                if all(isinstance(v, list) and len(v) > 0 for v in arr):
                    return arr

            time.sleep(self.backoff_s)

        meta = {
            "model": self.model,
            "base_url": self.base_url,
            "requested": len(texts),
            "ok": 0,
            "failed_indexes": list(range(len(texts))),
            "raw_first": (
                last_resp if isinstance(last_resp, dict) else {"raw": last_resp}
            ),
        }
        raise RuntimeError(
            f"Ollama embeddings em lote vazios/inconsistentes: {json.dumps(meta, ensure_ascii=False)}"
        )

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Garante 1:1 (len(vectors) == len(texts)).
        Tenta primeiro /api/embed (batch) com campo 'input' (quando houver >1 texto).
        Fallback: /api/embeddings com campo 'prompt' (modo unitário).
        """
        if not texts:
            return []

        # Caminho preferencial: tentativa de batch em /api/embed (quando houver >1 texto).
        # Mantém compatibilidade total: em caso de falha, cai para o modo legado 1:1.
        if len(texts) > 1:
            try:
                vectors = self._embed_batch(texts)
                # sanity: garante 1:1
                if len(vectors) == len(texts):
                    return vectors
            except Exception:
                # Fallback silencioso para o modo antigo (um POST por texto).
                # Observabilidade de erros/falhas fica a cargo de quem chama.
                pass

        out: List[List[float]] = []
        for idx, t in enumerate(texts):
            last_resp: Dict[str, Any] | None = None
            for attempt in range(self.retries + 1):
                payload = {"model": self.model, "prompt": t}
                data = self._post("/api/embeddings", payload)
                last_resp = data
                if "error" in data:
                    time.sleep(self.backoff_s)
                    continue
                # tenta extrair vetor unitário...
                vec = self._extract_vector(data)
                if isinstance(vec, list) and len(vec) > 0:
                    out.append(vec)
                    break
                # ...ou, se a API devolveu 'embeddings', pega o primeiro
                if isinstance(data, dict) and isinstance(data.get("embeddings"), list):
                    arr = data["embeddings"]
                    if arr and isinstance(arr[0], list) and len(arr[0]) > 0:
                        out.append(arr[0])
                        break

                time.sleep(self.backoff_s)
            else:
                # Falhou após retries
                meta = {
                    "model": self.model,
                    "base_url": self.base_url,
                    "requested": 1,
                    "ok": 0,
                    "failed_indexes": [0],
                    "raw_first": (
                        last_resp if isinstance(last_resp, dict) else {"raw": last_resp}
                    ),
                }
                raise RuntimeError(
                    f"Ollama embeddings vazios/inconsistentes: {json.dumps(meta, ensure_ascii=False)}"
                )
        # sanity
        if len(out) != len(texts):
            raise RuntimeError(
                f"Inconsistência: len(out)={len(out)} != len(texts)={len(texts)}"
            )
        return out

    def generate(
        self, prompt: str, model: str | None = None, stream: bool = False
    ) -> str:
        """
        Chama /api/generate do Ollama para respostas de linguagem.
        Não afeta call sites atuais (método opcional).
        """
        gen_model = model or os.getenv("LLM_MODEL", "qwen2.5:7b")
        payload = {"model": gen_model, "prompt": prompt, "stream": bool(stream)}
        data = self._post("/api/generate", payload)
        if "error" in data:
            raise RuntimeError(f"Ollama generate error: {data['error']}")
        # API do Ollama quando stream=False retorna 'response'
        return str(data.get("response", "")) or ""
