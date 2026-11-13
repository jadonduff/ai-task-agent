#!/bin/bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  . "$ROOT_DIR/.env"
  set +a
fi

# default local mode
BIND="127.0.0.1"
EXTRA=(--webui-mcp-proxy)

# special tethering mode
if [ "$1" = "lan" ]; then
  if [ -z "$LLAMA_API_KEY" ]; then
    echo "LAN mode needs LLAMA_API_KEY set." >&2
    exit 1
  fi
  BIND="0.0.0.0"
  EXTRA=(--api-key "$LLAMA_API_KEY")
fi

llama-server \
  -m "$LLAMA_MODEL_PATH" \
  --host "$BIND" \
  --port 6573 \
  "${EXTRA[@]}" \
  -c 100000 \
  -ctk f16 \
  -ctv f16 \
  --load-mode mmap+mlock \
  --temp 1.0 \
  --top-p 0.95 \
  --top-k 20 \
  --min-p 0 \
  --repeat-penalty 1.0 \
  --presence-penalty 0 \
  --reasoning on \
  --reasoning-effort low \
  --spec-type draft-mtp,ngram-mod \
  --spec-ngram-mod-n-min 1 \
  --spec-ngram-mod-n-max 8 \
  --spec-ngram-mod-n-match 24
