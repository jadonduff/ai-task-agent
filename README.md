# AI Task Agent

### Developed by Jadon Duff, Jacob Ewasko, Ioannis Limniatis, & Jacob Lebkuecher

> This file contains the instructions for setting up and running the **AI Task Agent**.

---

## Helpful Commands

For **MacOS Users**:
- To **build** the application, run `make build`
- To **start** the application, run `make run-mac`
- To **stop** the application, run `make stop-mac`

For **Windows**:
- To **build** the application, run `make build`
- To **start** the application, run `make run-windows`
- To **stop** the application, run `make stop-windows`

---

## Setup

While in the **development phase**, this application requires an environment file.

This file should be placed in the **root** of the source code and be named `.env`. It is **untracked** by **Git**, so each developer/tester will need their own.

Example `.env`:
```
LLAMA_MODEL_PATH=/Users/AI/.cache/huggingface/hub/Qwen3.8-27B-UD-Q8_K_XL.gguf
```

**Note**: Currently, `llama.cpp` does not automatically install. You will need to manually install `llama.cpp` which comes with `llama-server`.

---

## Routes & Architecture

The **frontend** is located in `src/frontend`. It is hosted by a Python-based FastAPI application, `main.py`, located in `src`. It lives in a Docker container called `ai-task-agent` that is spawned from the `make` commands on port `6573`.

The **backend** is located in `src/backend`. It is hosted by a Python-based FastMCP application, `mcp_server.py`. It lives in a Docker container called `mcp-server` that is spawned from the `make` commands on port `6574`, using an `http` transport.

The **Large Language Model (LLM)** is ran by the host computer using `llama-server`, which is a part of `llama.cpp`. This is the industry-standard way of hosting **LLMs** locally, and is not located in a Docker container as it needs native **GPU** acceleration. It lives on port `6575`.

**Ports Reference Guide**:
- `6573` - Python Server & Web Application
- `6574` - MCP Server
- `6575` - LLM Server

---

## Documentation

The `/docs` subdirectory contains the files rendered via GitHub pages for the Senior Design project website.

The `/ref` subdirectory contains documentation files relevant to the codebase.

---

## Quick Links

[Web Application](http://127.0.0.1:6573)

---
*Updated Oct 6, 2026 by Jadon Duff*
