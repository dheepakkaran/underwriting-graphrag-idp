#!/usr/bin/env bash
# Docker smoke test: build, start, hit /health and /queue, stop. Writes results/docker_smoke.txt
set -e
cd "$(dirname "$0")"
docker compose up --build -d
for i in $(seq 1 30); do curl -sf localhost:8000/health >/dev/null && break; sleep 2; done
{
  echo "date: $(date -Is)"
  echo "image: $(docker compose images --format json 2>/dev/null | head -c 200)"
  echo "GET /health -> $(curl -s localhost:8000/health)"
  echo "GET /queue  -> $(curl -s localhost:8000/queue | python3 -c 'import sys,json;print(len(json.load(sys.stdin)),"referred files")')"
  echo "GET /       -> $(curl -s -o /dev/null -w '%{http_code}' localhost:8000/)"
} | tee results/docker_smoke.txt
docker compose down
