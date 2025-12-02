# app/context/context_manager.py
"""
Context Manager conversacional do Araquem.

Objetivo:
    - Definir o CONTRATO para memória de contexto entre perguntas,
      sem alterar o payload do /ask.
    - Aplicar políticas declarativas (data/policies/context.yaml).
    - Oferecer uma API estável para Orchestrator / Planner / Narrator.
    - Políticas são baseadas em ENTIDADES reais (data/entities/*).

Importante:
    - Este módulo, por enquanto, NÃO está plugado em lugar nenhum.
      Ou seja, não altera o comportamento atual do Araquem.
    - Backend default é in-memory, apenas para desenvolvimento/testes.
      Backends reais (ex.: Redis) podem ser adicionados depois,
      implementando o protocolo ContextBackend.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Literal, Tuple

from app.utils.filecache import load_yaml_cached

LOGGER = logging.getLogger(__name__)


Role = Literal["user", "assistant", "system"]


@dataclass
class ConversationTurn:
    """
    Representa um "turno" de conversa dentro de um mesmo conversation_id.

    Campos:
        role:    "user", "assistant" ou "system"
        content: texto bruto da mensagem
        created_at: timestamp em segundos (time.time())
        meta:   dicionário livre para informações adicionais
                (ex.: intent, entity, snippet_ids etc.)
    """

    role: Role
    content: str
    created_at: float
    meta: Optional[Dict[str, Any]] = None


DEFAULT_PLANNER_POLICY: Dict[str, Any] = {
    "enabled": True,
    "max_turns": 2,
    # Filtros por entidade; listas vazias significam "sem filtro"
    "allowed_entities": [],
    "denied_entities": [],
}


DEFAULT_NARRATOR_POLICY: Dict[str, Any] = {
    "enabled": True,
    "inject_history": True,
    "max_turns": 3,
    "max_chars": 2000,
    "allowed_entities": [],
    "denied_entities": [],
}


DEFAULT_POLICY: Dict[str, Any] = {
    # Liga/desliga memória conversacional globalmente
    "enabled": False,
    # Quantidade máxima de turns recentes a manter por conversa
    "max_turns": 4,
    # TTL em segundos para considerar um turn ainda válido
    # (0 ou negativo = sem TTL)
    "ttl_seconds": 3600,
    # Limite total (soma dos turns) em caracteres para prompts
    "max_chars": 4000,
    "planner": DEFAULT_PLANNER_POLICY,
    "narrator": DEFAULT_NARRATOR_POLICY,
}

DEFAULT_LAST_REFERENCE_POLICY: Dict[str, Any] = {
    "enable_last_ticker": False,
    "allowed_entities": [],
    "max_age_turns": 0,
}


def _load_policy(path: str = "data/policies/context.yaml") -> Tuple[Dict[str, Any], str, Optional[str]]:
    """
    Carrega política de contexto de data/policies/context.yaml, se existir.

    Estrutura esperada (sugestão):

        terms:
          - name: "context"
            kind: "policy"
            scope: "context"
            version: 1

        context:
          enabled: true
          max_turns: 4
          ttl_seconds: 3600
          max_chars: 4000

          planner:
            enabled: true
            max_turns: 2
            allowed_entities:
              - fiis_precos
            denied_entities: []

          narrator:
            enabled: true
            inject_history: true
            max_turns: 3
            max_chars: 2000
            allowed_entities:
              - fiis_precos
            denied_entities: []

    Se o arquivo não existir ou estiver inválido, usa DEFAULT_POLICY.
    """
    policy_path = Path(path)
    if not policy_path.exists():
        error = f"Política de contexto ausente em {policy_path}"
        LOGGER.warning("%s; usando DEFAULT_POLICY", error)
        return dict(DEFAULT_POLICY), "missing", error

    try:
        raw = load_yaml_cached(str(policy_path)) or {}
        if not isinstance(raw, dict):
            raise ValueError("context.yaml deve ser um mapeamento")

        policy = raw.get("context") or {}
        if policy and not isinstance(policy, dict):
            raise ValueError("Bloco 'context' deve ser um mapeamento")

        merged: Dict[str, Any] = {**DEFAULT_POLICY, **policy}

        planner_raw = policy.get("planner") if isinstance(policy, dict) else None
        narrator_raw = policy.get("narrator") if isinstance(policy, dict) else None

        if planner_raw and not isinstance(planner_raw, dict):
            raise ValueError("context.planner deve ser um mapeamento")
        if narrator_raw and not isinstance(narrator_raw, dict):
            raise ValueError("context.narrator deve ser um mapeamento")

        merged["planner"] = {
            **DEFAULT_PLANNER_POLICY,
            **(planner_raw or {}),
        }
        merged["narrator"] = {
            **DEFAULT_NARRATOR_POLICY,
            **(narrator_raw or {}),
        }
        last_ref_raw = policy.get("last_reference") if isinstance(policy, dict) else None
        merged["last_reference"] = {
            **DEFAULT_LAST_REFERENCE_POLICY,
            **(last_ref_raw or {}),
        }
        LOGGER.info("Context policy carregada de %s: %r", policy_path, merged)
        return merged, "ok", None
    except Exception as exc:  # pragma: no cover - defensivo
        LOGGER.error(
            "Falha ao carregar política de contexto de %s; usando DEFAULT_POLICY",
            policy_path,
            exc_info=True,
        )
        return dict(DEFAULT_POLICY), "invalid", str(exc)


POLICY, POLICY_STATUS, POLICY_ERROR = _load_policy()


class ContextBackend(Protocol):
    """
    Protocolo de backend para armazenamento de contexto.

    Implementações possíveis:
        - In-memory (desenvolvimento / testes)
        - Redis
        - Postgres
        - etc.
    """

    def load(self, client_id: str, conversation_id: str) -> List[ConversationTurn]: ...

    def save(
        self,
        client_id: str,
        conversation_id: str,
        turns: List[ConversationTurn],
    ) -> None: ...


class InMemoryBackend:
    """
    Backend in-memory simplificado, adequado apenas para desenvolvimento.

    Importante:
        - Não é persistente.
        - Não é seguro para múltiplos processos/workers.
    """

    def __init__(self) -> None:
        self._store: Dict[str, List[ConversationTurn]] = {}

    @staticmethod
    def _key(client_id: str, conversation_id: str) -> str:
        return f"{client_id}:{conversation_id}"

    def load(self, client_id: str, conversation_id: str) -> List[ConversationTurn]:
        key = self._key(client_id, conversation_id)
        return list(self._store.get(key, []))

    def save(
        self,
        client_id: str,
        conversation_id: str,
        turns: List[ConversationTurn],
    ) -> None:
        key = self._key(client_id, conversation_id)
        self._store[key] = list(turns)


class ContextManager:
    """
    Fachada principal para Gerenciamento de Contexto Conversacional.

    Uso típico (no futuro):
        cm = ContextManager()  # backend default in-memory
        history = cm.load_recent(client_id, conversation_id)
        cm.append_turn(client_id, conversation_id, role="user", content=question)
    """

    def __init__(
        self,
        backend: Optional[ContextBackend] = None,
        policy: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._backend: ContextBackend = backend or InMemoryBackend()
        self._last_reference: Dict[str, LastReference] = {}
        self._turn_counters: Dict[str, int] = {}
        if policy is not None:
            self._policy = policy
            self._policy_status = "ok"
            self._policy_error = None
        else:
            self._policy, self._policy_status, self._policy_error = _load_policy()

    # -------------------------
    # Propriedades / helpers
    # -------------------------

    @property
    def enabled(self) -> bool:
        return bool(self._policy.get("enabled", False))

    @property
    def policy_status(self) -> str:
        return getattr(self, "_policy_status", "ok")

    @property
    def policy_error(self) -> Optional[str]:
        return getattr(self, "_policy_error", None)

    # -------------------------
    # Políticas específicas
    # -------------------------

    @property
    def planner_policy(self) -> Dict[str, Any]:
        return self._policy.get("planner", DEFAULT_PLANNER_POLICY)

    @property
    def narrator_policy(self) -> Dict[str, Any]:
        return self._policy.get("narrator", DEFAULT_NARRATOR_POLICY)

    @property
    def last_reference_policy(self) -> Dict[str, Any]:
        raw = self._policy.get("last_reference") if isinstance(self._policy, dict) else None
        merged = {**DEFAULT_LAST_REFERENCE_POLICY, **(raw or {})}
        try:
            merged["max_age_turns"] = int(merged.get("max_age_turns", 0))
        except (TypeError, ValueError):
            merged["max_age_turns"] = 0
        allowed = merged.get("allowed_entities") or []
        merged["allowed_entities"] = [str(e) for e in allowed if e]
        merged["enable_last_ticker"] = bool(merged.get("enable_last_ticker", False))
        return merged

    @staticmethod
    def _ticker_from_identifiers(
        identifiers: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        if not identifiers or not isinstance(identifiers, dict):
            return None

        ticker = identifiers.get("ticker")
        if isinstance(ticker, str) and ticker:
            return ticker

        tickers = identifiers.get("tickers")
        if isinstance(tickers, list) and len(tickers) == 1:
            first = tickers[0]
            if isinstance(first, str) and first:
                return first
        return None

    def last_reference_allows_entity(self, entity: Optional[str]) -> bool:
        """Verifica se o uso de last_reference é permitido para a entidade.

        Regras globais:
            - contexto precisa estar habilitado;
            - last_reference.enable_last_ticker deve ser verdadeiro;
            - se last_reference.allowed_entities estiver preenchido, a entidade
              deve estar nela; caso contrário, qualquer entidade é aceita.
        """

        if not self.enabled:
            return False

        policy = self.last_reference_policy
        if not policy.get("enable_last_ticker"):
            return False

        allowed = policy.get("allowed_entities") or []
        if allowed and entity not in allowed:
            return False

        return True

    def planner_allows_entity(self, entity: Optional[str]) -> bool:
        return _entity_allowed(entity, self.planner_policy)

    def narrator_allows_entity(self, entity: Optional[str]) -> bool:
        return _entity_allowed(entity, self.narrator_policy)

    # --------- limites globais e por escopo ---------

    def _max_turns(self) -> int:
        return int(self._policy.get("max_turns", DEFAULT_POLICY["max_turns"]))

    def _ttl_seconds(self) -> int:
        return int(self._policy.get("ttl_seconds", DEFAULT_POLICY["ttl_seconds"]))

    def planner_max_turns(self) -> int:
        """
        Limite de turns que o Planner deve considerar, vindo de
        context.planner.max_turns (fallback para context.max_turns).
        """
        try:
            return int(self.planner_policy.get("max_turns", self._max_turns()))
        except (TypeError, ValueError):
            return self._max_turns()

    def narrator_max_turns(self) -> int:
        """
        Limite de turns que o Narrator deve considerar, vindo de
        context.narrator.max_turns (fallback para context.max_turns).
        """
        try:
            return int(self.narrator_policy.get("max_turns", self._max_turns()))
        except (TypeError, ValueError):
            return self._max_turns()

    def narrator_max_chars(self) -> int:
        """
        Limite de caracteres do histórico que o Narrator pode receber,
        vindo de context.narrator.max_chars (fallback para context.max_chars).
        """
        try:
            return int(self.narrator_policy.get("max_chars", self.max_chars()))
        except (TypeError, ValueError):
            return self.max_chars()

    # -------------------------
    # API pública
    # -------------------------

    def load_recent(
        self,
        client_id: str,
        conversation_id: str,
    ) -> List[ConversationTurn]:
        """
        Carrega o histórico recente para um (client_id, conversation_id),
        aplicando TTL e limite de max_turns.
        """
        if not self.enabled:
            return []

        now = time.time()
        ttl = self._ttl_seconds()
        max_turns = self._max_turns()

        turns = self._backend.load(client_id, conversation_id)
        if not turns:
            return []

        if ttl > 0:
            turns = [t for t in turns if (now - t.created_at) <= ttl]

        if max_turns > 0 and len(turns) > max_turns:
            turns = turns[-max_turns:]

        return turns

    def _conversation_key(self, client_id: str, conversation_id: str) -> str:
        return f"{client_id}:{conversation_id}"

    def _increment_turn_counter(self, client_id: str, conversation_id: str) -> int:
        key = self._conversation_key(client_id, conversation_id)
        current = self._turn_counters.get(key, 0) + 1
        self._turn_counters[key] = current
        return current

    def current_turn_index(self, client_id: str, conversation_id: str) -> int:
        """Retorna o contador lógico de turns já registrados para a conversa."""

        key = self._conversation_key(client_id, conversation_id)
        return int(self._turn_counters.get(key, 0))

    def max_chars(self) -> int:
        """
        Limite global (context.max_chars) para histórico em prompts.

        Detalhe:
            - Escopos específicos (planner/narrator) podem ter limites
              menores (ex.: narrator.max_chars).
            - Quem consome (Planner/Narrator) decide como aplicar isso.
        """
        return int(self._policy.get("max_chars", DEFAULT_POLICY["max_chars"]))

    def append_turn(
        self,
        client_id: str,
        conversation_id: str,
        role: Role,
        content: str,
        meta: Optional[Dict[str, Any]] = None,
        created_at: Optional[float] = None,
    ) -> None:
        """
        Acrescenta um novo turno à conversa, respeitando a política.

        Observação:
            - Se o contexto estiver desabilitado (enabled = False),
              a chamada é um no-op.
        """
        if not self.enabled:
            return

        ts = created_at if created_at is not None else time.time()
        turn = ConversationTurn(role=role, content=content, created_at=ts, meta=meta)

        self._increment_turn_counter(client_id, conversation_id)

        turns = self._backend.load(client_id, conversation_id)
        turns.append(turn)

        # Reaplica política de corte antes de salvar
        now = time.time()
        ttl = self._ttl_seconds()
        max_turns = self._max_turns()

        if ttl > 0:
            turns = [t for t in turns if (now - t.created_at) <= ttl]

        if max_turns > 0 and len(turns) > max_turns:
            turns = turns[-max_turns:]

        self._backend.save(client_id, conversation_id, turns)

    def update_last_reference(
        self,
        client_id: str,
        conversation_id: str,
        *,
        ticker: Optional[str],
        entity: Optional[str] = None,
        intent: Optional[str] = None,
    ) -> None:
        """Atualiza a última referência explícita de ticker para a conversa."""

        if not self.enabled:
            return

        policy = self.last_reference_policy
        if not policy.get("enable_last_ticker"):
            return

        if not ticker:
            return

        if entity and not self.last_reference_allows_entity(entity):
            return

        key = self._conversation_key(client_id, conversation_id)
        now = time.time()
        turn_index = self._turn_counters.get(key, 0)
        self._last_reference[key] = LastReference(
            ticker=str(ticker),
            entity=entity,
            intent=intent,
            updated_at=now,
            turn_index=turn_index,
        )

    def get_last_reference(
        self, client_id: str, conversation_id: str
    ) -> Optional[LastReference]:
        """Retorna a última referência respeitando as políticas de contexto."""

        try:
            last_ref, _ = self._get_last_reference_with_status(client_id, conversation_id)
            return last_ref
        except Exception:  # pragma: no cover - defensivo
            LOGGER.warning("Falha ao recuperar last_reference", exc_info=True)
            return None

    def _get_last_reference_with_status(
        self, client_id: str, conversation_id: str
    ) -> Tuple[Optional[LastReference], str]:
        if not self.enabled:
            return None, "context_disabled"

        policy = self.last_reference_policy
        if not policy.get("enable_last_ticker"):
            return None, "last_reference_disabled"

        key = self._conversation_key(client_id, conversation_id)
        last_ref = self._last_reference.get(key)
        if not isinstance(last_ref, LastReference):
            return None, "no_candidate"

        if not getattr(last_ref, "ticker", None):
            return None, "no_candidate"

        max_age_turns = policy.get("max_age_turns") or 0
        if max_age_turns > 0:
            current_turn = self._turn_counters.get(key, 0)
            if (current_turn - last_ref.turn_index) > max_age_turns:
                return None, "expired"

        return last_ref, "ok"

    def resolve_last_reference(
        self,
        *,
        client_id: str,
        conversation_id: str,
        entity: Optional[str],
        identifiers: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Resolve herança de ticker segundo políticas de contexto.

        Retorna dict com:
            - identifiers_resolved: identifiers possivelmente enriquecidos
            - last_reference_used: bool indicando uso de herança
            - last_reference_ticker: ticker herdado (ou None)
            - reason: string com o caminho decisório
        """

        resolved_identifiers = dict(identifiers or {})
        existing = self._ticker_from_identifiers(resolved_identifiers)

        if not self.enabled:
            return {
                "identifiers_resolved": resolved_identifiers,
                "last_reference_used": False,
                "last_reference_ticker": None,
                "reason": "context_disabled",
            }

        policy = self.last_reference_policy
        if not policy.get("enable_last_ticker"):
            return {
                "identifiers_resolved": resolved_identifiers,
                "last_reference_used": False,
                "last_reference_ticker": None,
                "reason": "last_reference_disabled",
            }

        if not entity:
            return {
                "identifiers_resolved": resolved_identifiers,
                "last_reference_used": False,
                "last_reference_ticker": None,
                "reason": "no_entity",
            }

        allowed_entities = policy.get("allowed_entities") or []
        if allowed_entities and entity not in allowed_entities:
            return {
                "identifiers_resolved": resolved_identifiers,
                "last_reference_used": False,
                "last_reference_ticker": None,
                "reason": "entity_not_allowed",
            }

        if existing:
            return {
                "identifiers_resolved": resolved_identifiers,
                "last_reference_used": False,
                "last_reference_ticker": None,
                "reason": "input_has_ticker",
            }

        last_ref, status = self._get_last_reference_with_status(client_id, conversation_id)
        if status != "ok" or not last_ref:
            return {
                "identifiers_resolved": resolved_identifiers,
                "last_reference_used": False,
                "last_reference_ticker": None,
                "reason": status,
            }

        resolved_identifiers["ticker"] = last_ref.ticker

        return {
            "identifiers_resolved": resolved_identifiers,
            "last_reference_used": True,
            "last_reference_ticker": last_ref.ticker,
            "reason": "last_reference_applied",
        }

    @staticmethod
    def to_wire(turns: List[ConversationTurn]) -> List[Dict[str, Any]]:
        """
        Converte uma lista de ConversationTurn em lista de dicts,
        pronta para ser injetada em prompts (Planner/Narrator).
        """
        return [asdict(t) for t in turns]


