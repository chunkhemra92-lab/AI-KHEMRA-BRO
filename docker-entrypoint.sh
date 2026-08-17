#!/usr/bin/env sh
set -eu

APP_USER="appuser"
APP_GROUP="appuser"
DATA_DIR="${AI_KHEMRA_DATA_DIR:-/var/lib/ai-khemra-bro}"
LICENSE_DB_PATH="${LICENSE_DB_PATH:-${DATA_DIR}/licenses.db}"
HF_HOME="${HF_HOME:-/home/appuser/.cache/huggingface}"

mkdir -p "${DATA_DIR}" "${HF_HOME}"
chown -R "${APP_USER}:${APP_GROUP}" "${DATA_DIR}" "${HF_HOME}"

export LICENSE_DB_PATH
export HF_HOME
exec gosu "${APP_USER}:${APP_GROUP}" "$@"
