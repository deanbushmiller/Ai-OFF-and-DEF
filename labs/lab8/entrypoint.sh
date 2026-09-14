#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
#   docker run --rm -it <image> lab 8
#
# Lab 8 runs no model, serves nothing and opens no port. It is the only lab in
# the course that does no work at all beyond reading two JSON files.
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "8" ]; then
  shift 2
  exec python /labs/lab8/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  cd /labs/lab8 || exit 1
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it <image> lab 8
  docker run --rm -it <image> lab 8 --expert      expert mode (real shell)
  docker run --rm -it <image> shell               shell inside the container

Lab 8 - Offensive recap and transition to defense
USAGE
exit 64
