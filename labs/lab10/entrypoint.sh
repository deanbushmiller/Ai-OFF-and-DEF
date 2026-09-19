#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
# Run convention across every lab:   docker run --rm -it <image> lab <N>
#   docker run --rm -it <image> lab 10              choose beginner or expert
#   docker run --rm -it <image> lab 10 --challenge  commands hidden
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "10" ]; then
  shift 2
  exec python /labs/lab10/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it <image> lab 10               run lab 10
  docker run --rm -it <image> lab 10 --challenge   hide the commands
  docker run --rm -it <image> shell                shell inside the container

Lab 10 - Defending RAG ingestion

  Run it with no network, which is what proves the retrieval hijack is local:
    docker run --rm -it --network none <image> lab 10
USAGE
exit 64
