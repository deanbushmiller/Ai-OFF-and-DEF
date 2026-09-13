#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
#   docker run --rm -it <image> lab 5
#
# Lab 5 serves nothing and needs no network: no background server to start, no
# /etc/hosts entry to write, no port to bind.
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "5" ]; then
  shift 2
  exec python /labs/lab5/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  cd /labs/lab5 || exit 1
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it <image> lab 5
  docker run --rm -it <image> lab 5 --expert      expert mode (real shell)
  docker run --rm -it <image> shell               shell inside the container

Lab 5 - Exploiting AI agents and excessive agency
USAGE
exit 64
