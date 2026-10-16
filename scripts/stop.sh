#!/usr/bin/env bash
# Stops only the processes started by scripts/dev.sh in this checkout. --infrastructure also
# stops the project's own Postgres cluster.
source "$(dirname "$0")/common.sh"
INFRASTRUCTURE=0
for arg in "$@"; do case "$arg" in --infrastructure) INFRASTRUCTURE=1 ;; *) echo "Unknown option: $arg" >&2; exit 1 ;; esac; done
PIDS=.local/processes.json
stop_tree() { local child; for child in $(pgrep -P "$1" 2>/dev/null); do stop_tree "$child"; done; kill "$1" 2>/dev/null || true; }
if [ -f "$PIDS" ]; then
  owner="$(node -e "const p=JSON.parse(require('fs').readFileSync('$PIDS','utf8'));console.log(p.root+'\n'+p.pid)")"
  root="$(echo "$owner" | sed -n 1p)"; pid="$(echo "$owner" | sed -n 2p)"
  [ "$root" = "$PROJECT_ROOT" ] || { echo 'Process ownership does not match this checkout.' >&2; exit 1; }
  if kill -0 "$pid" 2>/dev/null; then
    command="$(ps -o args= -p "$pid")"
    case "$command" in *"scripts/dev.mjs"*) stop_tree "$pid" ;; *) echo 'PID no longer belongs to the owned launcher. Refusing to stop it.' >&2; exit 1 ;; esac
  fi
  rm -f "$PIDS"
fi
if [ "$INFRASTRUCTURE" = 1 ] && [ -f .local/pgdata/PG_VERSION ]; then
  as_db_user "$(pg_bin)/pg_ctl" stop -D "$PROJECT_ROOT/.local/pgdata" -m fast -w
fi
echo 'Owned application processes stopped.'
