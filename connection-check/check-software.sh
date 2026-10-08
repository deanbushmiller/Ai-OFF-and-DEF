#!/usr/bin/env bash
# check-software.sh - connection check, test 3 (Mac and Linux): software needed for the labs.
#   1. git installed
#   2. Docker installed and running
#   3. any other Docker work already on this computer (counted, never changed)
#
# Students run it with the one command on connection-check/README.md.
# Needs no administrator rights (no sudo). Changes nothing.

ok=1
COURSE_IMAGE="ghcr.io/deanbushmiller/seclm-labs"
count() { grep -c . ; }

echo ""
echo "  ================================================================"
echo "   Test 3 - software needed for the labs"
echo "  ================================================================"

# --- 1. git ----------------------------------------------------------------
if command -v git >/dev/null 2>&1 && git --version >/dev/null 2>&1; then
  echo "  [OK] git is installed ($(git --version | sed 's/git version //'))"
else
  echo "  [!!] git is NOT installed."
  if [ "$(uname -s)" = "Darwin" ]; then
    echo "       Install it by running:  xcode-select --install"
  else
    echo "       Install it with your package manager, e.g.  sudo apt install git"
  fi
  ok=0
fi

# --- 2. Docker -------------------------------------------------------------
running=0
if ! command -v docker >/dev/null 2>&1; then
  echo "  [!!] Docker is NOT installed. Install Docker Desktop (Mac) or Docker Engine (Linux):"
  echo "       https://docs.docker.com/get-docker/"
  ok=0
else
  echo "  [OK] Docker is installed ($(docker --version | sed 's/Docker version //; s/,.*//'))"
  if info=$(docker info --format '{{.ServerVersion}}' 2>&1); then
    echo "  [OK] Docker is running (engine $info)"
    running=1
  else
    case "$info" in
      *ermission*denied*)
        echo "  [!!] Docker is installed, but your account is not allowed to use it."
        echo "       Linux: sudo usermod -aG docker \$USER   then log out and back in."
        ;;
      *)
        echo "  [!!] Docker is installed but NOT running."
        echo "       Start Docker Desktop (Mac) or the docker service (Linux),"
        echo "       wait until it is running, then run this test again."
        ;;
    esac
    ok=0
  fi
fi

# --- 3. Other Docker work already here (counts only) ------------------------
if [ "$running" -eq 1 ]; then
  images=$(docker images --format '{{.Repository}}' 2>/dev/null)
  total=$(printf '%s\n' "$images" | count)
  course=$(printf '%s\n' "$images" | grep -cx "$COURSE_IMAGE")
  other=$((total - course))
  containers=$(docker ps -aq 2>/dev/null | count)
  up=$(docker ps -q 2>/dev/null | count)
  volumes=$(docker volume ls -q 2>/dev/null | count)
  if [ "$other" -eq 0 ] && [ "$containers" -eq 0 ] && [ "$volumes" -eq 0 ]; then
    echo "  [i]  No other Docker work on this computer."
  else
    echo "  [i]  Other Docker work on this computer: $other image(s), $containers container(s)"
    echo "       ($up running), $volumes volume(s)."
    echo "       The labs will NOT touch, change or delete any of these."
    echo "       They only add their own images (seclm-labs) and remove their own"
    echo "       containers (named seclm-labN-run)."
  fi
  [ "$course" -gt 0 ] && echo "  [i]  Course lab images already downloaded: $course"
fi

# Tidy up: this script deletes itself.
rm -f "$0" 2>/dev/null

echo ""
if [ "$ok" -eq 1 ]; then
  echo "  RESULT: PASS - continue on to the next test."
else
  echo "  RESULT: STOP - fix the [!!] item(s) above, then run this test again."
fi
echo ""
