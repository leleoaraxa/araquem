# app/planner/ticker_index.py
from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional, Set
import logging

from app.utils.filecache import load_yaml_cached

_DEFAULT_PATH = "data/ontology/ticker_index.yaml"
_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)
_LOG = logging.getLogger("planner.ticker_index")


def _strip_accents(value: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", value)
        if unicodedata.category(c) != "Mn"
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
        self._enable_exact = False
        self._enable_prefix4 = False

        if isinstance(raw.get("rules"), list):
            for rule in raw["rules"]:
                if not isinstance(rule, dict) or not rule.get("enabled"):
                    continue
                transforms = rule.get("transforms")
                if not isinstance(transforms, list):
                    continue
                for transform in transforms:
                    if not isinstance(transform, dict):
                        continue
                    transform_type = transform.get("type")
                    target = transform.get("target")
                    if target != "canonical":
                        continue
                    if transform_type == "exact":
                        self._enable_exact = True
                    if transform_type == "prefix4":
                        self._enable_prefix4 = True

        prefix_map: Dict[str, List[str]] = {}
        if self._enable_prefix4:
            for ticker in self._canonical:
                prefix = ticker[:4]
                if len(prefix) != 4:
                    continue
                prefix_map.setdefault(prefix, []).append(ticker)

        self._by_prefix4: Dict[str, str] = {}
        if self._enable_prefix4:
            self._by_prefix4 = {
                prefix: values[0]
                for prefix, values in prefix_map.items()
                if len(values) == 1
            }

    def resolve(self, token: str) -> Optional[str]:
        token_norm = _normalize_token(token)
        if not token_norm:
            return None
        strategy = None
        resolved = None
        if self._enable_exact and token_norm in self._canonical:
            resolved = token_norm
            strategy = "exact"
        elif self._enable_prefix4 and len(token_norm) == 4:
            resolved = self._by_prefix4.get(token_norm)
            strategy = "prefix4" if resolved else None
        if resolved:
            try:
                _LOG.info(
                    {
                        "planner_phase": "ticker_resolve",
                        "token": token,
                        "token_norm": token_norm,
                        "resolved": resolved,
                        "strategy": strategy,
                    }
                )
            except Exception:
                pass
        return resolved


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
    tokens = _tokens_from_text(question)
    for token in tokens:
        resolved = ticker_index.resolve(token)
        if resolved:
            try:
                _LOG.info(
                    {
                        "planner_phase": "ticker_from_text",
                        "raw_question": question,
                        "token": token,
                        "resolved": resolved,
                        "tokens_count": len(tokens),
                    }
                )
            except Exception:
                pass
            return resolved
    try:
        _LOG.info(
            {
                "planner_phase": "ticker_from_text",
                "raw_question": question,
                "token": None,
                "resolved": None,
                "tokens_count": len(tokens),
            }
        )
    except Exception:
        pass
    return None


def extract_tickers_from_text(question: str) -> List[str]:
    ticker_index = get_ticker_index()
    seen = set()
    results: List[str] = []
    tokens = _tokens_from_text(question)
    for token in tokens:
        resolved = ticker_index.resolve(token)
        if resolved and resolved not in seen:
            results.append(resolved)
            seen.add(resolved)
    try:
        _LOG.info(
            {
                "planner_phase": "ticker_extract_multi",
                "raw_question": question,
                "tokens": tokens,
                "resolved": results,
            }
        )
    except Exception:
        pass
    return results
