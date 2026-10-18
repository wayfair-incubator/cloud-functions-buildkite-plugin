#!/usr/bin/env bash
set -euo pipefail

# Refresh uv.lock (pass --upgrade to move every pin to its latest release). The
# deploy container exports its hashed requirements from uv.lock when it runs, so
# there is no second lock file to keep in sync.
uv lock "$@"

echo "Rebuild containers to verify there are no conflicts."
