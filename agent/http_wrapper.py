"""
Thin HTTP bridge for the LëtzEval BAF agent.

Exposes:
    POST /chat   {"message": "...", "session_id": "...", "language": "en"}
    GET  /health

Internally opens a WebSocket connection to the BAF agent for each request,
sends the message, collects all replies until the agent goes quiet, and
returns them as JSON.  No BAF internals are touched.

Start with: start_http_bridge(host="0.0.0.0", port=8766)
"""
import asyncio
import json
import threading
import time
from typing import Optional

import uvicorn
import websockets
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

_BAF_WS_URL = "ws://localhost:8765"
_GREETING_DRAIN_S = 1.5   # seconds to drain automatic greeting messages
_QUIET_TIMEOUT_S  = 5.0   # seconds of silence after last reply → done
_HARD_TIMEOUT_S   = 60.0  # absolute per-request ceiling

app = FastAPI(title="LëtzEval Agent HTTP Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "http_client"
    language: Optional[str] = "en"


class ChatResponse(BaseModel):
    replies: list[str]
    response: str       # AgentSeal (and any single-field consumer) reads this field
    elapsed_s: float


async def _query_agent(message: str, language: str) -> list[str]:
    collected: list[str] = []
    start = time.monotonic()

    async with websockets.connect(_BAF_WS_URL) as ws:
        # Set UI language
        await ws.send(json.dumps({
            "action": "user_set_variable",
            "message": {"ui_language": language},
        }))

        # Drain the automatic greeting
        drain_until = time.monotonic() + _GREETING_DRAIN_S
        while time.monotonic() < drain_until:
            try:
                await asyncio.wait_for(ws.recv(), timeout=drain_until - time.monotonic())
            except (asyncio.TimeoutError, Exception):
                break

        # Send the user's message
        await ws.send(json.dumps({"action": "user_message", "message": message}))

        # Collect replies until quiet or hard timeout
        hard_until = start + _HARD_TIMEOUT_S
        while time.monotonic() < hard_until:
            remaining = hard_until - time.monotonic()
            try:
                raw = await asyncio.wait_for(
                    ws.recv(), timeout=min(remaining, _QUIET_TIMEOUT_S)
                )
                payload = json.loads(raw)
                action = payload.get("action", "")
                msg    = payload.get("message", "")

                if action == "agent_reply_options":
                    try:
                        opts = list(json.loads(msg).values())
                        collected.append("[OPTIONS: " + ", ".join(opts) + "]")
                    except Exception:
                        pass
                elif action in ("agent_reply_str", "agent_reply_markdown", ""):
                    if isinstance(msg, str) and msg and not msg.startswith("__UI_ACTION__"):
                        collected.append(msg)
            except asyncio.TimeoutError:
                if collected:
                    break  # agent went quiet — done

    return collected


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    start = time.monotonic()
    replies = await _query_agent(req.message, req.language or "en")
    return ChatResponse(
        replies=replies,
        response="\n".join(replies),
        elapsed_s=round(time.monotonic() - start, 2),
    )


@app.get("/health")
def health():
    return {"status": "ok"}


def start_http_bridge(host: str = "0.0.0.0", port: int = 8766) -> threading.Thread:
    """Start the HTTP bridge in a background daemon thread."""
    def _run() -> None:
        uvicorn.run(app, host=host, port=port, log_level="warning")

    thread = threading.Thread(target=_run, daemon=True, name="http-bridge")
    thread.start()
    return thread
