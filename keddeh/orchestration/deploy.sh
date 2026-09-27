#!/bin/sh
set -e

export DB_SECURE_PASSWORD="${DB_SECURE_PASSWORD:-$(openssl rand -hex 24)}"
export REDIS_SECURE_PASSWORD="${REDIS_SECURE_PASSWORD:-$(openssl rand -hex 24)}"

echo "[LOCAL_DEPLOY] Initializing stack setup protocols..."
docker-compose down --volumes --remove-orphans
docker-compose up --build -d database cache_broker

echo "[LOCAL_DEPLOY] Testing database cluster network accessibility..."
docker-compose exec -T database sh -c \
  "until pg_isready -U orchestrator_kernel -d agentic_mainframe; do echo waiting for db; sleep 1; done"

echo "[LOCAL_DEPLOY] Triggering core software agent containers..."
docker-compose up -d agent_node_cluster

echo "[LOCAL_DEPLOY] Bootstrapping functional testing scenarios..."
docker-compose exec -T agent_node_cluster python3 -c "
import sys
from durable_agentic_runtime import WorkerCriticPipeline, ExecutionTrace, NodeDestination
trace = ExecutionTrace(execution_line_code='print(\"System deployment healthy\")', target_ports_verified=[])
final = WorkerCriticPipeline(error_budget_max=2).run(trace)
if final.destination_node != NodeDestination.PRODUCTION_EMIT:
    sys.exit(1)
print('[DEPLOYMENT_VERIFIED] Core Worker-Critic loop compiled accurately inside docker architecture.')
"

echo "[LOCAL_DEPLOY] System state completely deployed."
