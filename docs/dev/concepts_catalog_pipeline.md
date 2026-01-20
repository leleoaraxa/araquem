# Concepts Catalog Pipeline

1. Defina a variável de ambiente `BUILD_ID` para identificar a versão do build.
2. Execute o gerador do catálogo para produzir os artefatos determinísticos.
3. Em seguida, rode o refresh existente de embeddings/RAG do projeto.

Exemplo mínimo:

```bash
BUILD_ID=dev-20251030 python scripts/maintenance/build_concepts_catalog.py
```

Essa ordem é obrigatória porque `data/embeddings/index.yaml` referencia os
artefatos gerados em `data/entities/concepts_catalog/`. Se o build não rodar
antes do refresh, o índice de embeddings não encontra os arquivos esperados e
falha.
