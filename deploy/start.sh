#!/bin/bash
cd /srv/leaderboard/backend
/opt/backend/bin/uvicorn main_api:app --host 127.0.0.1 --port 8080 &

# The agent trains its intent classifier at start; restart it if it exits.
cd /srv/leaderboard/agent
( while true; do /opt/agent/bin/python agent.py; echo "agent exited ($?), restarting in 5s"; sleep 5; done ) &

exec nginx -g "daemon off;"
