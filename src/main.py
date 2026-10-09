#!/usr/bin/env python3
# python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 6573
# ----------------------------------------------------------------------
# Title    : AI Task Agent Main
# Owner    : Jadon Duff
# Authors  : Jadon Duff, ChatGPT, Claude
# Date     : 2026-09-28
# Version  : v0.0.2
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
from contextlib import asynccontextmanager

from agents import Agent, Runner, OpenAIChatCompletionsModel, set_tracing_disabled
from fastapi.responses import FileResponse, PlainTextResponse
from agents.mcp import MCPServerStreamableHttp
from pydantic import BaseModel
from openai import AsyncOpenAI
from fastapi import FastAPI
from pathlib import Path

# ---- Setup -----------------------------------------------------------
MODEL = "unsloth/Qwen3.5-0.8B-GGUF:Q4_K_XL"

set_tracing_disabled(True)

with open(Path('.') / 'src' / 'utilities' / 'system_prompt.md') as file:
    SYSTEM_PROMPT = file.read()

client = AsyncOpenAI(base_url="http://host.docker.internal:6575/v1", api_key="none")

mcp_server = MCPServerStreamableHttp(
    name="local-mcp",
    params={"url": "http://mcp-server:6574/mcp"},
    cache_tools_list=True,
)

agent = Agent(
    name="Assistant",
    instructions=SYSTEM_PROMPT,
    model=OpenAIChatCompletionsModel(model=MODEL, openai_client=client),
    mcp_servers=[mcp_server],
)


# ---- Main ------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await mcp_server.connect()
    yield
    await mcp_server.cleanup()


app = FastAPI(lifespan=lifespan)


class PromptRequest(BaseModel):
    prompt: str


@app.get("/")
def index():
    return FileResponse("src/frontend/index.html")


@app.post("/prompt")
async def stream(req: PromptRequest):
    result = await Runner.run(agent, input=req.prompt)
    return PlainTextResponse(result.final_output)
