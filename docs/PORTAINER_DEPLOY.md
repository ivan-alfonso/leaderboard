# Deploying on Portainer

How the public leaderboard at <https://leaderboard-letz.besser-pearl.org> is deployed:
one container on a Portainer-managed Docker node, published through a Cloudflare Tunnel.
The files are in [`deploy/`](../deploy).

## Architecture

```
Browser ──► Cloudflare edge ──► tunnel (cloudflared container, host network)
                                   │
                                   ▼
                     node 127.0.0.1:3001 ──► leaderboard container, nginx :3000
                                              ├─ /       static frontend build
                                              ├─ /api/   FastAPI (uvicorn :8080)
                                              └─ /ws     BAF agent WebSocket (:8765)
```

Everything runs in one image (`deploy/Dockerfile`), so the node publishes a single port
and the tunnel needs a single route. Inside the image the API and the agent each have
their own virtualenv, because BAF pins versions of packages the API also uses.

The node's firewall blocks published ports, so the tunnel is the only way in. The agent's
HTTP bridge (port 8766) is not routed and stays private to the container.

## What you need

- A Portainer API key that can create containers and build images on the node.
- Python 3 and git on your machine. No local Docker: the image is built on the node.

```bash
export PORTAINER_URL=https://<portainer-host>:9443
export PORTAINER_NODE=<node-name>
export PORTAINER_TOKEN=<api-key>        # or put it in ~/.portainer_token
export PORTAINER_INSECURE=1             # only if Portainer has an internal certificate
```

## Deploy a new version

Run from the repo root, on the commit you want to publish. The build uses `git archive HEAD`,
so uncommitted changes are not included.

```bash
python deploy/portainer.py build besser/leaderboard:v4
python deploy/portainer.py deploy besser/leaderboard:v4
```

`build` sends the repo to the node and builds `deploy/Dockerfile` there (about 10 minutes
the first time, 1 to 2 minutes afterwards thanks to the layer cache).

`deploy` stops the running `leaderboard` container, keeps it as `leaderboard-prev`, and starts
a new one from the tag on `127.0.0.1:3001`. The LLM settings of the old container
(`OPENAI_API_KEY`, `LETZEVAL_*`, `GUARDRAIL_*`) are carried over.

The site and the API are back within seconds. **The agent trains its intent classifier at
start and needs about 3 minutes** before the chat connects; until then `/ws` returns 502 and
the chat widget shows as disconnected.

Check the result:

```bash
python deploy/portainer.py probe      # site, API and one chat question, from inside the container
python deploy/portainer.py logs
curl -o /dev/null -w "%{http_code}\n" https://leaderboard-letz.besser-pearl.org/api/model/leaderboard
```

## LLM key and agent mode

The image contains no key and starts the agent without an LLM (`LETZEVAL_LLM_PROVIDER=none`,
`LETZEVAL_AGENT_MODE=classical`). To switch the LLM on, or to change the key, deploy the same
tag again with an env file. No rebuild is needed.

```bash
cat > llm.env <<'EOF'
OPENAI_API_KEY=sk-...
LETZEVAL_LLM_PROVIDER=openai
LETZEVAL_AGENT_MODE=llm
LETZEVAL_LLM_MODEL=gpt-5.1
EOF
python deploy/portainer.py deploy besser/leaderboard:v4 --env-file llm.env
rm llm.env
```

`.env` files are git-ignored; do not commit a key.

## Roll back

```bash
# stop the new container, bring the previous one back
curl -sk -X POST   -H "X-API-Key: $PORTAINER_TOKEN" -H "X-PortainerAgent-Target: $PORTAINER_NODE" "$PORTAINER_URL/api/endpoints/2/docker/containers/leaderboard/stop"
curl -sk -X DELETE -H "X-API-Key: $PORTAINER_TOKEN" -H "X-PortainerAgent-Target: $PORTAINER_NODE" "$PORTAINER_URL/api/endpoints/2/docker/containers/leaderboard"
curl -sk -X POST   -H "X-API-Key: $PORTAINER_TOKEN" -H "X-PortainerAgent-Target: $PORTAINER_NODE" "$PORTAINER_URL/api/endpoints/2/docker/containers/leaderboard-prev/rename?name=leaderboard"
curl -sk -X POST   -H "X-API-Key: $PORTAINER_TOKEN" -H "X-PortainerAgent-Target: $PORTAINER_NODE" "$PORTAINER_URL/api/endpoints/2/docker/containers/leaderboard/start"
```

## Things to know

- **The database is inside the image.** `backend/data/AI_Sandbox.db` is copied at build time;
  publishing new results means a new build. Nothing written at runtime survives a deploy.
- **The chat's public address is fixed at build time.** The frontend is built with
  `VITE_AGENT_URL=wss://leaderboard-letz.besser-pearl.org/ws`. For another hostname:
  `python deploy/portainer.py build <tag> --build-arg VITE_AGENT_URL=wss://<host>/ws`.
- **LLM calls from the chat are not rate limited.** The `GUARDRAIL_*` limits apply to the HTTP
  bridge only. The chat widget talks to the agent's WebSocket directly, so every chat message
  can trigger an LLM call. Set a spending cap on the key.
- **Thread limits.** The image sets `OMP_NUM_THREADS=1` (and the OpenBLAS/MKL equivalents).
  On a node with many cores, PyTorch oversubscribes threads without them.
- **Debug telemetry is off.** Do not set `LETZEVAL_DEBUG_TELEMETRY=1` on the public site: it
  writes every user message to a file in the container.

## First-time setup of the tunnel

This is done once per hostname and does not change on later deploys. In the Cloudflare
dashboard (Zero Trust → Networks → Tunnels):

1. Create a tunnel and copy its connector token.
2. Add a public hostname that routes to `http://localhost:3001`.
3. Start the connector on the node, on the host network, through the Portainer API:

```bash
curl -sk -X POST -H "X-API-Key: $PORTAINER_TOKEN" -H "X-PortainerAgent-Target: $PORTAINER_NODE" \
  -H "Content-Type: application/json" \
  "$PORTAINER_URL/api/endpoints/2/docker/containers/create?name=leaderboard-tunnel" \
  -d '{"Image": "cloudflare/cloudflared:latest",
       "Cmd": ["tunnel", "--no-autoupdate", "run", "--token", "<connector-token>"],
       "HostConfig": {"NetworkMode": "host", "RestartPolicy": {"Name": "always"}}}'
curl -sk -X POST -H "X-API-Key: $PORTAINER_TOKEN" -H "X-PortainerAgent-Target: $PORTAINER_NODE" \
  "$PORTAINER_URL/api/endpoints/2/docker/containers/leaderboard-tunnel/start"
```

Cloudflare Tunnels pass WebSockets through, so `/ws` needs no extra setting.
