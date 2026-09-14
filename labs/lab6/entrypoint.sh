#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
#   docker run --rm -it <image> lab 6
#
# Lab 6 runs three processes - an MCP server, a proxy between, and a client -
# but the runner starts and stops them, so the entrypoint stays the same shape
# as every other lab. Nothing binds outside 127.0.0.1 and no port is published.
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "6" ]; then
  shift 2
  exec python /labs/lab6/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  cd /labs/lab6 || exit 1
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it <image> lab 6
  docker run --rm -it <image> lab 6 --expert      expert mode (real shell)
  docker run --rm -it <image> shell               shell inside the container

Lab 6 - MCP and interface hijacking
USAGE
exit 64
