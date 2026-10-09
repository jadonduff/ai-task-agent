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

.PHONY: build runm runw stopm stopw

build:
	docker compose build

runm:
	./scripts/run-llm-mac.sh & docker compose up

stopm:
	./scripts/stop-llm-mac.sh & docker compose down

runw:
	start /B cmd /c "scripts\run-llm-windows.bat" & docker compose up

stopw:
	cmd /c "scripts\stop-llm-windows.bat" & docker compose down
