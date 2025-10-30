# GIT_MINIGUIDE.md

## Inicializacao do repositorio
```
git init
git branch -M main
git add .
git commit -m "chore: bootstrap Araquem (M0 guardrails + setup)"
git remote add origin <SEU_REMOTE_GIT_URL>
git push -u origin main
```

## Fluxo de branches (simples e eficaz)
- main: sempre verde (build confiavel)
- feature branches por vertical/escopo curto:
```
git checkout -b feat/m1-nlsql-ask
# ... edita, testa ...
git add -A
git commit -m "feat(core): M1 /ask NL->SQL estavel (tests green)"
git push -u origin feat/m1-nlsql-ask
# abra PR e faca code review
```

## Commits padronizados
- feat(core): ... novas capacidades no nucleo
- fix(gateway): ... correcoes no gateway/contratos
- chore(dev): ... ajustes de tooling/scripts
- docs(dev): ... documentacao de engenharia
- perf(cache): ... otimizacoes de desempenho/cache
- test(planner): ... novos testes ou ajustes

## Tags de release (opcional)
```
git tag -a v0.1.0 -m "Araquem v0.1.0 — M0 guardrails"
git push origin v0.1.0
```

## Checklist de PR (colar na descricao)
- [ ] Payloads e contratos inalterados
- [ ] Sem heuristicas/hardcodes
- [ ] Testes pytest -q verdes
- [ ] Dashboards sem warnings
- [ ] Docs atualizados (se aplicavel)
- [ ] Metricas/Tracing para features novas
