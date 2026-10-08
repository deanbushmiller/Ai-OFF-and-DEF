#!/usr/bin/env bash
# check-run.sh - connection check, test 2 (Mac and Linux):
# can this computer download a script from GitHub and run it, without admin rights?
#
# Students run it with the one command on connection-check/README.md. If this
# text is on screen as output, both download and execution already worked.

echo ""
echo "  ================================================================"
echo "   Test 2 - can this computer download and run a script?"
echo "  ================================================================"
echo "  [OK] Downloaded a file from GitHub"
echo "  [OK] Ran the downloaded script"

# Administrator (root)? Not required for this test - reported so we know.
if [ "$(id -u)" -eq 0 ]; then
  echo "  [i]  Running as administrator (root): yes"
else
  echo "  [i]  Running as administrator (root): no (that is fine for this test)"
fi

# System and processor type - the labs ship a separate image for
# Intel/AMD (x86_64) and ARM (arm64 / aarch64, including Apple Silicon).
OS_NAME="$(uname -s)"
[ "$OS_NAME" = "Darwin" ] && OS_NAME="macOS $(sw_vers -productVersion 2>/dev/null)"
echo "  [i]  System: $OS_NAME    Processor type: $(uname -m)    bash $BASH_VERSION"

# Tidy up: this script deletes itself.
rm -f "$0" 2>/dev/null

echo ""
echo "  RESULT: PASS - continue on to the next test."
echo ""
