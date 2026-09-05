#!/bin/sh
set -eu

CORE_ROOT=/Users/admin/glm-workspace/Julia_core
ASSISTANT_ROOT=/Users/admin/julia_rd1_controlled/releases/assistant-03de982a3ad60cdbe067fe68e1be1db8a4202de4
MARKET_ROOT=/Users/admin/julia_rd1_controlled/releases/market-d6889f4f39fc4f8adf404ea7c51eee3ad22d7fa7
RUN_ROOT=${JULIA_R9_D1A_RUN_ROOT:-/tmp/rd1-l1-r9-d1a-runtime}

mkdir -p "$RUN_ROOT/state/private" "$RUN_ROOT/logs"
printf '{}\n' > "$RUN_ROOT/state/conversations.json"

export JULIA_BRAIN_ROOT="$ASSISTANT_ROOT"
export JULIA_LEGACY_CONVERSATION_PATH="$RUN_ROOT/state/conversations.json"
export JULIA_PRIVATE_DATA_ROOT="$RUN_ROOT/state/private"
export PYTHONPATH="$CORE_ROOT:$ASSISTANT_ROOT"
export PYTHONDONTWRITEBYTECODE=1
export NO_PROXY=127.0.0.1,localhost
export no_proxy=127.0.0.1,localhost

export JULIA_MARKET_SOURCE_ROOT="$MARKET_ROOT"
export JULIA_MARKET_SOURCE_SHA=d6889f4f39fc4f8adf404ea7c51eee3ad22d7fa7
export JULIA_MARKET_TREE_DIGEST=b07d454ac2c067717c7bdf70fc012c811d9d1636b427dd917134227e0df604dd
export JULIA_MARKET_DB_RUNTIME_DIGEST=19a4765e6e323bebb5b975560fce0a5a4111000844d95804a9dede1458935cff

export DB_TYPE=postgresql
export PG_HOST=localhost
export PG_PORT=5432
export PG_DATABASE=stock_data_test
export PG_SCHEMA=public
export PG_USERNAME=postgres
export JULIA_CONTROLLED_COMPOSITION_ATTESTATION="$RUN_ROOT/composition_attestation.json"

cd "$CORE_ROOT"
exec /opt/miniconda3/bin/python -c 'import asyncio; from julia_core.runtime.capability_bridge import run_controlled_brain; asyncio.run(run_controlled_brain(18090))'
