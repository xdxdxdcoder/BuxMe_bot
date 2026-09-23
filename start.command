#!/bin/bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_DIR="$(cd && pwd)"
BUNDLED_NODE_DIR="$USER_DIR/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin"
BUNDLED_TOOLS_DIR="$USER_DIR/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback"

cd "$PROJECT_DIR"

# Codex Desktop содержит собственный Node.js. Если проект запускают вне Codex,
# скрипт использует системный Node.js, установленный разработчиком.
if command -v node >/dev/null 2>&1; then
  NODE_DIR="$(dirname "$(command -v node)")"
elif [ -x "$BUNDLED_NODE_DIR/node" ]; then
  NODE_DIR="$BUNDLED_NODE_DIR"
else
  echo "Ошибка: Node.js не найден. Установите Node.js 20+ с https://nodejs.org/"
  read -r -p "Нажмите Enter, чтобы закрыть окно..."
  exit 1
fi

export PATH="$NODE_DIR:$BUNDLED_TOOLS_DIR:$PATH"

if command -v pnpm >/dev/null 2>&1; then
  PACKAGE_RUNNER="pnpm"
elif command -v corepack >/dev/null 2>&1; then
  corepack enable
  PACKAGE_RUNNER="pnpm"
else
  echo "Ошибка: pnpm не найден. Выполните: npm install -g pnpm"
  read -r -p "Нажмите Enter, чтобы закрыть окно..."
  exit 1
fi

if [ ! -d "node_modules" ]; then
  echo "Устанавливаю frontend-зависимости..."
  "$PACKAGE_RUNNER" install
fi

echo "Запускаю Buxme AI-Scout на http://127.0.0.1:5173"
(sleep 1 && open "http://127.0.0.1:5173") &
"$PACKAGE_RUNNER" dev --host 127.0.0.1
