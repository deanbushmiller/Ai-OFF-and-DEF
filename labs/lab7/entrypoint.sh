#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
#   docker run --rm -it <image> lab 7
#
# Lab 7 runs a collector process alongside the lab, but beacon.py starts and
# stops it, so the entrypoint stays the same shape as every other lab. Nothing
# binds outside 127.0.0.1 and no port is published.
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "7" ]; then
  shift 2
  exec python /labs/lab7/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  cd /labs/lab7 || exit 1
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it <image> lab 7
  docker run --rm -it <image> lab 7 --expert      expert mode (real shell)
  docker run --rm -it <image> shell               shell inside the container

Lab 7 - AI-powered attack orchestration
USAGE
exit 64
