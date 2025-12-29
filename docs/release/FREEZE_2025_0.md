# Freeze formal — Araquem 2025.0

## Escopo do freeze
- **O que é:** checkpoint documental/arquitetural para consolidar o estado 2025.0 sem alterar runtime. Mantém RAG e LLM desligados por policy, buckets neutros e payload `/ask` imutável.
- **O que não é:** não inclui reativações de RAG/LLM, mudanças em planner/presenter/context_manager/cache, nem ajustes de SQL ou contratos fora do padrão já estabelecido.

## Checklist do freeze
- [ ] Padronização de cabeçalho em `data/contracts/entities/*.schema.yaml` (`entity == filename`, `name == entity`, `kind: view`, `description` preenchida). *(Pendente conforme bloqueio listado no status canônico.)*
- [ ] Revalidação de cobertura Ontologia ↔ Catálogo ↔ Policies com lint estático/relatório. *(Pendente conforme bloqueio listado no status canônico.)*
- [ ] Baseline de quality datado e commitado (comando, output consolidado, commit/id de data). *(Pendente — status atual mantém quality gate ativo, mas sem evidência formal do baseline.)*
- [ ] Documentação operacional curta do contexto (`docs/dev/M13_CONTEXT_README.md`) cobrindo escopo, TTL, last_reference, limites e anti-casos. *(Pendente — indicado como falta no status.)*
- [ ] Checklist objetivo de smoke pós-deploy (curto, reprodutível) para o blue-green do compose atual. *(Pendente — itens de Infra/Produção ainda não fechados.)*

## Status do freeze: **NÃO APTO**
- Motivo: pendências em contratos/coverage e ausência de baseline formal de quality. Os itens acima precisam de evidência commitada antes de prosseguir.

## Comandos de tag/versionamento (preparados, não executados)
- Preparar tag final: `git tag -a araquem-2025.0 -m "Araquem 2025.0 (após freeze APTO)"` e `git push origin araquem-2025.0`.
- Executar a tag final somente quando status for **APTO**.
- Opcional: usar tag RC como checkpoint (`araquem-2025.0-rc0`) antes de declarar o freeze como APTO.

## Registro documental do freeze
- Data: 2025-12-29
- Tag pretendida: `araquem-2025.0` (somente após APTO)
- Escopo: consolidar estado determinístico (ContextManager por policy, RAG negado, Narrator LLM OFF, buckets neutros).
- Fora do escopo: qualquer alteração de runtime, reativação de RAG/LLM, mudanças em `/ask`, criação de novas entidades ou heurísticas.
