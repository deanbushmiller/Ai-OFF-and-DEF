#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
#   docker run --rm -it --network none <image> lab 13
#
# Lab 13 serves nothing: no port, no /etc/hosts entry, no background process.
# There is nothing to publish and nothing to promise.
#
# The --network none in the line above is not decoration. This lab's own subject
# includes egress control as the boundary a classifier is not (ATLAS AML.M0032),
# so it runs under the control it teaches, and says so on screen.
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "13" ]; then
  shift 2
  exec python /labs/lab13/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  cd /labs/lab13 || exit 1
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it --network none <image> lab 13
  docker run --rm -it --network none <image> lab 13 --expert   expert mode (real shell)
  docker run --rm -it <image> shell                            shell inside the container

Lab 13 - Defending AI agents

Nothing in this lab reaches the network. No port is published and none is
needed: the agent, its tools, the policy, the model and the audit log are all
inside this container.
USAGE
exit 64
