#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
#   docker run --rm -it <image> lab 2               choose beginner or expert
#   docker run --rm -it <image> lab 2 --expert      straight to the shell
#   docker run --rm -it <image> lab 2 --challenge   beginner, commands hidden
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "2" ]; then
  shift 2
  exec python /labs/lab2/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then exec /bin/bash; fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it <image> lab 2               run lab 2
  docker run --rm -it <image> lab 2 --expert      expert mode (real shell)
  docker run --rm -it <image> lab 2 --challenge   beginner, commands hidden
  docker run --rm -it <image> shell               shell inside the container

Lab 2 - RAG and semantic ingestion attacks
USAGE
exit 64
