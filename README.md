# AI Task Agent

### Developed by Jadon Duff, Jacob Ewasko, Ioannis Limniatis, & Jacob Lebkuecher

> This file contains the instructions for setting up and running the **AI Task Agent**.

---

## Helpful Commands

For **MacOS Users**:
- To **build** the application, run `make build`
- To **start** the application, run `make runm`
- To **stop** the application, run `make stopm`

For **Windows**:
- To **build** the application, run `make build`
- To **start** the application, run `make runw`
- To **stop** the application, run `make stopw`

---

## Setup

**Note**: Currently, `llama.cpp` does not automatically install. You will need to manually install `llama.cpp` which comes with `llama-server`.

## Authentication Setup - Normal Use Mode

1. Start AI Task Agent
2. Go to .env
3. Copy the value assigned to LLAMA_API_KEY
4. Paste that in the Llama UI authentication popup on the Web Application.
5. Go back to .env
6. Copy the value assigned to MCP_TOKEN
7. Go back to the Web Application
8. Go to the MCP tab
    - Edit
        - Turn on Authorization
            - write: 
            Bearer (then the mcp token you copied earlier)

---

## Routes & Architecture

The **frontend** is hosted by `llama.cpp` on port `6573`.

The **backend** is located in `src/backend`. It is hosted by a Python-based FastMCP application, `mcp_server.py`. It lives in a Docker container called `mcp-server` that is spawned from the `make` commands on port `6574`, using an `http` transport.

The **Large Language Model (LLM)** is ran by the host computer using `llama-server`, which is a part of `llama.cpp`. This is the industry-standard way of hosting **LLMs** locally, and is not located in a Docker container as it needs native **GPU** acceleration. It lives on port `6573`.

The **Docker Screen** is ran by the MCP server container. You can access it on the link below, and it is hosted on port `6574`.

**Ports Reference Guide**:
- `6573` - LLM Server
- `6574` - MCP Server
- `6575` - Agent's Computer

---

## Documentation

The `/docs` subdirectory contains the files rendered via GitHub pages for the Senior Design project website.

The `/ref` subdirectory contains documentation files relevant to the codebase.

The `/knowledge` subdirectory contains the user-provided RAG documentation.

---

## Quick Links

[Web Application](http://127.0.0.1:6573)

[MCP Server](http://127.0.0.1:6574/mcp/)

[Agent's Computer](http://localhost:6575/vnc.html?autoconnect=true&resize=scale)

---
*Updated Nov 8, 2026 by Jadon Duff*
