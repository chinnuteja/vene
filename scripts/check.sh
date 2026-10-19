#!/usr/bin/env bash
# Linux/macOS equivalent of check.ps1: --phase N or --all.
source "$(dirname "$0")/common.sh"
PHASE=1
while [ $# -gt 0 ]; do
  case "$1" in --phase) PHASE="$2"; shift 2 ;; --all) PHASE=all; shift ;; *) echo "Unknown option: $1" >&2; exit 1 ;; esac
done
IMPLEMENTED=12
if [ "$PHASE" = all ]; then PHASE=$IMPLEMENTED; echo "All implemented checks: Phases 1-$IMPLEMENTED. Live STT/model/TTS and physical acoustics remain separate gates."; fi
[[ "$PHASE" =~ ^[0-9]+$ ]] && [ "$PHASE" -ge 1 ] && [ "$PHASE" -le "$IMPLEMENTED" ] || { echo "Only Phases 1-$IMPLEMENTED checks are implemented. Later phases cannot be declared passed." >&2; exit 1; }
require_runtime
database_env
started=$(date +%s)
node --test scripts/child-logs.test.mjs
uv run --frozen pytest
node scripts/contracts.mjs --check
pnpm typecheck
NEXT_DIST_DIR=.next-check pnpm build
export NEXT_DIST_DIR=.next-check BRING_VENE_PHASE="$PHASE" BRING_VENE_BASE_URL="http://127.0.0.1:$(runtime_get web_port)"
unset BRING_VENE_E2E_GREP
node scripts/browser-check.mjs
node -e "
  const [phase,seconds]=process.argv.slice(1).map(Number);
  require('fs').writeFileSync('.local/check-phase-'+String(phase).padStart(2,'0')+'.json',JSON.stringify({phase,platform:process.platform,
    checked_at:new Date().toISOString(),duration_seconds:seconds,backend:'passed',contracts:'passed',typecheck:'passed',build:'passed',
    browser:'passed',mode:'fixture'},null,2)+'\n');
" "$PHASE" "$(( $(date +%s) - started ))"
echo "Phase $PHASE automated checks passed on $(uname -s). Visual browser review is recorded separately."
