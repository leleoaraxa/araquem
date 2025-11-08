# Checklist — Refactor seguro para M10

- [ ] Classe `Narrator` + flag `NARRATOR_ENABLED` (default: false)
- [ ] Ponto de integração: Executor → Narrator → Responder
- [ ] Logs de shadow: pergunta, facts.hash, texto_atual, texto_narrator
- [ ] Testes unitários do Narrator (mocks por intent)
- [ ] Métricas: `latencia_narrator_ms`, `consistencia_fatos`
- [ ] Gate não bloqueante no `quality_gate_check.sh` (optativo)
- [ ] Script `scripts/quality/quality_eval_narrator.py` (comparação)
- [ ] Plano de rollback (flag OFF em produção)
