#!/bin/sh
set -eu

CORE_ROOT=/Users/admin/glm-workspace/Julia_core
ASSISTANT_ROOT=/Users/admin/julia_rd1_controlled/releases/assistant-3841a3bee5995d67c87b04dc00a0abeebac6f50e
MARKET_ROOT=/Users/admin/julia_rd1_controlled/releases/market-ca939a08726f45e60fc2c80793076865ce21af7c
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

# NCF-A7 A3-4: controlled Brain is a controlled profile => internal token required.
export JULIA_INTERNAL_TOKEN="${JULIA_INTERNAL_TOKEN:-ncf-a7-controlled-brain-token}"

export JULIA_MARKET_SOURCE_ROOT="$MARKET_ROOT"
export JULIA_MARKET_SOURCE_SHA=ca939a08726f45e60fc2c80793076865ce21af7c
export JULIA_MARKET_TREE_DIGEST=34f72e3ac3d025c05e18814f76d75999ed385baa865b5263dbfb64eab20805f4
export JULIA_MARKET_DB_RUNTIME_DIGEST=52c3dffb2e061ed7f32278e65170db1a7b53556acaf46eb9dc43a0ae05a28f24

export DB_TYPE=postgresql
export PG_HOST=localhost
export PG_PORT=5432
export PG_DATABASE=stock_data_test
export PG_SCHEMA=public
export PG_USERNAME=postgres
export JULIA_CONTROLLED_COMPOSITION_ATTESTATION="$RUN_ROOT/composition_attestation.json"

cd "$CORE_ROOT"
exec /opt/miniconda3/bin/python -c 'import asyncio; from julia_core.runtime.capability_bridge import run_controlled_brain; asyncio.run(run_controlled_brain(18090))'
