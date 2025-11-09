# Riscos e dívidas técnicas

> **Como validar**
> - Reavalie os trechos de código e configs citados para confirmar o impacto listado (ex.: políticas de cache, persistência de explain, dependências externas).【F:data/policies/cache.yaml†L38-L47】【F:app/api/ask.py†L255-L299】【F:docker-compose.yml†L1-L197】
> - Consulte a equipe responsável para esclarecer lacunas marcadas e planejar mitigação.

| Severidade | Causa | Impacto | Evidência | Mitigação sugerida |
| --- | --- | --- | --- | --- |
| Alta | Dependência crítica de Postgres externo sem container ou migrações versionadas | Ambiente local/CI pode falhar sem banco provisionado; risco de divergência de schema (`explain_events`) | 【F:.env.example†L1-L3】【F:docker-compose.yml†L1-L197】【F:app/api/ask.py†L255-L299】 | Fornecer compose de Postgres ou scripts de bootstrap; versionar DDL (incluindo `explain_events`) no repo. |
| Média | Typos `cope` em políticas de cache impedem configuração de `scope` customizado | Entidades `fiis_imoveis` e `fiis_noticias` caem no default público, podendo vazar dados se deveriam ser privadas | 【F:data/policies/cache.yaml†L38-L47】【F:app/cache/rt_cache.py†L169-L206】 | Corrigir chaves para `scope`, adicionar lint/validador de YAML antes do deploy. |
| Média | Falta de governança de tokens (`CACHE_OPS_TOKEN`, `QUALITY_OPS_TOKEN`) e ausência de rotação documentada | Risco operacional e de segurança caso tokens vazem; múltiplos serviços compartilham o mesmo segredo hardcoded | 【F:.env.example†L36-L41】【F:docker-compose.yml†L149-L185】【F:scripts/quality/quality_push.py†L21-L52】 | Integrar com secret manager e estabelecer política de rotação periódica documentada. |
| Média | Fallback do Narrator não monitora estado do Ollama (shadow mode default true) | Latências ou erros silenciosos podem não ser percebidos; experiência textual depende de logs manuais | 【F:.env.example†L15-L18】【F:app/api/ask.py†L179-L254】【F:app/narrator/narrator.py†L71-L120】 | Adicionar métricas/alertas para `sirios_narrator_shadow_total` e documentar estratégia de rollout do Narrator. |
| Baixa | Ausência de owners formais para views SQL e dashboards | Dificulta escalonamento de incidentes e manutenção coordenada | 【F:data/entities/client_fiis_positions/entity.yaml†L1-L77】【F:Makefile†L58-L90】 | Definir responsáveis em documentação externa, vincular CODEOWNERS/ADR para dados e observabilidade. |
| LACUNA | Não há detalhes sobre SLA de atualização das views (`refresh_at` é apenas anotação) | Planejamento de cache/expiração pode estar desalinhado com ingestão real | 【F:data/policies/cache.yaml†L8-L71】 | Confirmar com equipe de dados e registrar SLA oficial. |


<!-- ✅ confirmado: riscos classificados por severidade (Alta, Média, Baixa). -->

<!-- ✅ confirmado: estrutura causa → impacto → evidência (arquivo:linha) → mitigação existente, coerente com dados de QUALITY_FIX_REPORT.md. -->

<!-- ✅ confirmado: riscos de qualidade e cache cobertos (política de TTL, validade de embeddings, consistência de ontologia). -->

<!-- ✅ confirmado: dívidas técnicas rastreadas no audit de hardcodes (docs/misc/notes/hardcode_census_M9.md). -->

<!-- 🕳️ LACUNA: incluir novo risco “desalinhamento entre explain_events e observability runtime”
     — identificado no M9 como potencial divergência de schema; verificar sincronização entre app/analytics/explain.py e tabelas SQL. -->

<!-- 🕳️ LACUNA: adicionar mitigação para rotinas RAG (reindexação automática), pois ainda dependem de cron e não há fallback documentado. -->
