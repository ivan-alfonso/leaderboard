# AWS Deployment Handover Notes

Operational notes for deploying the LëtzEval BAF agent on AWS.
This document covers architecture decisions and pre-flight checklist only — it does **not** contain deployment scripts or infrastructure-as-code.

---

## Architecture overview

```
Browser ──wss──▶ ALB (SSL termination) ──ws──▶ BAF agent container
                                                      │
                                              reads AI_Sandbox.db
                                              (mounted read-only volume)
                                                      │
                                         (optional) LLM backend ──▶ OpenAI API
                                                                └──▶ Ollama container (same VPC)
```

The BAF agent is a long-running Python process that exposes a WebSocket endpoint on port 8765 (configurable in `config.yaml`). The Application Load Balancer terminates TLS and forwards plain `ws://` connections to the container.

---

## Container image

The agent Dockerfile lives at `agent/Dockerfile`. Build it with:

```bash
docker build -t letzeval-agent:latest ./agent
```

The image does **not** bundle the SQLite database. Mount `AI_Sandbox.db` from a persistent volume or EFS at the path configured in `config.yaml` → `db_path`.

**Do not run `Base.metadata.create_all` or any migration against the authoritative database.** The database is read-only from the agent's perspective; the `safe_db` module opens it with `check_same_thread=False` and never writes.

---

## Environment variables

See `agent/.env.example` for the full list. On AWS, set these via ECS task definition environment variables or AWS Secrets Manager (for `OPENAI_API_KEY`):

| Variable | Required | Notes |
|---|---|---|
| `LETZEVAL_LLM_PROVIDER` | No | `none` disables the LLM fallback entirely |
| `LETZEVAL_LLM_MODEL` | Conditional | Required when provider ≠ none |
| `OPENAI_API_KEY` | When `provider=openai` | Store in Secrets Manager, not plaintext env |
| `LETZEVAL_OLLAMA_BASE_URL` | When `provider=ollama` | Use the ECS service name, not `localhost` |
| `LETZEVAL_LLM_TIMEOUT_SECONDS` | No | Default 12; increase for slow Ollama instances |

---

## Networking

### WebSocket keep-alives

AWS ALB has an idle timeout (default 60 s). BAF sends periodic pings; verify the ALB idle timeout matches or exceeds the BAF heartbeat interval. If sessions drop after 60 s of user inactivity, increase the ALB timeout.

### Ollama on the same task / VPC

If running Ollama as a sidecar or a separate ECS service:

- Set `LETZEVAL_OLLAMA_BASE_URL=http://<service-name>:11434` — use the ECS service discovery DNS name, **not** `localhost`.
- `localhost` inside a container refers to the container's own loopback interface; it cannot reach a sibling container or host.

### Security groups

- ALB inbound: 443 (HTTPS/WSS from internet)
- Agent container: 8765 from ALB security group only (not from internet)
- Ollama container (if used): 11434 from agent container security group only

---

## TLS / WSS

- **Production must use `wss://`** (WebSocket Secure). Never expose `ws://` on a public endpoint.
- TLS is terminated at the ALB. The BAF agent itself does not need a certificate.
- Set `VITE_AGENT_URL=wss://your-domain.example.com/ws` in the frontend build environment.
- The frontend checks `import.meta.env.VITE_AGENT_URL`; an absent or `ws://localhost` value is fine for local development but must never appear in a production build artifact.

### Trusted origins

Configure `allowed_origins` in `config.yaml` (BAF WebSocket platform setting) to the production domain. Do not use `*` in production.

---

## Database

- Mount `AI_Sandbox.db` as a **read-only** volume (EFS with read-only access policy, or a pre-baked volume).
- The `safe_db` module uses a connection pool opened at startup. If the DB file path changes, update `config.yaml → db_path` and redeploy.
- No schema migrations are run by the agent. Any schema changes require a separate migration process applied outside the agent container before deploying.

---

## LLM security reminders

- The LLM router (`agent/llm/router.py`) never executes SQL. Its output is parsed JSON used only for intent/entity extraction; the deterministic `safe_db` layer executes all queries.
- Generated SQL is never exposed to users. The `safe_db` module uses parameterized queries only.
- Raw database errors, schema details, and model comments are never returned to the client.
- `OPENAI_API_KEY` must not appear in container image layers, environment variable plaintext in the task definition, or application logs. Use AWS Secrets Manager and inject via `secrets` in the task definition.

---

## Health check

The BAF agent does not expose an HTTP health endpoint by default. Options:

1. **TCP health check** on port 8765 (ALB target group): simplest, checks the process is listening.
2. **Custom HTTP endpoint**: add a minimal HTTP server alongside BAF that returns 200 OK (separate thread or sidecar).

---

## Scaling

The BAF agent is stateful per session (in-memory session store). Horizontal scaling requires sticky sessions on the ALB (load balancer cookie stickiness), or migrating to a shared session store (not currently implemented). For the current scale (single-team evaluation leaderboard), a single task with restart-on-failure is sufficient.
