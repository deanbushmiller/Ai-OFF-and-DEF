#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
# Run convention across all 8 labs:   docker run --rm -it <image> lab <N>
#   docker run --rm -it <image> lab 1              type the commands
#   docker run --rm -it <image> lab 1 --challenge  commands hidden
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "1" ]; then
  shift 2
  exec python /labs/lab1/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it <image> lab 1               run lab 1
  docker run --rm -it <image> lab 1 --challenge   hide the commands
  docker run --rm -it <image> shell               shell inside the container

Lab 1 - Data and model supply chain poisoning
USAGE
exit 64
