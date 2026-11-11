# Makefile
# ----------------------------------------------------------------------
# Title    : AI Task Agent Makefile
# Owner    : Jadon Duff
# Authors  : Jadon Duff, Jacob Ewasko, ChatGPT
# Date     : 2026-10-02
# Version  : v0.0.2
# Project  : AI Task Agent
# Software : GNU Make 3.81
# ----------------------------------------------------------------------
# Description:
#   Makefile providing building, running, and stopping application.
#
# References:
#   None.
# ----------------------------------------------------------------------

.PHONY: build index reindex env-win env-mac runm runw stopm stopw runm-mcp runw-mcp runm-llm runw-llm stopm-mcp stopw-mcp stopm-llm stopw-llm

build:
	docker compose build
	$(MAKE) index

index:
	mkdir -p ragdata
	docker compose run --rm --no-deps ai-task-agent python -m src.rag.ingest

reindex:
	rm -rf ragdata
	$(MAKE) index

env-win:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts\gen-env.ps1

env-mac:
	./scripts/gen-env.sh

runm: env-mac
	./scripts/run-llm-mac.sh & docker compose up

stopm:
	./scripts/stop-llm-mac.sh & docker compose down

# runw:
# 	cmd /c "scripts\run-llm-windows.bat" & docker compose up
runw: env-win
	start "llama-server" cmd /c "scripts\run-llm-windows.bat" & docker compose up

stopw:
	cmd /c "scripts\stop-llm-windows.bat" & docker compose down

# special tethering modes
runm-mcp: env-mac
	docker compose up -d --wait
	docker compose logs -f

runw-mcp: env-win
	docker compose up -d --wait
	docker compose logs -f

runm-llm:
	./scripts/run-llm-mac.sh lan

runw-llm:
	cmd /c start "" /B "scripts\run-llm-windows.bat" lan

stopm-mcp:
	docker compose down

stopw-mcp:
	docker compose down

stopm-llm:
	./scripts/stop-llm-mac.sh

stopw-llm:
	cmd /c "scripts\stop-llm-windows.bat"



