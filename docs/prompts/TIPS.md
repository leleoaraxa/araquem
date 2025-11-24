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
