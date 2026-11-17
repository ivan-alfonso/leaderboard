FROM python:3.12-slim

WORKDIR /app

# Install torch CPU-only first (lighter than the GPU default, ~800 MB)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
# Remove torch from requirements so it isn't reinstalled (already installed above)
RUN grep -v "^torch" requirements.txt > requirements_notorch.txt \
    && pip install --no-cache-dir -r requirements_notorch.txt \
    && rm requirements_notorch.txt

COPY . .

EXPOSE 8765
EXPOSE 8766

# ── Runtime environment variables ────────────────────────────────────────────
# Agent
#   LETZEVAL_DB_PATH          Path to the SQLite database (required)
#   LETZEVAL_AGENT_MODE       classical | llm  (default: llm)
#   LETZEVAL_LLM_MODEL        OpenAI model ID  (default: gpt-5.1)
#   LETZEVAL_DEBUG_TELEMETRY  1 to enable JSONL telemetry output
#
# HTTP bridge guardrails (port 8766)
#   GUARDRAIL_RATE_LIMIT      Max requests per IP per minute  (default 6,  0 = off)
#   GUARDRAIL_BURST           Extra burst allowance           (default 2)
#   GUARDRAIL_MAX_CONCURRENT  Max parallel requests per IP    (default 2,  0 = off)
#   GUARDRAIL_MAX_MSG_LEN     Max message length in chars     (default 1000, 0 = off)
#   GUARDRAIL_CORS_ORIGINS    Comma-separated allowed origins (default *)
# ─────────────────────────────────────────────────────────────────────────────
CMD ["python", "agent.py"]
