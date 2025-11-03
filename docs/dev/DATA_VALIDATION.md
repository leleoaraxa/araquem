# Validação automática dos contratos de dados

**Objetivo**
Garantir coerência entre os contratos YAML e as políticas de dados Araquem.

**Como rodar**
```bash
python scripts/validate_data_contracts.py
```

**Validações realizadas**

* `param_inference.yaml` não define capacidades.
* Cada entidade define `aggregations.defaults` e `aggregations.windows_allowed`.
* Todas as janelas inferidas são suportadas pela entidade.
* Arquivos citados em `embeddings/index.yaml` existem.
* Cada entidade possui `presentation.result_key`.

**Saída esperada**
Linhas `[ok]` e `[fail]` por arquivo; exit code 0 indica sucesso total.

**Integração CI**
Adicionar etapa “Data Contracts Validation” antes do build ou release.
