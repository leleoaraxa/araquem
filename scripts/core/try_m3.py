#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: try_m3.py
Purpose: Instanciar rapidamente o planner/orchestrator para testar roteamento manual.
Compliance: Guardrails Araquem v2.1.1
"""

from app.orchestrator.routing import Orchestrator
from app.planner.planner import Planner
from app.executor.pg import PgExecutor

orch = Orchestrator(Planner("data/ontology/entity.yaml"), PgExecutor())
print(orch.route_question("Qual o CNPJ do VINO11?"))
