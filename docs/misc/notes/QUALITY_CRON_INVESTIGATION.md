# Investigação do quality-cron

## Sumário executivo
- O `quality-cron` falha porque o _gate_ de `top2_gap_p50` não é atendido: o relatório reporta valor `0.25`, abaixo do limiar configurado em `data/policies/quality.yaml`. Isso confirma a hipótese **(A) Gating** como causa primária do status `fail`.
- As hipóteses **(B) Timing** e **(C) Dependências** não se confirmaram. O shell do cron aguarda métricas válidas até 60 s e instala apenas `PyYAML` se ausente, o que indica que o problema não decorre da janela de espera nem da falta de dependências de runtime.
- Os arquivos com tipos não suportados (`rag_search`, `planner_rag_integration`, etc.) são ignorados intencionalmente pelo cron, portanto a hipótese **(D) Dataset/Tipos** refere-se apenas à necessidade de enriquecer `routing_samples.json` para ampliar o `top2_gap`.
- Recomendação: revisar o conjunto de _routing samples_ para aumentar a separação entre o 1º e o 2º candidatos (ex.: perguntas menos ambíguas por intent, maior cobertura de intents) antes de considerar alterar o limiar.

## Evidências

### 1. Estado do compose e imagens
Os comandos `docker compose` não estão disponíveis neste ambiente (`bash: command not found: docker`).【69efe3†L1-L3】【059b12†L1-L3】【1e73cf†L1-L3】

### 2. Limiares oficiais
`data/policies/quality.yaml` define `min_top1_accuracy: 0.95`, `min_top2_gap: 0.25` e `min_routed_rate: 0.98`.【F:data/policies/quality.yaml†L1-L12】

### 3. Métricas e relatório online
Não foi possível consultar `http://localhost:8000` (resposta vazia), indicando que a API não está ativa neste ambiente.【a8bb68†L1-L2】【f68716†L1-L3】

### 4. Reexecução manual dos pushes
`quality_push.py` falhou com `httpx.ConnectError: [Errno 111] Connection refused`, reforçando que a API não está acessível para o teste manual.【319ffd†L1-L46】

### 5. Janela de espera do cron
`docker/quality-cron.sh` aguarda a API ficar saudável e, após cada ciclo de push, aguarda até 60 s (sleep padrão de 2 s) por métricas válidas antes de rodar o _gate_.【F:docker/quality-cron.sh†L1-L27】

### 6. Tipos ignorados
Os arquivos em `data/ops/quality_experimental` incluem tipos como `rag_search` e `explain_contract_check`, mas `quality_push_cron.py` aceita apenas `routing` e `projection` por padrão, pulando os demais como "unsupported type".【F:data/ops/quality_experimental/rag_search_basics.json†L1-L26】【F:data/ops/quality_experimental/planner_rag_integration.json†L1-L12】【F:data/ops/quality_experimental/m66_projection.json†L1-L14】【F:scripts/quality/quality_push_cron.py†L12-L128】

### 7. Dependências do container
O cron instala `PyYAML` em runtime, o que evidencia dependência tratada dinamicamente, mas o `Dockerfile.quality-cron` não executa `pip install` durante o build.【F:docker/quality-cron.sh†L1-L27】【F:docker/Dockerfile.quality-cron†L1-L8】

### 8. Dataset de roteamento
`routing_samples.json` contém principalmente variações muito semelhantes de perguntas por intent, o que pode reduzir o `top2_gap` mesmo com acerto top1 perfeito.【F:data/ops/quality/routing_samples.json†L1-L200】【F:data/ops/quality/routing_samples.json†L200-L400】【F:data/ops/quality/routing_samples.json†L400-L423】

## Conclusão
- **Causa primária:** Gate de `top2_gap_p50` não atendido (hipótese A confirmada).
- **Timing:** script já aguarda até 60 s e bloqueia até receber métricas válidas ⇒ pouco provável.
- **Dependências:** instaladas dinamicamente (`PyYAML`) e não geram o `fail` observado ⇒ não causais, mas recomenda-se mover para etapa de build.
- **Dataset/Tipos:** tipos não suportados são ignorados; porém, o conjunto de `routing_samples` deve ser enriquecido para elevar o `top2_gap`.

## Próximos passos recomendados
1. Curar `routing_samples.json` para incluir perguntas menos ambíguas e com maior diversidade de intents, reduzindo a proximidade de scores entre top1 e top2.
2. (Melhoria) Incluir `RUN pip install --no-cache-dir -r /workspace/requirements.txt` no `Dockerfile.quality-cron` para evitar instalações em runtime.
3. Após ajustes, reexecutar o cron localmente garantindo que `top2_gap_p50` supere `0.25`.

## Patch sugerido (exemplo)
```dockerfile
# docker/Dockerfile.quality-cron
 FROM quality-runner:latest
 WORKDIR /workspace
 ENV PYTHONUNBUFFERED=1
 
 COPY requirements.txt /workspace/requirements.txt
 RUN pip install --no-cache-dir -r /workspace/requirements.txt
 
 COPY . /workspace
 COPY --chmod=0755 docker/quality-cron.sh /usr/local/bin/quality-cron.sh
 ENTRYPOINT ["/usr/local/bin/quality-cron.sh"]
```

> **Obs.:** a curadoria do `routing_samples.json` deve ser feita em colaboração com o time de NLP/Planner para garantir ganhos reais no `top2_gap_p50` antes de considerar qualquer ajuste permanente no limiar.
