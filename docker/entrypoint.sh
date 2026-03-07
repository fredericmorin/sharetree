#!/bin/sh
set -e

# Disable dev reload mode (default is on; containers should not hot-reload).
export SHARETREE_DEV=false

echo "Starting sharetree on :8000..."
exec sharetree
