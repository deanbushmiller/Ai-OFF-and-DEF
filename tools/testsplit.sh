#!/usr/bin/env bash
# testsplit.sh - INSTRUCTOR TEST: download the six model parts of the split
# lab 12 image (lab12-splittest-amd64) one at a time, with progress, outside Docker.
#
# Run from the course folder:
#   bash testsplit.sh        all six parts
#   bash testsplit.sh 1      first part only
#
# For each part it shows curl's progress bar, then OK or CUT. A CUT part is
# retried (up to 3 attempts), the way Docker retries a layer. Nothing is saved.
#
# How to read it:
#   all parts OK          the split downloads on this network; if docker pull still
#                         sits at "Pulling fs layer", the problem is Docker on this machine
#   parts CUT, then OK    GitHub's download link expired mid-part; the retry finished it
#   a part CUT 3 times    this network is too slow even for 190 MB parts

PARTS=${1:-6}
ATTEMPTS=3
REPO="deanbushmiller/seclm-labs"
SHARDS="sha256:b7e83f18d2689008ad17313f9418f27346d849e34269d2ddcce0df8078fd803f:190209381
sha256:4493b0e053f93efa4c3fdc5d9a5061940cce68fde1e4717d3de346d1ed34634f:186026772
sha256:6646e146359f4ab8fde51c84d166b5d99f9642ea6211ecff8d174fe10606ee34:181150035
sha256:6fbe2009c25e470f45bcd78396b0c3eef79f329d35b75ad10f0fefd39cb74bea:188174566
sha256:d81f296f8439fd9120b48a00c3054eef3e06cb504249b6a008d798f42829bfa4:188259357
sha256:3e99ba9076d815af9c6c9e73bd3ca1bede7cb51dab00ac5ca31ea7937addf8c9:158570409"
[ "$PARTS" -ge 1 ] 2>/dev/null || PARTS=1
[ "$PARTS" -gt 6 ] && PARTS=6

fmt() { printf '%dm%02ds' $(( $1 / 60 )) $(( $1 % 60 )); }

echo ""
echo "  ================================================================"
echo "   Split-model download test (lab12-splittest-amd64)"
echo "  ================================================================"
echo "  Downloads $PARTS model part(s) of up to 190 MB each, one at a time,"
echo "  the way Docker would. At 0.4 MB/s each part takes about 8 minutes."
echo "  Nothing is saved. Press Ctrl+C to stop at any time."
echo ""

ok=0; tries=0; start=$(date +%s); i=0
for entry in $(printf '%s\n' "$SHARDS" | head -n "$PARTS"); do
  i=$((i + 1))
  digest=${entry%:*}; size=${entry##*:}
  a=1; done_part=0
  while [ "$a" -le "$ATTEMPTS" ] && [ "$done_part" -eq 0 ]; do
    tries=$((tries + 1))
    printf '  [part %d/%d] %d MB   attempt %d of %d\n' "$i" "$PARTS" $((size / 1000000)) "$a" "$ATTEMPTS"
    TOKEN_JSON=$(curl -s --max-time 20 "https://ghcr.io/token?scope=repository:${REPO}:pull&service=ghcr.io")
    TOKEN=$(printf '%s' "$TOKEN_JSON" | sed -n 's/.*"token":"\([^"]*\)".*/\1/p')
    if [ -z "$TOKEN" ]; then
      echo "        !! Could not reach ghcr.io (firewall/proxy?)"
    else
      printf '        '
      t0=$(date +%s)
      out=$(curl -# -L -o /dev/null -H "Authorization: Bearer ${TOKEN}" \
            -w "%{size_download} %{speed_download}" "https://ghcr.io/v2/${REPO}/blobs/${digest}")
      rc=$?
      secs=$(( $(date +%s) - t0 ))
      got=${out%% *}; bps=${out##* }
      if [ "$rc" -eq 0 ] && [ "${got%.*}" = "$size" ]; then
        printf '        OK    %d MB in %s  (%s MB/s)\n' $((size / 1000000)) "$(fmt "$secs")" \
          "$(awk -v b="$bps" 'BEGIN{printf "%.2f", b/1e6}')"
        ok=$((ok + 1)); done_part=1
      else
        printf '        CUT   at %d of %d MB after %s  (curl exit %d) - link expired or connection dropped\n' \
          $(( ${got%.*} / 1000000 )) $((size / 1000000)) "$(fmt "$secs")" "$rc"
      fi
    fi
    a=$((a + 1))
  done
  echo ""
done

total=$(( $(date +%s) - start ))
echo "  ================================================================"
echo "   Done. Result:"
echo "  ================================================================"
printf 'SPLIT-TEST parts_ok=%d/%d attempts=%d total_time=%s\n' "$ok" "$PARTS" "$tries" "$(fmt "$total")"
echo ""
