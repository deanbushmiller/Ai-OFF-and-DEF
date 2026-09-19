#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
# Run convention across every lab:   docker run --rm -it <image> lab <N>
#   docker run --rm -it <image> lab 9              choose beginner or expert
#   docker run --rm -it <image> lab 9 --challenge  commands hidden
#
# Lab 9 is the first defend lab. When the image is consolidated, this file
# grows a case per lab rather than being forked - see the consolidation
# contract in the build prompt.
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "9" ]; then
  shift 2
  exec python /labs/lab9/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it <image> lab 9               run lab 9
  docker run --rm -it <image> lab 9 --challenge   hide the commands
  docker run --rm -it <image> shell               shell inside the container

Lab 9 - Defending the model supply chain

  Run it with no network, which is what the lab is about:
    docker run --rm -it --network none <image> lab 9
USAGE
exit 64
