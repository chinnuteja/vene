#!/usr/bin/env bash
# Linux/macOS setup. Same result as scripts/setup.ps1: dependencies, a project-owned Postgres
# cluster with development and test databases, migrations, seed data, contracts, pinned LiveKit.
source "$(dirname "$0")/common.sh"
SKIP_DEPENDENCIES=0
for arg in "$@"; do case "$arg" in --skip-dependencies) SKIP_DEPENDENCIES=1 ;; *) echo "Unknown option: $arg" >&2; exit 1 ;; esac; done
need node; need pnpm; need uv; need curl
mkdir -p .local/logs .local/downloads .local/tools

if [ "$SKIP_DEPENDENCIES" = 0 ]; then
  pnpm install --frozen-lockfile
  uv sync --frozen --python 3.12
fi
node scripts/ensure-browser.mjs

if [ ! -f "$RUNTIME" ]; then
  port="$(free_port 5432)"
  password="$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")"
  node -e "
    const [file,port,password,web,api]=process.argv.slice(1);
    require('fs').writeFileSync(file,JSON.stringify({database_mode:'native',postgres_port:Number(port),postgres_password:password,
      database_url:'postgresql+psycopg://vene_dev:'+password+'@127.0.0.1:'+port+'/bring_vene',
      test_database_url:'postgresql+psycopg://vene_dev:'+password+'@127.0.0.1:'+port+'/bring_vene_test',
      web_port:Number(web),api_port:Number(api)},null,2)+'\n');
  " "$RUNTIME" "$port" "$password" "$(free_port 3000)" "$(free_port 8000)"
fi
[ "$(runtime_get database_mode)" = native ] || { echo 'This checkout uses Docker Postgres; run setup.ps1 or migrate it explicitly.' >&2; exit 1; }

BIN="$(pg_bin)"
DATA="$PROJECT_ROOT/.local/pgdata"
PORT="$(runtime_get postgres_port)"
if [ ! -f "$DATA/PG_VERSION" ]; then
  mkdir -p "$DATA"; chmod 700 "$DATA"
  [ "$(id -u)" = 0 ] && chown postgres "$DATA"
  pwfile="$(mktemp)"; runtime_get postgres_password > "$pwfile"; chmod 644 "$pwfile"
  as_db_user "$BIN/initdb" -D "$DATA" -U vene_dev --auth=scram-sha-256 --encoding=UTF8 --locale=C --pwfile="$pwfile" >/dev/null
  rm -f "$pwfile"
fi
if ! as_db_user "$BIN/pg_ctl" status -D "$DATA" >/dev/null 2>&1; then
  as_db_user "$BIN/pg_ctl" start -D "$DATA" -l "$DATA/server.log" -o "-h 127.0.0.1 -p $PORT -k $DATA" -w >/dev/null
fi
export PGPASSWORD="$(runtime_get postgres_password)"
for database in bring_vene bring_vene_test; do
  exists="$("$BIN/psql" -h 127.0.0.1 -p "$PORT" -U vene_dev -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$database'")"
  [ "$exists" = 1 ] || "$BIN/createdb" -h 127.0.0.1 -p "$PORT" -U vene_dev "$database"
done
unset PGPASSWORD
"$BIN/postgres" --version

database_env
uv run --frozen alembic -c services/backend/alembic.ini upgrade head
uv run --frozen python -m bring_vene.seed
node scripts/contracts.mjs
bash scripts/setup-media.sh
uv run --frozen python scripts/generate-audio-fixtures.py
if ! command -v espeak-ng >/dev/null 2>&1 && [ "$(uname)" != Darwin ]; then
  echo 'Note: install espeak-ng for the offline fixture voice. Speech checks fail visibly without it.'
fi
echo "Setup ready. Start with scripts/dev.sh."
