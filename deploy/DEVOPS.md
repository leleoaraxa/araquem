
## 1) Subida do stage com múltiplas réplicas

Executar:

```bash
docker compose -f deploy/docker/docker-compose.stage.yaml up -d --build --scale api=3
```

Verificar:

```bash
docker compose ps
```

**Esperado**

* 3 containers `api` rodando
* 1 `gateway`
* Redis, Ollama, Prometheus, Grafana, Tempo saudáveis

---

## 2) Teste de balanceamento (gateway → múltiplas réplicas)

Executar 10–20 vezes:

```bash
curl -s http://localhost:8000/healthz
```

Depois, verificar logs:

```bash
docker compose logs api | grep healthz
```

**Esperado**

* Logs distribuídos entre múltiplas réplicas do `api`
* Nenhuma falha intermitente

---

## 3) Teste de plan-cache + single-flight

Disparar **20 requests simultâneos** com a **mesma pergunta pública**, por exemplo:

```bash
for i in {1..20}; do
  curl -s http://localhost:8000/ask \
    -H "Content-Type: application/json" \
    -d '{
      "question": "Qual o preço atual do MXRF11?",
      "conversation_id": "load-test-1",
      "client_id": "tester",
      "nickname": "tester"
    }' &
done
wait
```

**Verificar nos logs / métricas**

* Apenas **1 execução pesada** (SQL/LLM)
* Requests subsequentes retornam com:

  * `meta.compute.plan_cache_hit = true`
* Nenhuma explosão de latência

---

## 4) Teste de entidade privada (isolamento por client_id)

Executar a mesma pergunta privada com **client_id diferentes**:

```bash
# client A
curl -s http://localhost:8000/ask -d '{... "client_id":"A"}'

# client B
curl -s http://localhost:8000/ask -d '{... "client_id":"B"}'
```

**Esperado**

* Respostas não compartilham cache
* Cada client gera seu próprio `plan_cache_key`

---

## 5) Teste de saturação do LLM (semáforo)

Definir no stage:

```bash
export NARRATOR_MAX_CONCURRENCY=1
```

Disparar várias perguntas que forcem LLM:

```bash
for i in {1..10}; do
  curl -s http://localhost:8000/ask -d '{ pergunta longa }' &
done
wait
```

**Esperado**

* Parte das respostas vem com:

  * `meta.narrative_overload = true`
  * ou `error = llm_concurrency_limited`
* API **não trava**
* Métrica `services_narrator_llm_requests_total{outcome="overload"}` aparece

---

## 6) Relatório final (obrigatório)

O Codex deve devolver apenas:

* ✅ O que passou
* ⚠️ O que degradou (se houve)
* ❌ O que falhou (se houver)
* Conclusão: **Stage pronto ou não para chat multiusuário**

---

## Veredito técnico

Depois **desse prompt**, a Fase A está **formalmente encerrada**.

A partir daí:

* Ou você coloca usuários reais no chat
* Ou parte para a **Fase B (workers / filas / streaming)** quando as métricas pedirem
