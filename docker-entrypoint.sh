#!/usr/bin/env sh
set -eu
DATA_DIR="${STORE_DATA_DIR:-/var/lib/ai-khemra-bro}"
mkdir -p "${DATA_DIR}"
exec "$@"
