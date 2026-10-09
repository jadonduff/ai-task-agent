@echo off

llama-server.exe ^
  -m "%LLAMA_MODEL_PATH%" ^
  --host 0.0.0.0 ^
  --port 6573 ^
  --webui-mcp-proxy \
  -c 100000 ^
  -ctk f16 ^
  -ctv f16 ^
  --load-mode mmap+mlock ^
  --temp 1.0 ^
  --top-p 0.95 ^
  --top-k 20 ^
  --min-p 0 ^
  --repeat-penalty 1.0 ^
  --presence-penalty 0 ^
  --reasoning on ^
  --reasoning-effort low ^
