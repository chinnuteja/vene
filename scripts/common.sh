# Shared helpers for the Linux/macOS scripts. Mirrors scripts/common.ps1.
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
export NEXT_TELEMETRY_DISABLED=1
RUNTIME="$PROJECT_ROOT/.local/runtime.json"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing required tool: $1" >&2; exit 1; }; }

runtime_get() { node -e "const r=JSON.parse(require('fs').readFileSync(process.argv[1],'utf8').replace(/^﻿/,''));const v=r[process.argv[2]];process.stdout.write(v===undefined||v===null?'':String(v))" "$RUNTIME" "$1"; }

require_runtime() { [ -f "$RUNTIME" ] || { echo 'Run scripts/setup.sh first.' >&2; exit 1; }; }

free_port() {
  node -e "const net=require('net');let p=Number(process.argv[1]);(function t(){const s=net.createServer();s.once('error',()=>{p++;t()});s.listen(p,'127.0.0.1',()=>s.close(()=>console.log(p)))})()" "$1"
}

# Postgres binaries: PATH first, then Debian/Ubuntu and Homebrew layouts.
pg_bin() {
  if command -v pg_ctl >/dev/null 2>&1; then dirname "$(command -v pg_ctl)"; return; fi
  if command -v pg_config >/dev/null 2>&1 && [ -x "$(pg_config --bindir)/pg_ctl" ]; then pg_config --bindir; return; fi
  for dir in $(ls -d /usr/lib/postgresql/*/bin /opt/homebrew/opt/postgresql@*/bin /usr/local/opt/postgresql@*/bin 2>/dev/null | sort -rV); do
    [ -x "$dir/pg_ctl" ] && { echo "$dir"; return; }
  done
  echo 'No Postgres server binaries found. Install PostgreSQL 16 or 17 (server package).' >&2; exit 1
}

# Postgres refuses to run as root. In root-only containers, the project cluster runs as the
# system "postgres" account; elsewhere it runs as the current user.
as_db_user() {
  if [ "$(id -u)" = 0 ]; then
    id postgres >/dev/null 2>&1 || { echo 'Running as root needs a "postgres" system account.' >&2; exit 1; }
    runuser -u postgres -- "$@"
  else "$@"; fi
}

database_env() {
  export DATABASE_URL="$(runtime_get database_url)"
  export TEST_DATABASE_URL="$(runtime_get test_database_url)"
}
