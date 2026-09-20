#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
# Run convention across every lab:   docker run --rm -it <image> lab <N>
#   docker run --rm -it <image> lab 11              choose beginner or expert
#   docker run --rm -it <image> lab 11 --challenge  commands hidden
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "11" ]; then
  shift 2
  exec python /labs/lab11/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  cd /labs/lab11 || exit 1
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it <image> lab 11               run lab 11
  docker run --rm -it <image> lab 11 --challenge   hide the commands
  docker run --rm -it <image> shell                shell inside the container

Lab 11 - Defending multimodal input

  Run it with no network. Nothing here needs one, and it proves the hidden
  text is on your own disk, not fetched from anywhere:
    docker run --rm -it --network none <image> lab 11
USAGE
exit 64
