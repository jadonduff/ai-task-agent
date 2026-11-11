@echo off
setlocal EnableDelayedExpansion

rem Load .env file if it exists
if exist .env (
  for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    rem Only set variables that have a value
    if not "%%b"=="" set "%%a=%%b"
  )
)

rem default local mode
set "BIND=127.0.0.1"
set "PROXYARG=--webui-mcp-proxy"
set "KEYARG="

rem tethering mode
if /i "%~1"=="lan" (
  if not defined LLAMA_API_KEY (
    echo LAN mode needs LLAMA_API_KEY set.
    exit /b 1
  )
  set "BIND=0.0.0.0"
  set "PROXYARG="
  set "KEYARG=--api-key %LLAMA_API_KEY%"
)


llama-server.exe ^
  -m "%LLAMA_MODEL_PATH%" ^
  --host %BIND% ^
  --port 6573 ^
  %PROXYARG% ^
  %KEYARG% ^
  -c 20000 ^
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
