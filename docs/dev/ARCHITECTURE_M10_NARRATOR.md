# Arquitetura M10 — Camada Narrator (Expressão)

**Data:** 2025-11-08T17:54:08
**Responsável:** SIRIOS · Araquem  
**Objetivo:** Introduzir uma camada de **expressão** (Narrator) entre Executor (fatos) e Responder (UI), sem regressão funcional.

---

## 1. Visão de alto nível

```
Usuário → Planner → Builder → Executor → (NOVO) Narrator → Responder
                       ↑                     ↑            ↑
                    Ontologia               Estilo       Canal (chat, e-mail, PDF)
                      (M9)                  (M10)         (M10+)
```

- **Planner (M9):** continua responsável por *entender e rotear* (intenção/entidade).
- **Executor (M9):** continua responsável por *retornar fatos* (JSON) a partir dos contratos SQL.
- **Narrator (M10):** *transforma fatos em narrativa natural*, aplica tom de voz, contexto, e resolve ambiguidade textual.
- **Responder (M10+):** entrega o texto no formato do canal (markdown, HTML, WhatsApp, voz).

## 2. Princípios de não regressão

1. **Shadow mode**: Narrator roda em paralelo, mas **não substitui** a resposta atual; logamos difs (texto gerado vs. atual).
2. **Feature flags** (env/flag): `NARRATOR_ENABLED=false` por padrão em produção; ligar por rota/intent e usuário.
3. **Contratos imutáveis**: o payload do Executor **não muda** (mesmo JSON), o Narrator só lê.
4. **Quality gates**: `scripts/quality` continuam válidos; adicionamos um novo gate de forma **não bloqueante** (avalia estilo).
5. **Rollback trivial**: desligar flag volta ao comportamento M9 instantaneamente.

## 3. Interfaces

### 3.1. Contrato Executor → Narrator (JSON)

- Ver documento `CONTRACT_executor_narrator.json` (neste pacote).

### 3.2. API Python do Narrator

```python
class Narrator:
    def __init__(self, model="mistral:instruct", style="executivo"):
        ...

    def render(self, question: str, facts: dict, meta: dict) -> dict:
        '''
        question: string original do usuário
        facts: payload do Executor (ver contrato)
        meta: {'intent': 'metricas', 'entity': 'fiis_metrics', 'locale': 'pt-BR'}
        return:
          { 'text': '...', 'hints': {}, 'score': 0.0, 'tokens': {} }
        '''
```

## 4. Estratégia de Prompting (MVP)

- **System prompt**: tom de voz padrão SIRIOS (vide `PROMPTS_narrator.md`).
- **Few-shot por intent**: exemplos curtos por `intent/entity` com ênfase em *como falar* (não *o que falar*).
- **RAG opcional**: só para estilo (não para inventar fatos); o único *source of truth* é `facts`.

## 5. Métricas

- **latencia_narrator_ms** (p50, p95)
- **consist_fatos** (% de campos presentes citados corretamente)
- **leiturabilidade** (FK grade ~ alvo 8–12)
- **compactacao** (tokens por resposta, alvo por canal)
- **aderencia_tom** (score 0..1 por classificador leve)

## 6. Rollout (Resumo)

- Semana 1: shadow em `metricas/*` para 5% dos usuários internos; logs somente.
- Semana 2: canário 20% em intents com baixa variância (cadastro, precos).
- Semana 3: 100% em canais internos; aval coletivo; liberar para produção com flag.

## 7. Riscos e mitigação

- **Alucinação**: prompt bloqueia fontes externas; só `facts`. Validador pós-geração recusa menções a campos inexistentes.
- **Latência**: modelos leves locais (`phi-3`, `mistral`) + cache de scaffolds por intent.
- **Tom inadequado**: fine-tuning leve do classificador de estilo (não do LLM), com feedback explícito.

## 8. Próximos passos

1. Implementar `Narrator` (classe + flag).
2. Criar 5 few-shots por intent prioritário.
3. Habilitar shadow log + diffs de texto.
4. Adicionar gate de estilo (não bloqueante) em `quality_gate_check.sh`.
