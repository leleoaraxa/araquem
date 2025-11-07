import json
from pathlib import Path

from app.core.hotreload import get_manifest_hash
from app.rag.index_reader import EmbeddingStore


def _write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _row(doc_id, text, emb):
    return {
        "collection": "test",
        "doc_id": doc_id,
        "chunk_id": "c1",
        "text": text,
        "embedding": emb,
        "tags": [],
    }


def test_manifest_hash_changes_triggers_reload(tmp_path: Path):
    store_dir = tmp_path / "store"
    store_dir.mkdir(parents=True, exist_ok=True)
    jsonl = store_dir / "embeddings.jsonl"
    manifest = store_dir / "manifest.json"

    _write_jsonl(jsonl, [_row("doc-A", "aaa", [1.0, 0.0])])
    manifest.write_text(json.dumps({"tree": "hash-A"}, ensure_ascii=False), encoding="utf-8")

    es1 = EmbeddingStore(str(jsonl))
    rows1 = es1.rows_with_vectors()
    assert any(r["doc_id"] == "doc-A" for r in rows1)

    _write_jsonl(jsonl, [_row("doc-B", "bbb", [0.0, 1.0])])
    manifest.write_text(json.dumps({"tree": "hash-B"}, ensure_ascii=False), encoding="utf-8")

    es2 = EmbeddingStore(str(jsonl))
    rows2 = es2.rows_with_vectors()
    assert any(r["doc_id"] == "doc-B" for r in rows2)
    assert not any(r["doc_id"] == "doc-A" for r in rows2)


def test_missing_manifest_uses_missing_key(tmp_path: Path):
    store_dir = tmp_path / "store"
    store_dir.mkdir(parents=True, exist_ok=True)
    jsonl = store_dir / "embeddings.jsonl"

    _write_jsonl(jsonl, [_row("doc-X", "xxx", [0.5, 0.5])])

    es = EmbeddingStore(str(jsonl))
    assert any(r["doc_id"] == "doc-X" for r in es.rows_with_vectors())

    manifest_hash = get_manifest_hash(str(store_dir / "manifest.json"))
    assert manifest_hash == "missing"
