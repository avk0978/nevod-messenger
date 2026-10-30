#!/bin/bash
set -e

mkdir -p /app/data

if [ ! -f /app/data/node.json ]; then
    echo "[nevod] First run — initializing genesis node at ${NEVOD_ADDRESS}..."
    # Registration by invitation code until the owner decides otherwise in the admin
    # panel — an open default let anyone who learned the address register (and take
    # names) before the owner had even logged in.
    exec python nevod.py genesis "${NEVOD_ADDRESS}" \
        --identity data/node.json --db data/node.db --access closed --invite-mode delegated
else
    exec python nevod.py start --identity data/node.json --db data/node.db
fi
