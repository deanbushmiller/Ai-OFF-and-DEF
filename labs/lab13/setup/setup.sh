#!/usr/bin/env bash
# ===========================================================================
#  SecLLM Bootcamp - Lab 13 setup  (macOS and Linux)
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
LAB="lab13"
NEXT_LAB="lab14"         # set to "" on the final lab
NEXT_LAB_NAME="Lab 14 - Defending MCP tool calls"
CONTAINER="seclm-lab13-run"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="$HERE/lab13-results.txt"
AUDIT="$HERE/lab13-audit-log.jsonl"
POLICY="$HERE/lab13-policy.json"
EXTRA_ARGS=("$@")

OS_KIND="$(uname -s | tr '[:upper:]' '[:lower:]')"   # darwin | linux

ok()   { printf '  [ OK ]  %s\n' "$*"; }
bad()  { printf '  [FAIL]  %s\n' "$*"; }
warn() { printf '  [WARN]  %s\n' "$*"; }
info() { printf '          %s\n' "$*"; }
hr()   { printf '%s\n' "----------------------------------------------------------------"; }

printf '\n'; hr
printf '  SecLLM Bootcamp - Lab 13: Defending AI agents\n'
printf '  Setup and launcher (macOS / Linux)\n'
hr; printf '\n'
# Where am I? The script resolves its own location, so it does not matter where the
# course was cloned or which directory it was launched from. Printing it makes a clone
# that landed somewhere unexpected visible now, not later as a puzzling copy failure.
info "Course folder : $(cd "$HERE/../../.." 2>/dev/null && pwd || echo '?')"
info "Results go to : $HERE"
printf '\n'
printf '  Checking prerequisites...\n\n'

# --- 1. Docker installed? ---------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  bad "Docker is not installed."
  printf '\n'
  if [ "$OS_KIND" = "linux" ]; then
    info "Install Docker Engine, then run this script again."
    info ""
    info "  Debian / Ubuntu:  sudo apt install docker.io"
    info "  Fedora / RHEL:    sudo dnf install docker"
    info "  Arch:             sudo pacman -S docker"
    info ""
    info "  Or the official packages:  https://docs.docker.com/engine/install/"
    info ""
    info "After installing:"
    info "    sudo systemctl enable --now docker"
    info "    sudo usermod -aG docker \$USER"
    info "    (then log out and back in)"
  else
    info "Install Docker Desktop, then run this script again:"
    info "  https://www.docker.com/products/docker-desktop/"
  fi
  printf '\n'
  exit 1
fi
ok "Docker is installed  ($(docker --version 2>/dev/null))"

# --- 2. Docker daemon running? ----------------------------------------------
if ! docker info >/dev/null 2>&1; then
  # On Linux the most common cause is NOT a stopped daemon - it is that the
  # user is not in the docker group. Distinguish them, or students chase the
  # wrong problem.
  if [ "$OS_KIND" = "linux" ] && ! groups 2>/dev/null | tr ' ' '\n' | grep -qx docker; then
    bad "You are not in the 'docker' group."
    printf '\n'
    info "Docker is installed, but your user cannot talk to it without sudo."
    info "Fix it once:"
    info ""
    info "    sudo usermod -aG docker \$USER"
    info ""
    info "Then LOG OUT AND BACK IN - a new terminal is not enough, the group"
    info "membership is attached at login. Then run this script again."
    printf '\n'
    info "To check it worked:  groups | grep docker"
    printf '\n'
    exit 1
  fi
  bad "Docker is installed but not running."
  printf '\n'
  if [ "$OS_KIND" = "linux" ]; then
    info "Start the Docker service:"
    info ""
    info "    sudo systemctl start docker"
    info "    sudo systemctl enable docker     # start it at boot"
    info ""
    info "Then run this script again."
  else
    info "Open Docker Desktop from Applications and wait for the whale icon in"
    info "your menu bar to stop animating, then run this script again."
  fi
  printf '\n'
  exit 1
fi
ok "Docker is running"

# --- 3. Detect operating system and hardware --------------------------------
HW="$(uname -m)"

# NOTE: macOS reports arm64, Linux reports aarch64. Same chip, different string.
case "$HW" in
  arm64|aarch64) DETECTED="arm64" ;;
  x86_64|amd64)  DETECTED="amd64" ;;
  *)             DETECTED="" ;;