def _entity_allowed(entity: Optional[str], scope_policy: Dict[str, Any]) -> bool:
    """
    Aplica a regra (allowed_entities / denied_entities) para um escopo.

    Regras:
        - Se entity for vazia/None → False (não há o que herdar).
        - Se scope.enabled for False → False.
        - Se entity estiver em denied_entities → False.
        - Se allowed_entities estiver vazio → True (modo "whitelist vazia").
        - Caso contrário → True somente se entity estiver em allowed_entities.

    Isso garante:
        - Nada de contexto em entidades proibidas.
        - Possibilidade de operar via whitelist ou blacklist.
    """
    if not entity:
        return False

    if not scope_policy.get("enabled", True):
        return False

    allowed = scope_policy.get("allowed_entities") or []
    denied = scope_policy.get("denied_entities") or []

    if entity in denied:
        return False

    if not allowed:
        # sem allowed_entities configurado -> tudo liberado (exceto denied)
        return True

    return entity in allowed

@dataclass
class LastReference:
    """Representa a última referência explícita feita pelo usuário.

    Campos:
        ticker:     ticker inferido/fornecido na última resposta bem-sucedida.
        entity:     entidade associada ao ticker (quando aplicável).
        intent:     intent que originou a referência.
        updated_at: timestamp do turno em que foi registrada.
        turn_index: contador lógico de turns no momento do registro.
    """

    ticker: Optional[str]
    entity: Optional[str]
    intent: Optional[str]
    updated_at: float
    turn_index: int
