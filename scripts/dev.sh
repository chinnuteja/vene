#!/usr/bin/env bash
# Linux/macOS launcher. Same flags as dev.ps1: --mode fixture|live, --production,
# --model-live, --tts-live, --live-providers.
source "$(dirname "$0")/common.sh"
require_runtime
database_env
exec node scripts/dev.mjs "$@"