esac

if [ "$OS_KIND" = "linux" ]; then
  OS_VER="$(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || echo 'Linux')"
  case "$DETECTED" in
    arm64) CONFIG="Linux on ARM (aarch64)" ;;
    amd64) CONFIG="Linux on Intel or AMD (x86_64)" ;;
    *)     CONFIG="unrecognised hardware: $HW" ;;
  esac
else
  OS_VER="macOS $(sw_vers -productVersion 2>/dev/null || echo 'unknown')"
  case "$DETECTED" in
    arm64) CONFIG="macOS on Apple Silicon (M-series)" ;;
    amd64) CONFIG="macOS on Intel" ;;
    *)     CONFIG="unrecognised hardware: $HW" ;;
  esac
fi

# Cross-check against the Docker engine. The engine is the authority.
ENGINE_ARCH="$(docker version --format '{{.Server.Arch}}' 2>/dev/null || echo '')"
if [ -n "$ENGINE_ARCH" ] && [ -n "$DETECTED" ] && [ "$ENGINE_ARCH" != "$DETECTED" ]; then
  warn "Your hardware says $DETECTED but the Docker engine says $ENGINE_ARCH."
  info "Trusting the Docker engine. Using $ENGINE_ARCH."
  DETECTED="$ENGINE_ARCH"
fi
[ -z "$DETECTED" ] && [ -n "$ENGINE_ARCH" ] && DETECTED="$ENGINE_ARCH"

ok "Detected: $OS_VER  /  $HW"
info "Configuration: $CONFIG"
info "Image needed:  $DETECTED"

# --- 4. Confirm or override --------------------------------------------------
printf '\n'; hr
printf '  Is this right?\n\n'
printf '    [Enter]  Yes - use %s   (detected automatically)\n' "$DETECTED"
if [ "$OS_KIND" = "linux" ]; then
  printf '    1        ARM (aarch64)                     -> arm64\n'
  printf '    2        Intel or AMD (x86_64)             -> amd64\n'
else
  printf '    1        Mac, Apple Silicon (M1/M2/M3/M4)  -> arm64\n'
  printf '    2        Mac, Intel                        -> amd64\n'
fi
hr
printf '  Choice: '
if [ -t 0 ]; then read -r CHOICE || CHOICE=""; else CHOICE=""; fi
case "${CHOICE:-}" in
  1) DETECTED="arm64" ;;
  2) DETECTED="amd64" ;;
esac
printf '\n'; ok "Using image architecture: $DETECTED"

# --- 5. Disk space -----------------------------------------------------------
# df -g is BSD/macOS; Linux needs -BG.
if [ "$OS_KIND" = "linux" ]; then
  AVAIL_GB="$(df -BG "$HOME" 2>/dev/null | awk 'NR==2 {gsub(/G/,"",$4); print $4}')"
else
  AVAIL_GB="$(df -g "$HOME" 2>/dev/null | awk 'NR==2 {print $4}')"
fi
if [ -n "${AVAIL_GB:-}" ]; then
  if [ "$AVAIL_GB" -lt 2 ]; then
    warn "Only ${AVAIL_GB} GB free. The lab needs about 1 GB. It may fail."
  else
    ok "Disk space: ${AVAIL_GB} GB free (need ~1 GB)"
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
  printf '  Downloading the lab image.\n'
  printf '\n'
  printf '  If you have done lab 4 on this machine, this is about 21 MB on\n'
  printf '  Apple Silicon, 24 MB on Intel: the OCR engine and the base are\n'
  printf '  already on your disk down to the byte, and this pull is only the\n'
  printf '  two small libraries this lab carries for itself. From a clean\n'
  printf '  machine it is about 101 MB on Apple Silicon, 105 MB on Intel -\n'
  printf '  no language model, the smallest image in the course either way.\n'
  printf '  Measured on the published image.\n'
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
printf '  This lab runs with NO NETWORK AT ALL - --network none, below.\n'
printf '  That is the lesson, not a precaution: this lab is about keeping\n'
printf '  an agent away from things it was never meant to reach, so it\n'
printf '  runs that way itself. The agent, its tools, the policy file,\n'
printf '  the model and the audit log are all inside the container.\n'
printf '  No port is published and none is needed.\n'
printf '\n'
printf '  Starting the lab. You will be asked to choose beginner or\n'
printf '  expert mode. Beginner types 10 checked commands; expert gets\n'
printf '  a real shell and works from LAB.md.\n'
printf '\n'
printf '  If you did labs 3 to 8 or lab 12 on this machine, the 1.09 GB\n'
printf '  model layer is already on your disk and is not fetched again.\n'
printf '\n'
printf '  A local language model runs four times in this lab. Each\n'
printf '  answer takes 10-20 seconds, longer on a 2-core machine. The\n'
printf '  model WILL be tricked every time; watch what the broker does\n'
printf '  about it.\n'
hr; printf '\n'

