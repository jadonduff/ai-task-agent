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
from fastapi import FastAPI
from fastapi.responses import FileResponse

# ---- Main ------------------------------------------------------------
app = FastAPI()


@app.get("/")
def index():
    return FileResponse("src/frontend/index.html")
