#!/usr/bin/env python3
# python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 6573
# ----------------------------------------------------------------------
# Title    : AI Task Agent Main
# Owner    : Jadon Duff
# Authors  : Jadon Duff, ChatGPT, Claude
# Date     : 2026-09-28
# Version  : v0.0.1
# Project  : AI Task Agent
# Software : Python 3.14.3
# ----------------------------------------------------------------------
# Description:
#   Entry point to the AI Task Agent application.
#
# References:
#   None.
# ----------------------------------------------------------------------

# ---- Libraries -------------------------------------------------------
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, PlainTextResponse
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    OpenAIChatCompletionsModel,
    function_tool,
    set_tracing_disabled,
)

# ---- Agent -----------------------------------------------------------
set_tracing_disabled(True)

client = AsyncOpenAI(base_url="http://localhost:8080/v1", api_key="none")


@function_tool
def history_fun_fact() -> str:
    """Return a short history fact."""
    return "Sharks are older than trees."


agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant. Use history_fun_fact when it helps.",
    model=OpenAIChatCompletionsModel(model="local", openai_client=client),
    tools=[history_fun_fact],
)

# ---- Main ------------------------------------------------------------
app = FastAPI()


@app.get("/")
def index():
    return FileResponse("src/frontend/index.html")


@app.post("/submit")
async def submit(value: str = Form(...)):
    result = await Runner.run(agent, value)
    return PlainTextResponse(result.final_output)
