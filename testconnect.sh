#!/usr/bin/env bash
# testconnect.sh - check that this computer can download the course's language model.
#
# Run it from the course folder:   bash testconnect.sh
# Then copy the ONE line that starts with GHCR-TEST into the class chat.
#
# What it does (up to about 70 seconds, writes nothing to disk):
#   1. Pings the server Docker downloads the lab images from, 10 times.
#   2. Downloads 20 MB of the real model layer over ONE connection - the same
#      request Docker makes - and measures the speed.
#   3. Prints one line with the results and a verdict.
#
# Why the speed matters: GitHub's download link for each image layer expires
# 5-10 minutes after it is issued, and the download is cut when it does. The
# language model arrives in six parts of up to 190 MB, so each part must arrive at
# about 0.32 MB/s or faster or it can never finish (0.63 MB/s to finish first time).

HOST="pkg-containers.githubusercontent.com"
REPO="deanbushmiller/seclm-labs"
LAYER="sha256:b7e83f18d2689008ad17313f9418f27346d849e34269d2ddcce0df8078fd803f"
PINGS=10

echo ""
echo "  ================================================================"
echo "   Course connection check"
echo "  ================================================================"
echo "  Please stand by for up to 70 seconds while we test whether the"
echo "  labs will download on your network: speed, latency, and firewall"
echo "  filtering. Nothing is installed or saved."
echo ""

# ---------------------------------------------------------------------------
# 1. Latency and packet loss. Some networks block ping; that is fine.
#    The progress bar goes to the screen (stderr); the summary line is captured.
# ---------------------------------------------------------------------------
echo "  [1/2] Latency and packet loss"
echo "        $PINGS pings to the course image server ($HOST)."
echo "        High latency or lost packets slow down every download."
PING_SUMMARY=$(ping -c "$PINGS" -i 0.2 "$HOST" 2>/dev/null | {
  n=0; all=""
  while IFS= read -r line; do
    all="$all$line
"
    case "$line" in
      (*icmp_seq*)
        n=$((n + 1)); [ "$n" -gt "$PINGS" ] && n=$PINGS
        bar=$(printf '%*s' "$n" '' | tr ' ' '#')
        printf '\r        [%-10s] %d/%d pings' "$bar" "$n" "$PINGS" >&2 ;;
    esac
  done
  printf '\r        [##########] done          \n' >&2
  loss=$(printf '%s' "$all" | grep -o '[0-9.]*% packet loss' | cut -d% -f1)
  rtt=$(printf '%s' "$all" | grep -E 'min/avg' | awk -F/ '{print $5}')
  echo "${loss:-blocked} ${rtt:-blocked}"
})
LOSS=${PING_SUMMARY%% *}
LATENCY=${PING_SUMMARY##* }
[ -z "$PING_SUMMARY" ] && { LOSS=blocked; LATENCY=blocked; }
echo ""

# ---------------------------------------------------------------------------
# 2. Download speed and firewall filtering: 20 MB of the model layer over one
#    connection, anonymous read-only token. curl draws its own progress bar.
# ---------------------------------------------------------------------------
echo "  [2/2] Download speed and firewall filtering"
echo "        20 MB of the real lab model over one connection - the same way"
echo "        Docker downloads it. A firewall or proxy that blocks the course"
echo "        server shows up here."
NOTE=""
SPEED=0
TOKEN_JSON=$(curl -s --max-time 20 "https://ghcr.io/token?scope=repository:${REPO}:pull&service=ghcr.io")
case "$TOKEN_JSON" in
  *'"token":"'*)
    TOKEN=$(printf '%s' "$TOKEN_JSON" | sed 's/.*"token":"\([^"]*\)".*/\1/')
    printf '        '
    SPEED=$(curl -# -L -o /dev/null -r 0-20971519 \
            -H "Authorization: Bearer ${TOKEN}" \
            -w "%{speed_download}" \
            "https://ghcr.io/v2/${REPO}/blobs/${LAYER}")
    awk -v s="${SPEED:-0}" 'BEGIN{exit !(s+0 == 0)}' \
      && NOTE=" note=BLOCKED-download-failed(firewall/proxy?)"
    ;;
  *)
    # ghcr.io could not be reached at all: a firewall or proxy, not a slow line.
    echo "        !! Could not reach ghcr.io"
    NOTE=" note=BLOCKED-cannot-reach-ghcr.io(firewall/proxy?)"
    ;;
esac

echo ""
echo "  ================================================================"
echo "   Done. Copy the line below into the class chat and add your country:"
echo "  ================================================================"
echo ""

# ---------------------------------------------------------------------------
# 3. One line to paste.
#    result= whether the lab images will download: the model comes in six parts
#            of up to 190 MB (published 2026-10-10)
#    OK = downloads first time; RETRY = finishes after some restarts; FAIL = cannot finish
# ---------------------------------------------------------------------------
awk -v s="${SPEED:-0}" -v l="$LOSS" -v r="$LATENCY" -v note="$NOTE" 'BEGIN {
  m = s / 1e6
  v = (m >= 0.63) ? "OK" : (m >= 0.32) ? "RETRY" : "FAIL"
  printf "GHCR-TEST speed=%.2fMB/s latency=%sms loss=%s%% result=%s%s\n", m, r, l, v, note
}'
echo ""