# --network none, as labs 9 to 12 do. The addendum's rule is that a defend lab
# runs under the control it teaches; ATLAS AML.M0032 names egress restriction as
# part of the boundary this lab is about, so the lab runs with no route out.
#
# The pre-pull at the end of this script is a separate docker command and is
# unaffected - it runs after the container has exited.
#
# NO -p. Lab 13 serves nothing: no port, no background process, nothing to
# publish. The contract reserves 8013 only if a UI is ever added, and none is.
docker run -it --network none --name "$CONTAINER" "$TAG" lab 13 "${EXTRA_ARGS[@]}"
RUN_RC=$?

# --- 8. Recover the transcript and the images --------------------------------
printf '\n'
if docker cp "$CONTAINER:/labs/lab13/lab13-results.txt" "$RESULTS" >/dev/null 2>&1; then
  ok "Results saved: $RESULTS"
  info "Paste the evidence table from the last step into the class chat."
  info "The column that matters is the gate the privileged call died at,"
  info "walking 3 -> 2 -> 1 while the clean run keeps passing."
else
  warn "Could not save the results file (lab exit code $RUN_RC)."
  info "Scroll up in this window to copy the evidence block instead."
fi

# The broker's own tool-call log comes out too. It is the evidence for this
# lab and the thing worth re-reading after class: every attempted call, with
# the verdict on each. Regenerated on every run.
rm -f "$AUDIT" 2>/dev/null || true
if docker cp "$CONTAINER:/labs/lab13/audit-log.jsonl" "$AUDIT" >/dev/null 2>&1; then
  ok "Audit log saved: $AUDIT"
  info "One JSON object per attempted tool call. Look for the run where"
  info "set_role is ALLOW and read_notes:admin is DENY - that is an agent"
  info "that was fully compromised and still did not get the data."
else
  info "No audit log to copy - the agent did not run this time."
fi

# The policy file as the student left it, so they can see their own two
# changes next to the log that prompted them.
rm -f "$POLICY" 2>/dev/null || true
if docker cp "$CONTAINER:/labs/lab13/policy.json" "$POLICY" >/dev/null 2>&1; then
  ok "Policy saved: $POLICY"
  info "active=false on admin-notes-ro, and set_role gone from the"
  info "triage allow-list. Two edits, in a file the agent cannot write."
else
  info "No policy file to copy."
fi

docker rm -f "$CONTAINER" >/dev/null 2>&1 || true

# --- 10. Pre-pull the next lab ----------------------------------------------
# Done here, while the student is still online and still has the terminal open.
if [ -n "${NEXT_LAB:-}" ]; then
  NEXT_TAG="$IMAGE:$NEXT_LAB-$DETECTED"
  printf '\n'; hr
  printf '  BEFORE YOU GO - get the next lab now\n'
  hr
  printf '\n'
  info "$NEXT_LAB_NAME"
  info "Lab 14 is the same dependency tier as this lab, so it shares the"
  info "1.09 GB model layer you already have on disk. A student who has"
  info "lab 13 pulls a small delta for lab 14, not the model again."
  info "No exact size until it is published and measured."
  printf '\n'
  info "Doing it now, while you are online, means no waiting at the start"
  info "of the next session."
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
      info " That is expected and harmless - lab 13 is already complete.)"
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
printf '  Lab 13 complete. The image stays on your machine for the next lab.\n'
hr; printf '\n'
