# 🟦 **ARAQUEM — USER JOURNEY (Jornadas Oficiais do Usuário)**

## *Mapa completo de como o usuário interage com o Araquem, passo a passo, incluindo fluxo cognitivo, entidades acessadas, o papel do Narrator e decisões de UX.*

---


# **0. Propósito**

Este documento define oficialmente:

* As jornadas do usuário
* Como o chat deve se comportar em cada momento
* Como o usuário descobre as funcionalidades
* Como erros/inconsistências são tratados
* Como funciona a navegação mental do usuário no Araquem
* Estados cognitivos (“momento de uso”)
* Como o Narrator converte dados técnicos em experiência fluida

É o **guia canônico para UX + AI do produto Araquem**.

---


# **1. As 5 Jornadas Canônicas**

O Araquem opera sobre **5 grandes jornadas reais**, todas baseadas no comportamento de investidores de FIIs.

As jornadas são:

---

## **1. “Explique pra mim” — Jornada Conceitual**

💡 **Usuário quer aprender algo.**
Não quer número. Quer contexto.

Exemplos:

* “O que é Sharpe?”
* “O que significa IPCA alto para FIIs?”
* “O IFIX subindo é bom pra quem?”
* “Como interpretar vacância alta?”

**Pipeline:**

1. Planner detecta pergunta conceitual (sem ticker).
2. Entidade: `concepts-*` via RAG.
3. Narrator escreve explicação curta e elegante.

**Objetivo da UX:**
Educar sem cansar.
Resposta curta, clara e prática.

**Valor entregue:**
Confiança + entendimento.

---

## **2. “Me mostra os dados” — Jornada Factual com Ticker**

📊 **Usuário quer ver números e interpretar dados de um FII.**

Exemplos:

* “DY do HGLG11 nos últimos meses”
* “Volatilidade do MXRF11”
* “Como está o histórico de preços do KNRI11?”
* “Quais notícias do VISC11?”

**Pipeline:**

1. Planner encontra entidade associada ao ticker.
2. Builder gera SELECT totalmente determinístico.
3. Executor retorna tabela original (sem alterações).
4. Narrator interpreta:

   * “O fundo distribuiu X”
   * “A volatilidade está em Y”
   * “As notícias mostram…”

**Objetivo da UX:**
Tornar o dado “legível” e útil.

**Valor entregue:**
Compreensão rápida + visão clara do FII.

---

## **3. “E pra mim?” — Jornada Privada (Carteira do Cliente)**

🔒 **Usuário logado pedindo análises personalizadas.**

Exemplos:

* “Minha carteira está melhor ou pior que o IFIX?”
* “Estou ganhando da inflação?”
* “Minha renda mensal está crescendo?”

**Entidades:**

* `client_fiis_positions`
* `client_fiis_dividends_evolution`
* `client_fiis_performance_vs_benchmark`

**Pipeline:**

1. Planner reconhece pergunta privada.

2. Checa `client_id` → se ausente:

   > “Essa informação exige login.”

3. Se presente:

   * Query rodando apenas sobre FIIs da carteira.
   * Narrator interpreta valores da carteira.

**Objetivo da UX:**
Mostrar evolução, tendência e contexto da vida real do cliente.

**Valor entregue:**
Sensação de que “a IA me conhece”.

---

## **4. “Deixa eu explorar” — Jornada Navegação Natural**

🌀 **Usuário flui por perguntas adjacentes.**
O Araquem vira um “Google dos FIIs”.

Exemplos:

* “CNPJ do HGLG11”
* “Agora me mostra o risco dele.”
* “E o yield?”
* “Quais imóveis ele tem?”

**Pipeline:**

1. Context Manager ativa “last_reference”
2. Usuário dá follow-up sem ticker
3. Planner entende que é sobre o mesmo fundo
4. UX flui como se fosse uma conversa humana

**Objetivo da UX:**
Zero atrito.
Sensação de inteligência contínua.

**Valor entregue:**
Velocidade + naturalidade.

---

## **5. “E agora?” — Jornada de Incerteza e Desambiguação**

⚠️ **Usuário faz pergunta vaga, genérica ou perigosa.**

Exemplos:

* “Esse fundo é bom?”
* “Quais os melhores FIIs?”
* “Compro ou vendo?”
* “O que fazer com essa queda?”
* “Me recomenda um fundo.”

**Pipeline:**

1. Planner identifica risco regulatório + ambiguidade.
2. Narrator entra em modo “segurança cognitiva”.

Respostas permitidas:

* pedir esclarecimento
* reforçar limites
* oferecer contexto neutro
* explicar o que influencia determinado risco

