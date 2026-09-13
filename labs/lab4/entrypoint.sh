#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
#   docker run --rm -it <image> lab 4
#
# Lab 4 serves nothing and needs no network, so unlike lab 3 there is no
# background server to start and no /etc/hosts entry to write.
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "4" ]; then
  shift 2
  exec python /labs/lab4/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  cd /labs/lab4 || exit 1
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it <image> lab 4
  docker run --rm -it <image> lab 4 --expert      expert mode (real shell)
  docker run --rm -it <image> shell               shell inside the container

Lab 4 - Multimodal and vision-based exploits
USAGE
exit 64
