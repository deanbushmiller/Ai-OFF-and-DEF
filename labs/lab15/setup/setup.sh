#!/usr/bin/env bash
# ===========================================================================
#  SecLLM Bootcamp - Lab 15 setup  (macOS and Linux)
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
LAB="lab15"
# EMPTY ON PURPOSE. Lab 15 is the last PULLED lab. Lab 16 is the red-team
# process intro: instructor demo material and a take-home runbook, run against
# targets in the student's own authorised environment after class, not an
# offline container. There is nothing to pre-pull, so this script points at
# lab 16's runbook instead. See section 10.
NEXT_LAB=""
CONTAINER="seclm-lab15-run"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="$HERE/lab15-results.txt"
DETECTLOG="$HERE/lab15-detect-log.jsonl"
DETECTOR="$HERE/lab15-detector.json"
EXTRA_ARGS=("$@")

OS_KIND="$(uname -s | tr '[:upper:]' '[:lower:]')"   # darwin | linux

ok()   { printf '  [ OK ]  %s\n' "$*"; }
bad()  { printf '  [FAIL]  %s\n' "$*"; }
warn() { printf '  [WARN]  %s\n' "$*"; }
info() { printf '          %s\n' "$*"; }
hr()   { printf '%s\n' "----------------------------------------------------------------"; }

printf '\n'; hr
printf '  SecLLM Bootcamp - Lab 15: Defending against AI-scaled attacks\n'
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
  printf '  If you have done any of labs 3 to 8, 12, 13 or 14 on this\n'
  printf '  machine, this is a small delta - tens of kilobytes. Those labs\n'
  printf '  and this one share the same base, the same Python packages and\n'
  printf '  the same 1.09 GB language model, byte for byte, so none of it\n'
  printf '  is downloaded twice. From a clean machine it is about 1.2 GB.\n'
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
printf '  That is the lesson, not a precaution: this lab is about spotting\n'
printf '  traffic leaving a network, so it is given no network to leave.\n'
printf '  The estate telemetry, the mock collector, the detector, the\n'
printf '  model and the log are all inside the container.\n'
printf '  The collector binds 127.0.0.1:8015 in there. No port is\n'
printf '  published and none is needed - nothing to open in a browser.\n'
printf '\n'
printf '  Starting the lab. You will be asked to choose beginner or\n'
printf '  expert mode. Beginner types 10 checked commands; expert gets\n'
printf '  a real shell and works from LAB.md.\n'
printf '\n'
printf '  If you did labs 3 to 8 or 12 to 14 on this machine, the 1.09 GB\n'
printf '  model layer is already on your disk and is not fetched again.\n'
printf '\n'
printf '  A local language model runs ONCE in this lab, for about 20\n'
printf '  seconds on two cores. Everything else is plain Python and runs\n'
printf '  in well under a second.\n'
printf '\n'
printf '  One step is SUPPOSED to get past your detector. When you reach\n'
printf '  it the lab says so. That is the most useful step in the lab.\n'
hr; printf '\n'

# --network none, as labs 9 to 14 do. The addendum's rule is that a defend lab
# runs under the control it teaches, and this lab is about detecting traffic
# leaving a network - so it is given no network to leave.
#
# NO -p. Lab 15 runs its mock collector on 127.0.0.1:8015 INSIDE the container,
# started and stopped by the lab itself. A loopback bind inside a container
# cannot be reached from the host - lab 12 measured that - so -p would promise
# a browser view that does not work. There is nothing to publish: the collector
# answers one local process and exits with it.
docker run -it --network none --name "$CONTAINER" "$TAG" lab 15 "${EXTRA_ARGS[@]}"
RUN_RC=$?

# --- 8. Recover the transcript and the images --------------------------------
printf '\n'
if docker cp "$CONTAINER:/labs/lab15/lab15-results.txt" "$RESULTS" >/dev/null 2>&1; then
  ok "Results saved: $RESULTS"
  info "Paste the three numbers from the last step into the class chat:"
  info "lab 7's detector on a real estate, yours after tuning, and what"
  info "evasion cost the attacker. The middle one is the achievement."
