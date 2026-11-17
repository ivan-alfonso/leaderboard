"""Runs INSIDE the container (agent venv): checks nginx, the API and the agent WebSocket."""
import asyncio, json, sys, urllib.request

BASE = "http://127.0.0.1:3000"


def get(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=20) as r:
            return r.status, r.read()
    except Exception as e:
        return -1, repr(e).encode()


code, body = get("/")
print("GET / ->", code, "title ok" if b"<title>" in body else body[:120])
code, body = get("/api/model/leaderboard")
try:
    rows = json.loads(body)
    print("GET /api/model/leaderboard ->", code, "rows:", len(rows))
except Exception:
    print("GET /api/model/leaderboard ->", code, body[:200])


async def ask(q):
    import websockets
    out = []
    async with websockets.connect("ws://127.0.0.1:3000/ws") as ws:
        await ws.send(json.dumps({"action": "user_set_variable", "message": {"ui_language": "en"}}))
        try:
            while True:
                await asyncio.wait_for(ws.recv(), timeout=2)
        except asyncio.TimeoutError:
            pass
        await ws.send(json.dumps({"action": "user_message", "message": q}))
        try:
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=8 if not out else 3)
                p = json.loads(raw)
                m = p.get("message", "")
                if isinstance(m, str) and m:
                    out.append(f'[{p.get("action")}] {m[:300]}')
        except asyncio.TimeoutError:
            pass
    return out

for q in sys.argv[1:] or ["What is ChatGPT 4o's Macro Average?"]:
    try:
        replies = asyncio.run(ask(q))
        print("WS Q:", q)
        for r in replies or ["<no reply>"]:
            print("   ", r.replace("\n", " | "))
    except Exception as e:
        print("WS FAILED:", repr(e))
