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
from typing import Any, Dict, List, Optional, Protocol, Literal

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


def _load_policy() -> Dict[str, Any]:
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
    path = "data/policies/context.yaml"
    try:
        raw = load_yaml_cached(path) or {}
        policy = raw.get("context") or {}

        # merge raso do topo
        merged: Dict[str, Any] = {**DEFAULT_POLICY, **policy}

        # merge dos blocos planner / narrator preservando defaults
        planner_raw = policy.get("planner") or {}
        narrator_raw = policy.get("narrator") or {}

        merged["planner"] = {**DEFAULT_PLANNER_POLICY, **planner_raw}
        merged["narrator"] = {**DEFAULT_NARRATOR_POLICY, **narrator_raw}
        LOGGER.info("Context policy carregada de %s: %r", path, merged)
        return merged
    except Exception as exc:  # pragma: no cover - defensivo
        LOGGER.warning(
            "Falha ao carregar política de contexto de %s (%s). "
            "Usando DEFAULT_POLICY.",
            path,
            exc,
        )
        return dict(DEFAULT_POLICY)


POLICY: Dict[str, Any] = _load_policy()


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
        self._policy: Dict[str, Any] = policy or POLICY

    # -------------------------
    # Propriedades / helpers
    # -------------------------

    @property
    def enabled(self) -> bool:
        return bool(self._policy.get("enabled", False))

    # -------------------------
    # Políticas específicas
    # -------------------------

    @property
    def planner_policy(self) -> Dict[str, Any]:
        return self._policy.get("planner", DEFAULT_PLANNER_POLICY)

    @property
    def narrator_policy(self) -> Dict[str, Any]:
        return self._policy.get("narrator", DEFAULT_NARRATOR_POLICY)

    def planner_allows_entity(self, entity: Optional[str]) -> bool:
        return _entity_allowed(entity, self.planner_policy)

    def narrator_allows_entity(self, entity: Optional[str]) -> bool:
        return _entity_allowed(entity, self.narrator_policy)

    def _max_turns(self) -> int:
        return int(self._policy.get("max_turns", DEFAULT_POLICY["max_turns"]))

    def _ttl_seconds(self) -> int:
        return int(self._policy.get("ttl_seconds", DEFAULT_POLICY["ttl_seconds"]))

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