else
  warn "Could not save the results file (lab exit code $RUN_RC)."
  info "Scroll up in this window to copy the evidence block instead."
fi

# The detector's own log comes out too. It is the evidence for this lab and the
# thing worth re-reading after class: every detector that ran, with its true and
# false positive counts. Regenerated on every run.
rm -f "$DETECTLOG" 2>/dev/null || true
if docker cp "$CONTAINER:/labs/lab15/detect-log.jsonl" "$DETECTLOG" >/dev/null 2>&1; then
  ok "Detector log saved: $DETECTLOG"
  info "One JSON object per verdict. The field to follow is 'precision':"
  info "0.0069 with the detector you inherited from lab 7, 1.0000 with"
  info "the one you tuned - same estate, same beacon, same day."
else
  info "No detector log to copy - the lab did not run this time."
fi

# The detector configuration as the student left it, so they can see their own
# two changes next to the log that prompted them.
rm -f "$DETECTOR" 2>/dev/null || true
if docker cp "$CONTAINER:/labs/lab15/detector.json" "$DETECTOR" >/dev/null 2>&1; then
  ok "Detector config saved: $DETECTOR"
  info "Two edits: the threshold you chose from the sweep, and the"
  info "matching window you widened after the miss. The second one is"
  info "the interesting change, because it is not a number."
else
  info "No detector config to copy."
fi

docker rm -f "$CONTAINER" >/dev/null 2>&1 || true

# --- 10. The hand-off, and there is nothing to download ----------------------
# DELIBERATELY NOT A PRE-PULL. Lab 15 is the last pulled lab. Lab 16 is the
# red-team process intro: instructor demo material plus a take-home runbook the
# student follows in their OWN authorised environment after class. It is not an
# offline container and it is the one place the course's offline rule relaxes,
# so offering "docker pull seclm-labs:lab16" here would promise a tag that will
# never exist. NEXT_LAB is empty above for exactly this reason.
printf '\n'; hr
printf '  THAT IS THE LAST LAB TO DOWNLOAD\n'
hr
printf '\n'
info "Labs 1 to 15 are done. There is no lab 16 image and nothing more"
info "to pull - and that is on purpose."
printf '\n'
info "Lab 16 is the red-team process: how you VALIDATE that the controls"
info "you built in labs 9 to 15 still hold when somebody attacks them."
info "The instructor demonstrates it live, and you get a take-home"
info "runbook for setting the workflow up in your own authorised"
info "environment afterwards."
printf '\n'
info "You have already run the one-command version of it. Step 6 of this"
info "lab generated a variant your detector had never seen and tested"
info "your own control against it. ATLAS calls that AML.M0035, AI Red"
info "Team. Lab 16 is that, as a process, with a scope agreement."
printf '\n'
# Absolute path: works no matter which directory the student ran from.
LABS_DIR="$(cd "$HERE/../.." 2>/dev/null && pwd || true)"
RUNBOOK=""
[ -n "$LABS_DIR" ] && RUNBOOK="$LABS_DIR/lab16/RUNBOOK.md"
if [ -n "$RUNBOOK" ] && [ -f "$RUNBOOK" ]; then
  info "The runbook is here:"
  printf '\n      %s\n\n' "$RUNBOOK"
else
  info "The runbook ships with lab 16. If it is not in your course folder"
  info "yet, pull the course repository again before the last session."
fi

printf '\n'; hr
printf '  BEFORE THE LAST SESSION\n'
hr
printf '\n'
info "Check you have submitted evidence for every defend lab:"
info "  lab  9  supply chain        lab 13  agents"
info "  lab 10  RAG ingestion       lab 14  MCP tool calls"
info "  lab 11  multimodal          lab 15  AI-scaled attacks  <- this one"
info "  lab 12  injection firewall"
printf '\n'
info "Lab 16 builds on all seven. If one is missing, say so in the class"
info "chat before the session rather than during it."

printf '\n'; hr
printf '  Lab 15 complete. Labs 1 to 15 are done.\n'
hr; printf '\n'
