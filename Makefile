# Makefile
# ----------------------------------------------------------------------
# Title    : AI Task Agent Makefile
# Owner    : Jadon Duff
# Authors  : Jadon Duff, ChatGPT
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

.PHONY: build run stop clean rebuild

build:
	docker compose build

run-mac:
	./scripts/run-llm-mac.sh & docker compose up

# make windows will run the application for Windows
# TODO: create Windows llama-cli script
run-windows:
	docker compose up

stop-mac:
	./scripts/stop-llm-mac.sh & docker compose down

# TODO: make Windows stop script
stop-windows:
	docker compose down
