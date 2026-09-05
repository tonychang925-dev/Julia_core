#!/bin/sh
set -eu

CORE_ROOT=/Users/admin/glm-workspace/Julia_core
ASSISTANT_ROOT=/Users/admin/julia_rd1_controlled/releases/assistant-03de982a3ad60cdbe067fe68e1be1db8a4202de4
MARKET_ROOT=/Users/admin/julia_rd1_controlled/releases/market-f0aae447654bc50100bc6a26a3e204fbdac6a707
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
export JULIA_MARKET_SOURCE_SHA=f0aae447654bc50100bc6a26a3e204fbdac6a707
export JULIA_MARKET_TREE_DIGEST=34f72e3ac3d025c05e18814f76d75999ed385baa865b5263dbfb64eab20805f4
export JULIA_MARKET_DB_RUNTIME_DIGEST=23bc6dcf76650700353150f2eb95773169d14a3708293ac8b7826cde4f6b7454

export DB_TYPE=postgresql
export PG_HOST=localhost
export PG_PORT=5432
export PG_DATABASE=stock_data_test
export PG_SCHEMA=public
export PG_USERNAME=postgres
export JULIA_CONTROLLED_COMPOSITION_ATTESTATION="$RUN_ROOT/composition_attestation.json"

cd "$CORE_ROOT"
exec /opt/miniconda3/bin/python -c 'import asyncio; from julia_core.runtime.capability_bridge import run_controlled_brain; asyncio.run(run_controlled_brain(18090))'
