# All-in-one image: frontend + API + BAF agent behind one nginx port (3000).
# Build context = repo root:  docker build -f deploy/Dockerfile .
FROM node:20 AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
ARG VITE_AGENT_URL=wss://leaderboard-letz.besser-pearl.org/ws
ENV VITE_API_URL=/api VITE_AGENT_URL=$VITE_AGENT_URL
RUN npm run build

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*

# Separate venvs: BAF pins its own versions of packages the API also uses.
COPY backend/requirements.txt /tmp/backend-req.txt
RUN python -m venv /opt/backend \
    && /opt/backend/bin/pip install --no-cache-dir -r /tmp/backend-req.txt

COPY agent/requirements.txt /tmp/agent-req.txt
RUN python -m venv /opt/agent \
    && /opt/agent/bin/pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && grep -v "^torch" /tmp/agent-req.txt > /tmp/agent-notorch.txt \
    && /opt/agent/bin/pip install --no-cache-dir -r /tmp/agent-notorch.txt

# Same layout as the repo, so the agent's ../backend/data path resolves.
COPY backend/ /srv/leaderboard/backend/
COPY agent/ /srv/leaderboard/agent/
COPY --from=frontend-build /app/build /var/www/html
COPY deploy/nginx.conf /etc/nginx/sites-available/default
COPY deploy/start.sh /start.sh
RUN chmod +x /start.sh

# No LLM key in the image. To enable it, start the container with
# OPENAI_API_KEY, LETZEVAL_LLM_PROVIDER=openai, LETZEVAL_AGENT_MODE=llm.
# Thread caps: the node has 40 cores and torch oversubscribes without them.
ENV LETZEVAL_DB_PATH=/srv/leaderboard/backend/data/AI_Sandbox.db \
    LETZEVAL_LLM_PROVIDER=none \
    LETZEVAL_AGENT_MODE=classical \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    PYTHONUNBUFFERED=1

EXPOSE 3000
CMD ["/start.sh"]
