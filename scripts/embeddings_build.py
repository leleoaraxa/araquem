# scripts/embeddings_build.py
from __future__ import annotations
import os, sys, re, json, argparse, hashlib, yaml, time
from pathlib import Path
from typing import Iterable, List, Dict, Any
from app.rag.ollama_client import OllamaClient


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
            vectors = []
            # embarca em lotes pequenos p/ não estourar payload
            B = 8
            for i in range(0, len(chunks), B):
                batch = chunks[i : i + B]
                embs = client.embed(batch)
                vectors.extend(embs)

            assert len(vectors) == len(chunks)
            for k, (c, v) in enumerate(zip(chunks, vectors)):
                rec = {
                    "collection": collection,
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}:{k}",
                    "path": str(p),
                    "tags": tags,
                    "sha": _sha(c),
                    "text": c,
                    "embedding": v,
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

    (Path(out_dir) / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[done] {total_chunks} chunks → {out_jsonl}")
    return {"chunks": total_chunks, "out": str(out_jsonl)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    client = OllamaClient()
    build_index(args.index, args.out, client)
