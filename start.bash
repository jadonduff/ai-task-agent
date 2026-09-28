#!/usr/bin/env bash
set -e

MODEL="put_your_model_path_here"
LLAMA_PORT=8080
APP_PORT=6573
URL="http://localhost:$APP_PORT"

# source .venv/bin/activate   # uncomment if you use a virtual environment

trap 'kill $LLAMA_PID $APP_PID 2>/dev/null || true' EXIT

# 1. llama-server
llama-server -m "$MODEL" -ngl 99 -c 4096 --jinja --port $LLAMA_PORT &
LLAMA_PID=$!

echo "Waiting for llama-server..."
until curl -sf "http://localhost:$LLAMA_PORT/health" >/dev/null; do
  kill -0 $LLAMA_PID 2>/dev/null || { echo "llama-server exited"; exit 1; }
  sleep 1
done

# 2. FastAPI app
python3.14 -m uvicorn src.main:app --reload --host 127.0.0.1 --port $APP_PORT &
APP_PID=$!

until curl -sf "$URL" >/dev/null; do sleep 0.5; done

# 3. Open the browser
if command -v xdg-open >/dev/null; then xdg-open "$URL"
elif command -v open >/dev/null; then open "$URL"
else start "$URL"
fi

wait