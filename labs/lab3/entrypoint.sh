#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
#   docker run --rm -it -p 127.0.0.1:8003:8003 <image> lab 3
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "3" ]; then
  shift 2
  # Map the realistic hostname to our own loopback. This MUST happen at run time:
  # Docker rewrites /etc/hosts on container start, so a build-time entry is lost.
  grep -q "news.acme.com" /etc/hosts 2>/dev/null || \
    echo "127.0.0.1  news.acme.com" >> /etc/hosts 2>/dev/null || true
  # The mock site must be up before any step runs. Loopback only.
  python /labs/lab3/serve.py &
  SERVER_PID=$!
  trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
  for _ in $(seq 1 40); do
    curl -sf -o /dev/null http://127.0.0.1:8003/article.html && break
    sleep 0.25
  done
  exec python /labs/lab3/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  grep -q "news.acme.com" /etc/hosts 2>/dev/null || \
    echo "127.0.0.1  news.acme.com" >> /etc/hosts 2>/dev/null || true
  python /labs/lab3/serve.py & sleep 1
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it -p 127.0.0.1:8003:8003 <image> lab 3
  docker run --rm -it <image> lab 3 --expert      expert mode (real shell)
  docker run --rm -it <image> shell               shell inside the container

Lab 3 - Advanced prompt injection
USAGE
exit 64
