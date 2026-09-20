#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
#   docker run --rm -it --network none <image> lab 12
#
# NO -p FLAG, deliberately. serve.py binds 127.0.0.1 INSIDE the container, so a
# published port forwards to a listener that refuses every connection - measured
# with a control on 2026-09-19, which is when we found lab 3 had been telling
# students to open a browser at a port that never answered. This lab publishes
# nothing and promises nothing.
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "12" ]; then
  shift 2
  # Map the realistic hostname to our own loopback. This MUST happen at run time:
  # Docker rewrites /etc/hosts on container start, so a build-time entry is lost.
  grep -q "news.acme.com" /etc/hosts 2>/dev/null || \
    echo "127.0.0.1  news.acme.com" >> /etc/hosts 2>/dev/null || true
  # The mock site must be up before any step runs. Loopback only.
  python /labs/lab12/serve.py &
  SERVER_PID=$!
  trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
  for _ in $(seq 1 40); do
    curl -sf -o /dev/null http://127.0.0.1:8012/article.html && break
    sleep 0.25
  done
  exec python /labs/lab12/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  grep -q "news.acme.com" /etc/hosts 2>/dev/null || \
    echo "127.0.0.1  news.acme.com" >> /etc/hosts 2>/dev/null || true
  python /labs/lab12/serve.py & sleep 1
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it --network none <image> lab 12
  docker run --rm -it --network none <image> lab 12 --expert   expert mode (real shell)
  docker run --rm -it <image> shell                            shell inside the container

Lab 12 - Defending against prompt injection

The mock site is served on 127.0.0.1 INSIDE the container. No port is published
and none is needed; read the pages with curl from inside the lab.
USAGE
exit 64
