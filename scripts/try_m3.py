# scripts/try_m3.py
from app.orchestrator.routing import Orchestrator
from app.planner.planner import Planner
from app.executor.pg import PgExecutor

orch = Orchestrator(Planner("data/ontology/entity.yaml"), PgExecutor())
print(orch.route_question("Qual o CNPJ do VINO11?"))
