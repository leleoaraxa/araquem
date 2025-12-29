# Roadmap controlado — Araquem 2025.1

> Este documento descreve evolução futura. Não representa o estado atual.  
> Estado atual: `docs/ARAQUEM_STATUS_2025.md`  
> Freeze 2025.0: `docs/release/FREEZE_2025_0.md`

## Princípios (invariantes)
- /ask imutável
- YAML/ontologia/policies como contrato
- compute-on-read como padrão
- sem hardcode/heurísticas
- RAG/Narrator só via policy e sem tocar números

## P0 — Desbloqueadores (para tornar o freeze 2025.0 APTO)
- Padronização completa dos contratos (`data/contracts/entities/*.schema.yaml`) com lint passando sem avisos. **Critério de aceite:** checklist executado e relatório de lint commitado sem pendências.
- Revalidação de cobertura Ontologia ↔ Catálogo ↔ Policies. **Critério de aceite:** relatório de cobertura commitado apontando 0 gaps críticos.
- Baseline de quality datado e reproduzível. **Critério de aceite:** comando + output armazenados em doc/artefato e vinculados a um commit específico.

## P1 — Consolidação (redução de drift, higiene, confiabilidade)
- Lint contínuo de documentação/coverage com resumos curtos em `docs/dev/`. **Critério de aceite:** pipeline de lint documental reportando sucesso em branch principal.
- Melhoria de relatórios de observabilidade para contexto/last_reference (hit/no-op). **Critério de aceite:** documentação de métricas esperadas e dashboards configurados em ambiente controlado.
- Documentos operacionais mínimos (Context, Quality, Narrator) revisados e alinhados ao estado real. **Critério de aceite:** READMEs atualizados com data/commit de referência.

## P2 — Evolução controlada (somente após freeze APTO)
- Reativação RAG opt-in restrita para intents textuais, com guardrails explícitos. **Critério de aceite:** policy com allowlist limitada, latência e recall monitorados, sem impacto em números.
- Shadow Narrator em dev/staging para entidades textuais selecionadas. **Critério de aceite:** `llm_enabled` apenas em ambientes de teste, coleta de métricas e revisão humana antes de qualquer expansão.
- Compute-mode declarativo “data vs concept” por ontologia/policy. **Critério de aceite:** regra documentada e testada que evita heurísticas e não altera payloads numéricos.

## Fora de escopo (2025.1)
- reativação de LLM como roteador/decisor
- mudanças no payload /ask
- heurísticas em código
- qualquer mudança que altere números fora do SQL
