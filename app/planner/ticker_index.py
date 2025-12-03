from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional, Set

from app.utils.filecache import load_yaml_cached

_DEFAULT_PATH = "data/ontology/ticker_index.yaml"
_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)


def _strip_accents(value: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn"
    )


def _normalize_token(token: str) -> str:
    normalized = _strip_accents(token or "").upper()
    return normalized


def _tokens_from_text(text: str) -> List[str]:
    tokens: List[str] = []
    for match in _WORD_RE.finditer(text or ""):
        token = _normalize_token(match.group(0))
        if token:
            tokens.append(token)
    return tokens


class TickerIndex:
    def __init__(self, path: str = _DEFAULT_PATH):
        raw = load_yaml_cached(path) or {}
        tickers = raw.get("tickers") if isinstance(raw, dict) else None

        canonical_candidates: List[str] = []
        if isinstance(tickers, list):
            for ticker in tickers:
                if isinstance(ticker, str) and ticker.strip():
                    canonical_candidates.append(ticker.strip().upper())

        self._canonical: Set[str] = set(canonical_candidates)

        prefix_map: Dict[str, List[str]] = {}
        for ticker in self._canonical:
            prefix = ticker[:4]
            if len(prefix) != 4:
                continue
            prefix_map.setdefault(prefix, []).append(ticker)

        self._by_prefix4: Dict[str, str] = {
            prefix: values[0] for prefix, values in prefix_map.items() if len(values) == 1
        }

    def resolve(self, token: str) -> Optional[str]:
        token_norm = (token or "").upper()
        if not token_norm:
            return None
        if token_norm in self._canonical:
            return token_norm
        if len(token_norm) == 4:
            return self._by_prefix4.get(token_norm)
        return None


def get_ticker_index(path: str = _DEFAULT_PATH) -> TickerIndex:
    global _TICKER_INDEX
    try:
        index = _TICKER_INDEX
    except NameError:
        index = None
    if index is None:
        index = TickerIndex(path)
        _TICKER_INDEX = index
    return index


def resolve_ticker_from_text(question: str) -> Optional[str]:
    ticker_index = get_ticker_index()
    for token in _tokens_from_text(question):
        resolved = ticker_index.resolve(token)
        if resolved:
            return resolved
    return None


def extract_tickers_from_text(question: str) -> List[str]:
    ticker_index = get_ticker_index()
    seen = set()
    results: List[str] = []
    for token in _tokens_from_text(question):
        resolved = ticker_index.resolve(token)
        if resolved and resolved not in seen:
            results.append(resolved)
            seen.add(resolved)
    return results
