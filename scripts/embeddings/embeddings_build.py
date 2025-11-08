#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: embeddings_build.py
Purpose: Regenerar o índice RAG lendo configurações declarativas e chamando o gerador de embeddings.
Compliance: Guardrails Araquem v2.1.1
"""

from __future__ import annotations
import os, sys, re, json, argparse, hashlib, yaml, time
from pathlib import Path
from typing import Iterable, List, Dict, Any
from app.rag.ollama_client import OllamaClient

_ENTITY_TAG_PREFIXES = ("entity:", "entity=")


def _extract_entity_from_tags(tags: List[str]) -> str | None:
    """
    Procura por uma tag declarativa de entidade no formato:
      - 'entity:<snake_case_name>'   (preferido)
      - 'entity=<snake_case_name>'   (aceito)
    Retorna o nome da entidade em snake_case (sem validar lista), ou None.
    """
    if not tags:
        return None
    for t in tags:
        if not isinstance(t, str):
            continue
        ts = t.strip()
        if not ts:
            continue
        for pref in _ENTITY_TAG_PREFIXES:
            if ts.lower().startswith(pref):
                val = ts[len(pref) :].strip()
                # normaliza para snake_case simples
                val = val.replace("-", "_").replace(" ", "_")
                return val
    return None


def _to_kebab(s: str) -> str:
    return s.replace("_", "-")


def _read_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return text
    except Exception:
        # fallback para YAML/JSON estruturado → vira texto
        try:
            obj = yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore"))
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            return ""


def _normalize_whitespace(s: str) -> str:
    return re.sub(r"[ \t]+", " ", re.sub(r"\r?\n", "\n", s)).strip()


def _chunk(text: str, max_chars: int, overlap: int) -> List[str]:
    text = _normalize_whitespace(text)
    if not text:
        return []
    chunks, i, n = [], 0, len(text)
    while i < n:
        j = min(i + max_chars, n)
        chunk = text[i:j]
        chunks.append(chunk)
        if j == n:
            break
        i = max(0, j - overlap)
    return chunks


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def build_index(index_path: str, out_dir: str, client: OllamaClient) -> Dict[str, Any]:
    idx = yaml.safe_load(Path(index_path).read_text(encoding="utf-8"))
    version = idx.get("version", 1)
    collection = idx.get("collection", "default")
    model = idx.get("embedding_model", "nomic-embed-text")
    chunk_cfg = idx.get("chunk", {}) or {}
    max_chars = int(chunk_cfg.get("max_chars", 1200))
    overlap = int(chunk_cfg.get("overlap_chars", 120))
    include = idx.get("include", []) or []

    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    out_jsonl = outp / "embeddings.jsonl"
    manifest = {
        "version": version,
        "collection": collection,
        "embedding_model": model,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": str(index_path),
        "docs": [],
    }

    total_chunks = 0
    B = int(os.getenv("EMBED_BATCH_SIZE", "8"))
    with out_jsonl.open("w", encoding="utf-8") as fw:
        for item in include:
            doc_id = str(item.get("id") or "")
            p = Path(item.get("path") or "")
            tags = item.get("tags") or []
            if not doc_id or not p.exists():
                print(f"[skip] {doc_id or '(sem id)'} → not found: {p}")
                continue

            text = _read_text(p)
            if not text.strip():
                print(f"[skip] {doc_id} → empty")
                continue

            chunks = _chunk(text, max_chars=max_chars, overlap=overlap)
            vectors: List[List[float]] = []
            # embarca em lotes pequenos p/ não estourar payload (configurável via EMBED_BATCH_SIZE)
            for i in range(0, len(chunks), B):
                batch = chunks[i : i + B]

                try:
                    embs = client.embed(batch)
                except RuntimeError as e:
                    # fallback item-a-item quando batch falhar
                    print(
                        f"[warn] embed batch falhou ({len(batch)} itens). Fallback item-a-item. Detalhe: {e}"
                    )
                    embs = []
                    for j, t in enumerate(batch):
                        try:
                            single = client.embed([t])
                            if (
                                not single
                                or not isinstance(single, list)
                                or not single[0]
                            ):
                                raise RuntimeError("single empty")
                            embs.append(single[0])
                        except Exception as ee:
                            # grava vetor vazio para preservar alinhamento e permitir diagnosticar depois
                            print(
                                f"[error] embed falhou no item {i+j} (doc={doc_id}): {ee}"
                            )
                            embs.append([])
                # se vier tamanho diferente, mantemos alinhamento, mas marcamos vazios
                if len(embs) != len(batch):
                    print(
                        f"[warn] embed retornou {len(embs)} para {len(batch)}. Normalizando com vetores vazios."
                    )
                    while len(embs) < len(batch):
                        embs.append([])
                    if len(embs) > len(batch):
                        embs = embs[: len(batch)]
                vectors.extend(embs)

            assert len(vectors) == len(chunks)
            for k, (c, v) in enumerate(zip(chunks, vectors)):
                entity_name = _extract_entity_from_tags(tags)
                # Preserva o doc_id declarado, mas prefixa quando houver entidade
                base_doc_id = doc_id
                if entity_name:
                    entity_kebab = _to_kebab(entity_name)
                    prefixed_doc_id = f"entity-{entity_kebab}:{doc_id}"
                else:
                    prefixed_doc_id = doc_id

                rec = {
                    "collection": collection,
                    "doc_id": prefixed_doc_id,
                    "chunk_id": f"{prefixed_doc_id}:{k}",
                    "source_id": base_doc_id,
                    "entity": entity_name,  # útil p/ diagnósticos; não é obrigatório p/ o hints
                    "path": str(p),
                    "tags": tags,
                    "sha": _sha(c),
                    "text": c,
                    "embedding": v if isinstance(v, list) else [],
                }
                fw.write(json.dumps(rec, ensure_ascii=False) + "\n")
                total_chunks += 1

            manifest["docs"].append(
                {
                    "id": doc_id,
                    "path": str(p),
                    "tags": tags,
                    "chunks": len(chunks),
                    "sha_all": _sha(text),
                }
            )

    manifest_path = Path(out_dir) / "manifest.json"
    manifest["last_refresh_epoch"] = int(time.time())
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[manifest] updated {manifest_path}")
    print(f"[done] {total_chunks} chunks → {out_jsonl}")
    return {"chunks": total_chunks, "out": str(out_jsonl)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    client = OllamaClient()
    build_index(args.index, args.out, client)
