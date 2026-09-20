#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
#   docker run --rm -it --network none <image> lab 14
#
# Lab 14 runs a mock MCP server on 127.0.0.1:8014 INSIDE this container. ask.py
# starts it as a child process and stops it again when the exchange is done, the
# same way a real MCP host spawns a server it was configured to trust.
#
# The port is never published. A loopback bind inside a container cannot be
# reached from the host - lab 12 measured that - so -p would promise a view that
# does not work. There is nothing to see in a browser anyway.
#
# The --network none in the line above is not decoration. This lab is about what
# you accept from a third-party server, so it runs with no route to any of them
# and says so on screen.
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "14" ]; then
  shift 2
  exec python /labs/lab14/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  cd /labs/lab14 || exit 1
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it --network none <image> lab 14
  docker run --rm -it --network none <image> lab 14 --expert   expert mode (real shell)
  docker run --rm -it <image> shell                            shell inside the container

Lab 14 - Defending MCP tool calls

Nothing in this lab reaches the network. The mock MCP server binds 127.0.0.1:8014
inside this container and is started and stopped by the lab itself; no port is
published and none is needed.
USAGE
exit 64
