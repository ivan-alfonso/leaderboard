"""
Thin HTTP bridge for the LëtzEval BAF agent.

Exposes:
    POST /chat   {"message": "...", "session_id": "...", "language": "en"}
    GET  /health

Internally opens a WebSocket connection to the BAF agent for each request,
sends the message, collects all replies until the agent goes quiet, and
returns them as JSON.  No BAF internals are touched.

Start with: start_http_bridge(host="0.0.0.0", port=8766)

─── Production guardrails (env vars) ───────────────────────────────────────
  GUARDRAIL_RATE_LIMIT      Max requests per IP per minute    (default 6,  0 = off)
  GUARDRAIL_BURST           Extra burst above the rate limit  (default 2)
  GUARDRAIL_MAX_CONCURRENT  Max parallel requests per IP      (default 2,  0 = off)
  GUARDRAIL_MAX_MSG_LEN     Max message length in characters  (default 1000, 0 = off)
  GUARDRAIL_CORS_ORIGINS    Comma-separated allowed origins   (default *, e.g. https://letz.uni.lu)
"""
import asyncio
import collections
import json
import logging
import os
import threading
import time
from typing import Optional

import uvicorn
import websockets
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

_BAF_WS_URL       = "ws://localhost:8765"
_GREETING_DRAIN_S = 1.5   # seconds to drain automatic greeting messages
_QUIET_TIMEOUT_S  = 5.0   # seconds of silence after last reply → done
_HARD_TIMEOUT_S   = 60.0  # absolute per-request ceiling

# ---------------------------------------------------------------------------
# Guardrail configuration — read once at import time
# ---------------------------------------------------------------------------
_RATE_LIMIT:     int = int(os.environ.get("GUARDRAIL_RATE_LIMIT",     "6"))    # req/min per IP
_BURST:          int = int(os.environ.get("GUARDRAIL_BURST",          "2"))    # burst above limit
_MAX_CONCURRENT: int = int(os.environ.get("GUARDRAIL_MAX_CONCURRENT", "2"))    # parallel req per IP
_MAX_MSG_LEN:    int = int(os.environ.get("GUARDRAIL_MAX_MSG_LEN",    "1000")) # chars per message
_CORS_ORIGINS: list[str] = [
    o.strip()
    for o in os.environ.get("GUARDRAIL_CORS_ORIGINS", "*").split(",")
    if o.strip()
] or ["*"]

logging.info(
    "Guardrails: rate=%d/min burst=%d concurrent=%d msg_len=%d cors=%s",
    _RATE_LIMIT, _BURST, _MAX_CONCURRENT, _MAX_MSG_LEN, _CORS_ORIGINS,
)

# ---------------------------------------------------------------------------
# Rate limiter — sliding window per remote IP (thread-safe, in-memory)
# ---------------------------------------------------------------------------
# _rate_windows[ip] → deque of monotonic timestamps within the last 60 s
_rate_windows: dict[str, collections.deque] = collections.defaultdict(collections.deque)
_rate_lock = threading.Lock()


def _check_rate_limit(ip: str) -> bool:
    """Return True (allowed) or False (rate-limited). Records the request timestamp."""
    if _RATE_LIMIT <= 0:
        return True
    now = time.monotonic()
    cutoff = now - 60.0
    with _rate_lock:
        dq = _rate_windows[ip]
        while dq and dq[0] < cutoff:   # evict expired timestamps
            dq.popleft()
        if len(dq) >= _RATE_LIMIT + _BURST:
            return False
        dq.append(now)
    return True


# ---------------------------------------------------------------------------
# Concurrency limiter — max in-flight requests per IP (thread-safe, in-memory)
# ---------------------------------------------------------------------------
_in_flight: dict[str, int] = collections.defaultdict(int)
_concurrency_lock = threading.Lock()


class _ConcurrencySlot:
    """Sync context manager: acquire a per-IP slot or raise 429."""

    def __init__(self, ip: str):
        self._ip = ip
        self._acquired = False

    def __enter__(self):
        if _MAX_CONCURRENT <= 0:
            self._acquired = True
            return self
        with _concurrency_lock:
            if _in_flight[self._ip] >= _MAX_CONCURRENT:
                logging.warning("Guardrail: concurrency limit hit for %s", self._ip)
                raise HTTPException(
                    status_code=429,
                    detail="Too many concurrent requests from this client. Please wait for a reply before sending another.",
                )
            _in_flight[self._ip] += 1
            self._acquired = True
        return self

    def __exit__(self, *_):
        if self._acquired and _MAX_CONCURRENT > 0:
            with _concurrency_lock:
                _in_flight[self._ip] = max(0, _in_flight[self._ip] - 1)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="LëtzEval Agent HTTP Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


def _client_ip(request: Request) -> str:
    """Real client IP, honoring X-Forwarded-For from a trusted reverse proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


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
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    ip = _client_ip(request)

    # ── Guardrail: message length ──────────────────────────────────────────
    if _MAX_MSG_LEN > 0 and len(req.message) > _MAX_MSG_LEN:
        logging.warning("Guardrail: message too long (%d chars) from %s", len(req.message), ip)
        raise HTTPException(
            status_code=400,
            detail=f"Message exceeds the {_MAX_MSG_LEN}-character limit.",
        )

    # ── Guardrail: rate limit ──────────────────────────────────────────────
    if not _check_rate_limit(ip):
        logging.warning("Guardrail: rate limit hit for %s", ip)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({_RATE_LIMIT} requests/min). Please wait before sending again.",
            headers={"Retry-After": "60"},
        )

    # ── Guardrail: concurrency ─────────────────────────────────────────────
    with _ConcurrencySlot(ip):
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
