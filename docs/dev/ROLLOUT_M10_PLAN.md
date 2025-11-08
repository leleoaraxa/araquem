# Plano de Rollout — M10 Narrator

**Objetivo:** habilitar a camada de expressão sem regressão.

## Fases
1. Shadow (D0–D7) — `NARRATOR_SHADOW=true`, `NARRATOR_ENABLED=false`. Coletar latência, dif de texto, consistência factual.
2. Canário (D8–D14) — `NARRATOR_ENABLED=true` para 20% das rotas: cadastro e precos (baixa variância).
3. Expansão (D15–D21) — incluir metricas (risk, revenue) quando consistência > 0.98.
4. GA (D22+) — 100% intents; monitoramento contínuo.

## KPIs
- Regressão funcional = 0
- Consistência factual > 0.98
- Reclamações de estilo < 0.5%
- P95 latência adicional < 250ms (local) / < 700ms (remoto)
