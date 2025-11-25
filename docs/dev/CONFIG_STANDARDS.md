# Padrões de Configuração em Código — Araquem

## 1. Objetivo deste documento

Este documento define **como o código do Araquem deve lidar com configurações**, em especial:

- Leitura de YAML (policies, thresholds, context, etc.)
- Uso de variáveis de ambiente
- Tratamento de erro em loaders
- Modos degradados explícitos

Ele é o “manual de conduta” para qualquer novo:

- `_load_*_policy`
- `_load_*_thresholds`
- carregamento de RAG, Narrator, context
- ou qualquer integração configurável via `data/` + env.

---

## 2. Classificação obrigatória de configs

Sempre que criar uma nova configuração, **classifique primeiro**:

1. 🟥 **Crítica**   
   - Se estiver ausente ou inválida, o sistema NÃO pode subir.
   - Ex.: `narrator.yaml`, `planner_thresholds.yaml`.

2. 🟧 **Importante (não bloqueante)**   
   - Ausente/ inválida → modo degradado **explícito** (status + error).
   - Ex.: `context.yaml`.

3. 🟦 **Opcional**   
   - Ausente é aceitável, MAS:
     - deve haver log claro
     - fallback controlado e previsível.
   - Ex.: algumas policies experimentais, flags de feature.

### Regra de ouro

> Nunca escreva código sem saber em qual categoria a config se encaixa.

---

## 3. Padrão de loaders YAML

Todo loader de YAML deve seguir este **template conceitual**:

```python
from pathlib import Path
from app.utils.filecache import load_yaml_cached
import logging

LOGGER = logging.getLogger(__name__)

def load_minha_policy(path: str = "data/policies/minha_policy.yaml") -> dict:
    policy_path = Path(path)

    # 1) Classificação da config
    #    (ajustar conforme crítica / importante / opcional)
    if not policy_path.exists():
        LOGGER.warning("Minha policy ausente em %s", policy_path)
        # crítico => raise
        # importante => status 'missing' + {}
        # opcional  => {} aceitável
        return {}

    try:
        data = load_yaml_cached(str(policy_path)) or {}
    except Exception as exc:
        LOGGER.error("Falha ao carregar minha policy", exc_info=True)
        # crítico => raise RuntimeError(...)
        # importante => status 'invalid' + {}
        # opcional  => {} + warning
        raise

    if not isinstance(data, dict):
        LOGGER.error("Minha policy deve ser um mapeamento YAML")
        # crítico => raise RuntimeError(...)
        # importante => status 'invalid'
        raise RuntimeError("Minha policy inválida (não é um dict)")

    # 2) Validações de chaves + tipos (sem regra de negócio embutida)
    # - valida presença de blocos esperados
    # - valida tipos básicos (str, bool, num, lista)
    # - evita bool como número (True/False em lugar de 0/1)
    # - NÃO define faixas de negócio em código

    # 3) Retornar estrutura bruta ou normalizada
    return data

NUNCA fazer

except Exception: pass

retornar {} silenciosamente em config crítica

inventar defaults de thresholds/pesos em código
(isso deve estar em YAML).
```

---

## 4. Variáveis de ambiente

Padrão:

- Ler env o mais próximo possível da fronteira de infra (ex.: caminho de index RAG).
- Tipar imediatamente (int, bool, etc.).
- Validar quando afetar comportamento crítico.

Exemplo correto:

```python
import os

def _read_int_env(name: str, default: int | None = None) -> int | None:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise RuntimeError(f"Env {name} deve ser inteiro, valor atual: {raw}")
    return value
```

Boas práticas

- Para bool, prefira YAML (ex.: llm_enabled, shadow), não env com "true"/"false".
- Para paths (index, policies), valide existência quando o componente for usado.
- Não misturar env solta com YAML definindo a mesma coisa.

---

## 5. Tratamento de erros em configs

### 5.1 Crítica (fail-fast)

- Falha de leitura ou validação → raise (ValueError, RuntimeError, etc.).
- O módulo que depende disso NÃO deve continuar.

Ex.: `_load_narrator_flags`, `_load_thresholds`.

### 5.2 Importante (modo degradado explícito)

- Ausência:
  - status "missing"
  - objeto vazio, mas com log.

- Malformação:
  - status "invalid"
  - error: "<mensagem>"
  - log nível ERROR.

Ex.: `_load_context_policy` + `planner.explain.context`.

### 5.3 Opcional

- Warning no log.
- Fallback documentado (ex.: {}).
- Não impactar roteamento/contrato se estiver ausente.

---

## 6. Logging obrigatório

Sempre que houver try/except em loader ou uso de config:

- Logar com `exc_info=True`.
- Adicionar contexto mínimo: `{ "entity": ..., "intent": ..., "path": ... }` quando couber.
- Nunca engolir exceção em config crítica.

Exemplo:

```python
except Exception as exc:
    LOGGER.error(
        "Falha ao carregar thresholds do planner",
        exc_info=True,
        extra={"path": str(policy_path)},
    )
    raise RuntimeError("Erro ao carregar thresholds do planner") from exc
```

---

## 7. Modos degradados e meta

Quando um módulo operar em modo degradado (RAG, context, etc.), é obrigatório:

- Expor o status em meta ou explain (quando houver).
- Preencher error com mensagem útil (sem stack trace completo).

Exemplos já consolidados:

- `meta["context"].status = "ok" | "missing" | "invalid"`
- `meta["context"].error = "<mensagem>"` (se inválido)
- `meta["rag"].error = "<motivo da falha>"` quando o índice ou embedder caem.

---

## 8. Padrão para novos módulos

Quando criar um novo módulo/config:

1. Decida:
   - Crítico, importante ou opcional?

2. Implemente loader:
   - `Path(...)` + `load_yaml_cached` + validações.

3. Garanta:
   - Logs em caso de falha.
   - Falha explícita para configs críticas.
   - Campos de status/erro em meta ou explain se aplicável.

---

## 9. Anti-padrões proibidos

Os seguintes padrões são proibidos no código novo:

- `_DEFAULTS = {...}` com thresholds/pesos de negócio em código.
- `load_yaml_cached(...); except: return {}` sem log.
- `except Exception: pass` em qualquer ponto de configuração.
- Ajustar comportamento crítico com base em env sem validação.

Qualquer introdução desses padrões deve ser tratada como violação de guardrails.
