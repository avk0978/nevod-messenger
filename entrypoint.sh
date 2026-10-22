#!/bin/bash
set -e

mkdir -p /app/data

if [ ! -f /app/data/node.json ]; then
    echo "[nevod] First run — initializing genesis node at ${NEVOD_ADDRESS}..."
    exec python nevod.py genesis "${NEVOD_ADDRESS}" \
        --identity data/node.json --db data/node.db --access closed
else
    exec python nevod.py start --identity data/node.json --db data/node.db
fi