Respostas proibidas:

* recomendação
* preço alvo
* futurologia
* conselhos pessoais

**Objetivo da UX:**
Proteger o usuário e a SIRIOS sem “parecer robô”.

**Valor entregue:**
Clareza + confiança + segurança.

---


# **2. Relacionando Jornadas x Entidades**

| Jornada            | Entidades principais                         | Modo Narrator                    |
| ------------------ | -------------------------------------------- | -------------------------------- |
| Conceitual         | concepts-fiis, concepts-risk, concepts-macro | Explicação curta                 |
| Factual com ticker | qualquer entidade de FIIs                    | Interpretação + leitura de dados |
| Privada            | client_*                                     | Interpretação personalizada      |
| Navegação natural  | todas suportadas no context                  | Follow-up                        |
| Incerteza          | nenhuma (fallback seguro)                    | Desambiguação + proteção         |

---


# **3. Como o usuário descobre que o Araquem faz tudo isso?**

A descoberta é **progressiva e natural**, com 5 gatilhos:

## **3.1 O usuário pergunta algo simples**

“CNPJ do HGLG11”
→ Ele vê que funciona.

## **3.2 Ele faz follow-up**

“E o risco dele?”
→ Ele percebe memória contextual.

## **3.3 Ele faz uma pergunta conceitual**

“Por que vacância importa?”
→ Aprende que também é educacional.

## **3.4 Ele experimenta uma pergunta privada**

“Minha renda está crescendo?”
→ Vê que o Araquem entende a carteira.

## **3.5 Ele testa perguntas amplas**

“Quais os melhores FIIs?”
→ Araquem desambiguiza com elegância.

É uma progressão natural.
Nenhum popup.
Nenhuma instrução explícita.
**A experiência revela o produto.**

---


# **4. Diretrizes para Comportamento Inteligente**

## **4.1 Não interromper o fluxo do usuário**

Se fizer follow-up sem ticker → aplicar context

## **4.2 Não adivinhar**

Se ambíguo → perguntar

## **4.3 Não travar**

Se entidade retorna vazia → narrador dá saída elegante

## **4.4 Não “encher linguiça”**

Respostas sempre curtas.

## **4.5 Evitar jargões**

Ajudar o usuário a aprender.

## **4.6 Ajudar o usuário a continuar**

Encerramento sempre com:

> “Se quiser, posso mostrar X.”

---


# **5. Erros de UX que o Araquem nunca pode cometer**

* não responder nada
* responder algo muito técnico
* gerar texto imenso
* “vomitar tabela sem explicação”
* usar primeira pessoa emocional
* inventar notícia
* inventar número
* inventar recomendação

---


# **6. Exemplos Oficiais de Jornadas (com fluxo completo)**

## **6.1 Jornada Conceitual**

**User:** o que é vacância alta?
**Planner:** concepts-fiis
**RAG:** chunk conceitual
**Narrator:**

> “Vacância alta significa que uma parte maior dos imóveis do fundo está desocupada.
> Isso reduz o fluxo de aluguel e pode pressionar o rendimento.
> Posso explicar como avaliar o impacto disso.”

---

## **6.2 Jornada Factual**

**User:** yield do HGLG11
**SQL:** retorna 1xN histórico
**Narrator:**

> “Aqui está o histórico recente.
> Um yield mais alto indica maior retorno em relação ao preço atual.
> Se quiser, comparo com o IFIX.”

---

## **6.3 Jornada Privada**

**User:** minha renda mensal está crescendo?
**SQL:** `client_fiis_dividends_evolution`
**Narrator:**

> “Sim, sua renda mensal média subiu nos últimos meses.
> Isso aconteceu principalmente pelos fundos X e Y.
> Posso detalhar por fundo.”

---

## **6.4 Jornada de Navegação Natural**

**User:** CNPJ do HGLG11
**Assistant:** responde
**User:** e o risco?
**Context:** inherited ticker
**Narrator:**

> “O risco do HGLG11 está concentrado em volatilidade moderada e baixo endividamento…”

---

## **6.5 Jornada de Incerteza**

**User:** esse fundo é bom?
**Narrator:**

> “Depende do que você deseja analisar: risco, rendimento, qualidade da carteira ou histórico de dividendos.
> Quer ver qual desses pontos?”

---


# **7. Final — Como este documento será usado**

Este arquivo é referência canônica para:

* UX do front-end
* Prompt do Narrator
* Finetune futuro
* Testes de qualidade
* Treinamento interno
* Auditoria de comportamentos
* Revisão de erros do Planner
* Ajustes no RAG
* Projetar as próximas 10 features do Araquem

---
