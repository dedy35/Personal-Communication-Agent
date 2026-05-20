#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../apps/api"

if [ -d .venv ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

alembic upgrade head
