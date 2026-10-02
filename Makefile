# Makefile
# ----------------------------------------------------------------------
# Title    : AI Task Agent Makefile
# Owner    : Jadon Duff
# Authors  : Jadon Duff, ChatGPT
# Date     : 2026-10-02
# Version  : v0.0.1
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

run:
	docker compose up

stop:
	docker compose down
