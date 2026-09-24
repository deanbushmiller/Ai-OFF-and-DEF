#!/usr/bin/env bash
# testconnect.sh - check that this computer can download the course's language model.
#
# Run it from the course folder:   bash testconnect.sh
# Then copy the ONE line that starts with GHCR-TEST into the class chat.
#
# What it does (about 5-70 seconds, writes nothing to disk):
#   1. Pings the server Docker downloads the lab images from, 10 times.
#   2. Downloads 20 MB of the real model layer over ONE connection - the same
#      request Docker makes - and measures the speed.
#   3. Prints one line with the results and a verdict.
#
# Why the speed matters: GitHub's download link for each image layer expires
# 5-10 minutes after it is issued, and the download is cut when it does. The
# language model is one 1.09 GB layer, so it must arrive at about 1.8 MB/s or
# faster or it can never finish.

HOST="pkg-containers.githubusercontent.com"
REPO="deanbushmiller/seclm-labs"
LAYER="sha256:d9ae46c7ff1e789554d81c957ae0b48bcba3f48601761937e6274ebfb57b1e9b"

# 1. Latency and packet loss. Some networks block ping; that is fine.
PING_OUT=$(ping -c 10 -i 0.2 "$HOST" 2>/dev/null)
LOSS=$(echo "$PING_OUT" | grep -o '[0-9.]*% packet loss' | cut -d% -f1)
LATENCY=$(echo "$PING_OUT" | tail -1 | awk -F/ '{print $5}')

# 2. Speed: 20 MB of the model layer, one connection, anonymous read-only token.
TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:${REPO}:pull&service=ghcr.io" \
        | sed 's/.*"token":"\([^"]*\)".*/\1/')
SPEED=$(curl -sL -o /dev/null -r 0-20971519 \
        -H "Authorization: Bearer ${TOKEN}" \
        -w "%{speed_download}" \
        "https://ghcr.io/v2/${REPO}/blobs/${LAYER}")

# 3. One line to paste.
#    now=   the lab images as published today (single 1.09 GB model layer)
#    split= the model split into six layers of at most 190 MB (being tested)
#    OK = downloads first time; RETRY = finishes after some restarts; FAIL = cannot finish
awk -v s="${SPEED:-0}" -v l="${LOSS:-blocked}" -v r="${LATENCY:-blocked}" 'BEGIN {
  m = s / 1e6
  v_now   = (m >= 3.6)  ? "OK" : (m >= 1.8)  ? "RETRY" : "FAIL"
  v_split = (m >= 0.63) ? "OK" : (m >= 0.32) ? "RETRY" : "FAIL"
  printf "GHCR-TEST speed=%.2fMB/s latency=%sms loss=%s%% now=%s split=%s\n", m, r, l, v_now, v_split
}'
