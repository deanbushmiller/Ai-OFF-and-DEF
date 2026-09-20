#!/usr/bin/env bash
# Shared entrypoint for the consolidated image.
#   docker run --rm -it --network none <image> lab 15
#
# Lab 15 runs a mock collector on 127.0.0.1:8015 INSIDE this container. inbox.py,
# limit.py and evade.py start it as a child process and stop it again when they
# are done; nothing is left running between commands, so a failed step cannot
# leave a process behind to confuse the next one.
#
# The port is never published. A loopback bind inside a container cannot be
# reached from the host - lab 12 measured that - so -p would promise a view that
# does not work. There is nothing to see in a browser anyway.
#
# The --network none in the line above is not decoration. This lab is about
# detecting traffic leaving a network, so it is given no network to leave.
set -uo pipefail

if [ "${1:-}" = "lab" ] && [ "${2:-}" = "15" ]; then
  shift 2
  exec python /labs/lab15/runner.py "$@"
fi
if [ "${1:-}" = "shell" ]; then
  cd /labs/lab15 || exit 1
  exec /bin/bash
fi

cat <<'USAGE'
SecLLM Bootcamp labs

  docker run --rm -it --network none <image> lab 15
  docker run --rm -it --network none <image> lab 15 --expert   expert mode (real shell)
  docker run --rm -it <image> shell                            shell inside the container

Lab 15 - Defending against AI-scaled attacks

Nothing in this lab reaches the network. The mock collector binds 127.0.0.1:8015
inside this container and is started and stopped by the lab itself; no port is
published and none is needed.
USAGE
exit 64
