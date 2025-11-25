🧠 Como usar na prática (fluxo sugerido pelo Sirius)

🌅 De manhã / início da sessão
- Abrir Codex Workspace
- Rodar Prompt SAFE
- Rodar Atualizar workspace
- Conversar / investigar / debater

🔧 Quando quiser mudar código

- Dizer: “GERAR PATCH”
- Rodar Prompt STRICT
- Solicitar o que quer exatamente
- Revisar diff
- Aprovar e aplicar

🌙 Ao encerrar
- Nada. Só reabrir amanhã e sincronizar.


🧠 Sempre lembrar

Código (.py) = motor genérico
- interpretar YAML / ontologia
- aplicar thresholds/diretrizes declaradas
- NUNCA “inventar” regra de negócio por conta própria.

Config (data/policies/*.yaml, data/entities/*, data/contracts/*, data/ontology/*) = contrato de negócio
- pesos
- limites
- estilos de resposta
- textos / templates
- estratégias de RAG / Narrator / Contexto.


# 🚦 **FLUXO RECOMENDADO – QUANDO USAR CADA MODO DO CODEX**

A tabela abaixo é **prática**, **cirúrgica** e totalmente **aplicável na vida real**.

---

# 🧩 **Legenda dos módulos principais**

* **Planner** → interpretação da pergunta, intent, entidades
* **Builder** → gera SQL determinístico
* **Executor/PG** → executa SQL
* **Formatter** → formata as linhas
* **Narrator** → gera o texto final ou usa template
* **RAG** → coleta contexto
* **Orchestrator** → coordena tudo
* **Entities/YAML** → definição contratual do sistema
* **Policies** → comportamentos permitidos/proibidos

---

# 🧠 **1) Modo Curto e Objetivo → mudanças pequenas, rotina**

### ✔ Use quando:

* é uma alteração simples e totalmente controlada
* você já sabe exatamente o que precisa
* não é uma parte crítica do pipeline
* a mudança é “cosmética” ou estrutural leve

### 🔧 Exemplos reais no Araquem:

* ajustar token limit no narrador
* corrigir comentário errado no builder
* melhorar formatação do Formatter
* alterar ordem de imports

### 🟢 Seguro para:

* Formatter
* Presenter
* Scripts `scripts/*.py`
* Ajustes pequenos no Orchestrator

---

# 🔐 **2) Modo Ultra Restrito → partes CRÍTICAS do Araquem**

### ✔ Use quando:

* for alterar algo que **não pode ter inferência**
* você precisa eliminar heurísticas
* mexe com components centrais
* qualquer deslize pode quebrar o sistema

### 🔧 Exemplos reais:

* remover heurística do `prompts.py`
* alterar lógica do Planner (importantíssimo!)
* ajustar o Builder (GENERATE SQL)
* mexer na camada de Policies

### 🔥 Este modo deve ser o padrão para:

* Planner
* Builder
* Narrator (prompt + lógica)
* Policies (data/policies/*.yaml)
* Ontologia (data/entities)

**Se der merda aqui, o Araquem cai.**

---

# 🕵️ **3) Modo Debug-Friendly → investigar antes de mexer**

### ✔ Use quando:

* você quer ENTENDER antes de mudar
* suspeita de heurística escondida
* vai mexer em código legado sensível
* o arquivo é grande e confuso
* quer saber exatamente o impacto antes de alterar

### 🔧 Exemplos reais:

* revisar Planner para detectar heurísticas
* entender porque o RAG tá puxando chunks errados
* analisar fluxos do Orchestrator
* investigar funções do Builder
* revisar entity.yaml grande ou confusa

---

# 📋 **4) Modo Auditoria → diagnóstico puro, sem mexer**

### ✔ Use quando:

* quer uma checagem total de integridade
* antes de passar o Codex para refatorar
* quer ver risco, impacto, suposições
* está fazendo revisão de PR de terceiros

### 🔧 Útil para:

* Orchestrator completo
* Narrator (antes de mudar)
* RAG context builder
* Policies de refresh, cache, quality

---

# 🧪 **5) Modo CI/CD → validação sem alteração**

### ✔ Use quando:

* preparando PR
* integrando novos contribuidores
* criando scripts automáticos de verificação

### 🔧 Exemplos reais:

* garantir que um patch vindo do Codex segue o Guardrails
* validar que ninguém adicionou heurística no Planner
* revisar uma alteração no builder gerada por outro dev

---

# 👮‍♂️ **6) Modo Polícia Federal → caçar gambiarras**

### ✔ Use quando:

* você acha que o GPT (ou alguém) enfiou heurística
* suspeita que o código ganhou “inteligência indevida”
* quer examinar comportamento linha a linha

### 🔧 Exemplos:

* revisar se o Narrator está fazendo inferência não declarada
* procurar “jeitinho” dentro do Planner
* achar fallback indevido no Builder

---

# 🪓 **7) Modo Cirúrgico → alterar o mínimo possível**

### ✔ Use quando:

* você precisa patch pequeno e seguro
* alteração é localizada e sensível
* partes do Araquem onde touch mínimo é crucial

### 🔧 Exemplos:

* ajuste específico no Planner
* corrigir um fallback no Builder
* trocar um valor no narrator.yaml

---

# 🧑‍🏫 **8) Modo Tutor → quando você quer APRENDER**

### ✔ Use quando:

* precisa estudar o arquivo
* quer compreender a arquitetura
* está incorporando parte nova do Araquem

### 🔧 Exemplos:

* “me explica como o Planner resolve intents”
* “me ensina como o RAG reconstroi o contexto”
* “por que o Formatter faz isso?”

---

# 🧪 **9) Modo Sandbox → simular sem aplicar**

### ✔ Use quando:

* quer experimentar ideias
* quer prever o impacto antes de tocar no código
* vai fazer alteração grande depois

### 🔧 Exemplos:

* simular como ficaria o Narrator sem heurísticas
* simular reorganização do Orchestrator
* simular refatoração do RAG policies

---

# 🛡️ **10) Modo Blindado → sem risco de acionar LLM/RAG indevidamente**

### ✔ Use quando:

* alterando partes conectadas a LLM
* manipulando prompts
* mexendo no pipeline do narrator
* reescrevendo RAG context builder

### 🔧 Exemplos:

* alterar prompts.py
* revisar chamadas ao Ollama
* modificar RAG policies
* ajustar os templates do Narrator

---

# 🧠 **MAPA VISUAL – O MODO CERTO PARA CADA PARTE DO ARAQUEM**

| Componente          | Modo Sugerido                    | Observação                  |
| ------------------- | -------------------------------- | --------------------------- |
| **Planner**         | Ultra Restrito / Polícia Federal | Parte mais crítica de todas |
| **Builder (SQL)**   | Ultra Restrito / Debug-Friendly  | Erro aqui = SQL errado      |
| **Narrator Prompt** | Ultra Restrito / Blindado        | Zero heurística             |
| **Narrator Lógica** | Ultra Restrito / Cirúrgico       | Fluxo sensível              |
| **RAG**             | Debug-Friendly / Auditoria       | Precisa entender antes      |
| **RAG Policies**    | Ultra Restrito                   | YAML como contrato          |
| **Orchestrator**    | Debug-Friendly / Auditoria       | Extenso e integrado         |
| **Entities YAML**   | Ultra Restrito                   | Contrato absoluto           |
| **Policies YAML**   | Ultra Restrito                   | Regra do sistema            |
| **Formatter**       | Curto e Objetivo                 | Sem risco alto              |
| **Presenter**       | Curto e Objetivo                 | Zona segura                 |
| **Quality Scripts** | Cirúrgico / Curto                | Não pode quebrar CRON       |
| **Observability**   | Curto e Objetivo                 | Manutenção leve             |
| **Scripts misc**    | Curto                            | Sem risco                   |

---

# 🎯 Conclusão (vale ouro pra você implementar)

**Se mexer em Planner, Builder ou Narrator → MODO ULTRA RESTRITO**
**Se quer entender antes de mexer → DEBUG-FRIENDLY**
**Se é manutenção leve → CURTO E OBJETIVO**
**Se precisa validar PR → CI/CD**
**Se desconfia de gambiarra → POLÍCIA FEDERAL**
**Se o arquivo é sensível → CIRÚRGICO**
**Se é parte LLM/RAG → BLINDADO**
