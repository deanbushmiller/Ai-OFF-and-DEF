#!/usr/bin/env bash
# ===========================================================================
#  SecLLM Bootcamp - Lab 2 setup  (macOS)
#
#  Windows students: use setup.ps1 instead.
#
#  Run it:   bash setup.sh
#  Hard mode: bash setup.sh --challenge      (commands hidden, work them out)
#
#  This script installs nothing on your machine. It checks that Docker is
#  ready, works out which image your Mac needs, downloads it, runs the lab,
#  and saves your results next to this file.
# ===========================================================================
set -uo pipefail

IMAGE="ghcr.io/deanbushmiller/seclm-labs"
LAB="lab2"
NEXT_LAB="lab3"          # set to "" on the final lab
NEXT_LAB_NAME="Lab 3 - Advanced prompt injection"
CONTAINER="seclm-lab2-run"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="$HERE/lab2-results.txt"
EXTRA_ARGS=("$@")

ok()   { printf '  [ OK ]  %s\n' "$*"; }
bad()  { printf '  [FAIL]  %s\n' "$*"; }
warn() { printf '  [WARN]  %s\n' "$*"; }
info() { printf '          %s\n' "$*"; }
hr()   { printf '%s\n' "----------------------------------------------------------------"; }

printf '\n'; hr
printf '  SecLLM Bootcamp - Lab 2: RAG and semantic ingestion attacks\n'
printf '  Setup and launcher (macOS)\n'
hr; printf '\n'
printf '  Checking prerequisites...\n\n'

# --- 1. Docker installed? ---------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  bad "Docker is not installed."
  printf '\n'
  info "Install Docker Desktop, then run this script again:"
  info "  https://www.docker.com/products/docker-desktop/"
  printf '\n'
  exit 1
fi
ok "Docker is installed  ($(docker --version 2>/dev/null))"

# --- 2. Docker daemon running? ----------------------------------------------
if ! docker info >/dev/null 2>&1; then
  bad "Docker is installed but not running."
  printf '\n'
  info "Open Docker Desktop from Applications and wait for the whale icon in"
  info "your menu bar to stop animating, then run this script again."
  printf '\n'
  exit 1
fi
ok "Docker is running"

# --- 3. Detect operating system and hardware --------------------------------
HW="$(uname -m)"
OS_VER="$(sw_vers -productVersion 2>/dev/null || echo 'unknown')"

case "$HW" in
  arm64)  DETECTED="arm64"; CONFIG="macOS on Apple Silicon (M-series)" ;;
  x86_64) DETECTED="amd64"; CONFIG="macOS on Intel" ;;
  *)      DETECTED="";      CONFIG="unrecognised hardware: $HW" ;;
esac

# Cross-check against the Docker engine. The engine is the authority.
ENGINE_ARCH="$(docker version --format '{{.Server.Arch}}' 2>/dev/null || echo '')"
if [ -n "$ENGINE_ARCH" ] && [ -n "$DETECTED" ] && [ "$ENGINE_ARCH" != "$DETECTED" ]; then
  warn "Your hardware says $DETECTED but the Docker engine says $ENGINE_ARCH."
  info "Trusting the Docker engine. Using $ENGINE_ARCH."
  DETECTED="$ENGINE_ARCH"
fi
[ -z "$DETECTED" ] && [ -n "$ENGINE_ARCH" ] && DETECTED="$ENGINE_ARCH"

ok "Detected: macOS $OS_VER  /  $HW"
info "Configuration: $CONFIG"
info "Image needed:  $DETECTED"

# --- 4. Confirm or override --------------------------------------------------
printf '\n'; hr
printf '  Is this right?\n\n'
printf '    [Enter]  Yes - use %s   (detected automatically)\n' "$DETECTED"
printf '    1        Mac, Apple Silicon (M1/M2/M3/M4)  -> arm64\n'
printf '    2        Mac, Intel                        -> amd64\n'
hr
printf '  Choice: '
if [ -t 0 ]; then read -r CHOICE || CHOICE=""; else CHOICE=""; fi
case "${CHOICE:-}" in
  1) DETECTED="arm64" ;;
  2) DETECTED="amd64" ;;
esac
printf '\n'; ok "Using image architecture: $DETECTED"

# --- 5. Disk space -----------------------------------------------------------
AVAIL_GB="$(df -g "$HOME" 2>/dev/null | awk 'NR==2 {print $4}')"
if [ -n "${AVAIL_GB:-}" ]; then
  if [ "$AVAIL_GB" -lt 2 ]; then
    warn "Only ${AVAIL_GB} GB free. The lab needs about 2 GB. It may fail."
  else
    ok "Disk space: ${AVAIL_GB} GB free (need ~2 GB)"
  fi
fi

