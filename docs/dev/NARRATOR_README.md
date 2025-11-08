# SIRIOS Narrator — Drop-in (sem regressão)
Gerado em: 2025-11-08T18:03:21

## O que é
Camada de expressão que transforma o JSON factual do **Executor** em texto natural **sem mexer** na ontologia/roteamento.

## Como adicionar ao repo
Copie as pastas/arquivos para o mesmo layout dentro do seu projeto:
```
app/narrator/__init__.py
app/narrator/prompts.py
app/narrator/narrator.py
scripts/quality/quality_eval_narrator.py
docs/NARRATOR_README.md
config/narrator.env.example
```

## Flags (não alteram nada por padrão)
- `NARRATOR_ENABLED=false`
- `NARRATOR_SHADOW=false`
- `NARRATOR_MODEL=mistral:instruct`

## Uso em shadow (não altera resposta ao usuário)
```python
from app.narrator.narrator import Narrator

narr = Narrator()
if narr.shadow:
    sh = narr.render(question, facts, meta)
    print({"shadow": True, "intent": meta.get("intent"), "entity": meta.get("entity"), "latency_ms": sh["latency_ms"], "score": sh["score"]})
```

## Uso para exibir (opt-in por flag)
```python
narr = Narrator()
if narr.enabled:
    out = narr.render(question, facts, meta)
    final_text = out["text"]
else:
    final_text = legacy_format(facts)  # fluxo atual
```

## Teste rápido
```
python scripts/quality/quality_eval_narrator.py --payload /caminho/payload.json
```
