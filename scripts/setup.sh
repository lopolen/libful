#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
ENV_FILE="libful_api/config/database_url.env"
DEFAULT_DATABASE_URL="${DATABASE_URL:-sqlite:///./dev.db}"

echo "==> Creating virtual environment in ${VENV_DIR}"
"$PYTHON_BIN" -m venv "$VENV_DIR"

VENV_PYTHON="${VENV_DIR}/bin/python"
VENV_PIP="${VENV_DIR}/bin/pip"

echo "==> Upgrading pip"
"$VENV_PYTHON" -m pip install --upgrade pip

echo "==> Installing project dependencies"
"$VENV_PIP" install -r requirements.txt

if [ ! -f "$ENV_FILE" ]; then
  echo "==> Creating ${ENV_FILE}"
  printf 'DATABASE_URL=%s\n' "$DEFAULT_DATABASE_URL" > "$ENV_FILE"
else
  echo "==> Keeping existing ${ENV_FILE}"
fi

echo "==> Applying database migrations"
"$VENV_DIR/bin/alembic" upgrade head

echo "==> Writing installed package snapshot to requirements.lock.txt"
"$VENV_PIP" freeze > requirements.lock.txt

cat <<'MSG'

Setup complete.

Run the API with:
  source .venv/bin/activate
  uvicorn libful_api.main:app --reload

Open:
  http://127.0.0.1:8000/docs

MSG