# --- 6. Pull -----------------------------------------------------------------
TAG="$IMAGE:$LAB-$DETECTED"
printf '\n'; hr

# The previous lab offers to pre-pull this image when it finishes. If the
# student took that offer, it is already here and there is nothing to download.
if docker image inspect "$TAG" >/dev/null 2>&1; then
  printf '  Lab image is already on your machine.\n'
  printf '  %s\n' "$TAG"
  hr; printf '\n'
  ok "No download needed - the previous lab fetched this for you."
  SKIP_PULL=1
else
  printf '  Downloading the lab image. About 190-600 MB, usually 1-3 minutes.\n'
  printf '  %s\n' "$TAG"
  hr; printf '\n'
  SKIP_PULL=0
fi

if [ "$SKIP_PULL" -eq 0 ] && ! docker pull "$TAG"; then
  printf '\n'; bad "Could not download the lab image."
  printf '\n'
  info "Most likely causes, in order:"
  info "  1. The image is not public yet. Tell the instructor you got"
  info "     'denied' or 'unauthorized' on $TAG"
  info "  2. No internet connection, or a workplace VPN blocking ghcr.io."
  info "  3. Docker Desktop is running but has lost its network - quit and"
  info "     reopen it, then try again."
  printf '\n'
  info "Contact the instructor through GitHub with the error above."
  printf '\n'
  exit 1
fi
printf '\n'; ok "Image downloaded"

# --- 7. Run ------------------------------------------------------------------
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
printf '\n'; hr
printf '  Starting the lab. You will be asked to choose beginner or\n'
printf '  expert mode. Beginner types 10 checked commands; expert gets\n'
printf '  a real shell and works from LAB.md.\n'
hr; printf '\n'

docker run -it --name "$CONTAINER" "$TAG" lab 2 "${EXTRA_ARGS[@]}"
RUN_RC=$?

# --- 8. Recover the transcript ----------------------------------------------
printf '\n'
if docker cp "$CONTAINER:/labs/lab2/lab2-results.txt" "$RESULTS" >/dev/null 2>&1; then
  ok "Results saved: $RESULTS"
  info "Paste the BEFORE and AFTER evidence block into the class chat."
else
  warn "Could not save the results file (lab exit code $RUN_RC)."
  info "Scroll up in this window to copy your scan output instead."
fi

docker rm -f "$CONTAINER" >/dev/null 2>&1 || true

# --- 10. Pre-pull the next lab ----------------------------------------------
# Done here, while the student is still online and still has the terminal open.
# The shared base layers are already on disk, so the next lab is a small delta.
if [ -n "${NEXT_LAB:-}" ]; then
  NEXT_TAG="$IMAGE:$NEXT_LAB-$DETECTED"
  printf '\n'; hr
  printf '  BEFORE YOU GO - get the next lab now\n'
  hr
  printf '\n'
  info "$NEXT_LAB_NAME"
  info "Most of it is already on your machine (the labs share layers), so"
  info "this is a much smaller download than the first one."
  printf '\n'
  info "Doing it now means no waiting at the start of the next session."
  printf '\n  Pull it now? [Y/n] '
  if [ -t 0 ]; then read -r GETNEXT || GETNEXT=""; else GETNEXT="n"; fi
  case "${GETNEXT:-y}" in
    [Nn]*)
      printf '\n'
      info "Skipped. Run this before the next session:"
      info "    docker pull $NEXT_TAG"
      ;;
    *)
      printf '\n'
      info "(If $NEXT_LAB is not published yet you will see an error here."
      info " That is expected and harmless - lab 1 is already complete.)"
      printf '\n'
      if docker pull "$NEXT_TAG"; then
        printf '\n'; ok "$NEXT_LAB_NAME is ready on your machine."
        # Absolute path: works no matter which directory the student ran from.
        LABS_DIR="$(cd "$HERE/../.." 2>/dev/null && pwd || true)"
        NEXT_SCRIPT=""
        [ -n "$LABS_DIR" ] && NEXT_SCRIPT="$LABS_DIR/$NEXT_LAB/setup/setup.sh"
        printf '\n'
        if [ -n "$NEXT_SCRIPT" ] && [ -f "$NEXT_SCRIPT" ]; then
          info "When you are ready to start it, run:"
          printf '\n      bash "%s"\n\n' "$NEXT_SCRIPT"
        else
          info "The next lab's setup script is not in this folder yet."
          info "Pull the course repository again before the next session."
        fi
      else
        printf '\n'
        warn "Could not pull it yet."
        info "If the instructor has not published $NEXT_LAB, this is expected."
        info "Try again before the next session:"
        info "    docker pull $NEXT_TAG"
      fi
      ;;
  esac
fi

printf '\n'; hr
printf '  Lab 2 complete. The image stays on your machine for the next lab.\n'
hr; printf '\n'
