param([ValidateSet('auto','native','docker')][string]$DatabaseMode = 'auto', [switch]$SkipDependencies)
. "$PSScriptRoot/common.ps1"
New-Item -ItemType Directory -Force -Path '.local', '.local/logs', '.local/downloads' | Out-Null
if (-not $SkipDependencies) {
    $pnpmArgs = @('install')
    if (Test-Path -LiteralPath 'pnpm-lock.yaml') { $pnpmArgs += '--frozen-lockfile' }
    Invoke-Checked $PnpmExe $pnpmArgs
    $uvArgs = @('sync', '--python', $PythonExe)
    if (Test-Path -LiteralPath 'uv.lock') { $uvArgs += '--frozen' }
    Invoke-Checked $UvExe $uvArgs
}
$runtimePath = Join-Path $ProjectRoot '.local/runtime.json'
Invoke-Checked $NodeExe @('scripts/ensure-browser.mjs')
if (Test-Path -LiteralPath $runtimePath) {
    $runtime = Read-Runtime
} else {
    $selectedMode = $DatabaseMode
    if ($selectedMode -eq 'auto') {
        & docker version --format '{{.Server.Version}}' 2>$null | Out-Null
        $selectedMode = if ($LASTEXITCODE -eq 0) { 'docker' } else { 'native' }
    }
    $port = Get-FreePort 5432
    $password = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
    $runtime = [pscustomobject]@{
        database_mode = $selectedMode
        postgres_port = $port
        postgres_password = $password
        database_url = "postgresql+psycopg://vene_dev:${password}@127.0.0.1:${port}/bring_vene"
        test_database_url = "postgresql+psycopg://vene_dev:${password}@127.0.0.1:${port}/bring_vene_test"
        web_port = Get-FreePort 3000
        api_port = Get-FreePort 8000
    }
    $runtime | ConvertTo-Json | Set-Content -LiteralPath $runtimePath -Encoding utf8
}
if ($DatabaseMode -ne 'auto' -and $runtime.database_mode -ne $DatabaseMode) {
    throw 'An existing database configuration uses a different mode. Preserve it or migrate it explicitly.'
}
if ($runtime.database_mode -eq 'native') {
    $metadata = Get-Content -LiteralPath 'infra/postgres-binary.json' -Raw | ConvertFrom-Json
    $archivePath = Join-Path $ProjectRoot '.local/downloads/postgresql-17.11-windows-x64.zip'
    $toolsPath = Join-Path $ProjectRoot '.local/tools/postgres'
    $binPath = Join-Path $toolsPath 'pgsql/bin'
    if (-not (Test-Path -LiteralPath (Join-Path $binPath 'pg_ctl.exe'))) {
        if (-not (Test-Path -LiteralPath $archivePath)) { Invoke-WebRequest -Uri $metadata.url -OutFile $archivePath }
        if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $metadata.sha256) {
            throw 'Postgres archive does not match the pinned digest.'
        }
        New-Item -ItemType Directory -Force -Path $toolsPath | Out-Null
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $archive = [IO.Compression.ZipFile]::OpenRead($archivePath)
        try {
            foreach ($entry in $archive.Entries) {
                if ($entry.FullName -notmatch '^pgsql/(bin/|lib/|share/|server_license.txt$|commandlinetools_3rd_party_licenses.txt$)') { continue }
                if ($entry.FullName.EndsWith('/')) { continue }
                $target = [IO.Path]::GetFullPath((Join-Path $toolsPath $entry.FullName))
                $allowedRoot = [IO.Path]::GetFullPath($toolsPath) + [IO.Path]::DirectorySeparatorChar
                if (-not $target.StartsWith($allowedRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe archive path.' }
                New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
                [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $target, $true)
            }
        } finally { $archive.Dispose() }
    }
    $dataPath = Join-Path $ProjectRoot '.local/pgdata'
    if (-not (Test-Path -LiteralPath (Join-Path $dataPath 'PG_VERSION'))) {
        $passwordFile = Join-Path $ProjectRoot '.local/pg-password'
        [IO.File]::WriteAllText($passwordFile, $runtime.postgres_password + [Environment]::NewLine)
        try {
            Invoke-Checked (Join-Path $binPath 'initdb.exe') @('-D', $dataPath, '-U', 'vene_dev', '--auth=scram-sha-256', '--encoding=UTF8', '--locale=C', "--pwfile=$passwordFile")
        } finally { Remove-Item -LiteralPath $passwordFile }
    }
    & (Join-Path $binPath 'pg_ctl.exe') status -D $dataPath 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Invoke-Checked (Join-Path $binPath 'pg_ctl.exe') @('start', '-D', $dataPath, '-l', (Join-Path $ProjectRoot '.local/logs/postgres.log'), '-o', "-h 127.0.0.1 -p $($runtime.postgres_port)", '-w')
    }
    $env:PGPASSWORD = $runtime.postgres_password
    try {
        foreach ($database in @('bring_vene', 'bring_vene_test')) {
            $exists = & (Join-Path $binPath 'psql.exe') -h 127.0.0.1 -p $runtime.postgres_port -U vene_dev -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$database'"
            if ($LASTEXITCODE -ne 0) { throw 'Postgres connection failed.' }
            if ($exists -ne '1') { Invoke-Checked (Join-Path $binPath 'createdb.exe') @('-h','127.0.0.1','-p',"$($runtime.postgres_port)",'-U','vene_dev',$database) }
        }
    } finally { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
    Invoke-Checked (Join-Path $binPath 'postgres.exe') @('--version')
} else {
    Invoke-Checked 'docker' @('pull', 'postgres:17.11')
    $image = & docker image inspect postgres:17.11 --format '{{index .RepoDigests 0}}'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve Postgres image digest.' }
    @("POSTGRES_IMAGE=$image", "POSTGRES_PASSWORD=$($runtime.postgres_password)", "POSTGRES_PORT=$($runtime.postgres_port)") | Set-Content -LiteralPath '.local/compose.env'
    Invoke-Checked 'docker' @('compose','--env-file','.local/compose.env','-f','infra/compose.yaml','up','-d','--wait')
}
Set-DatabaseEnvironment $runtime
Invoke-Checked $UvExe @('run','--frozen','alembic','-c','services/backend/alembic.ini','upgrade','head')
Invoke-Checked $UvExe @('run','--frozen','python','-m','bring_vene.seed')
Invoke-Checked $NodeExe @('scripts/contracts.mjs')
& "$PSScriptRoot/setup-media.ps1"
Invoke-Checked $UvExe @('run','--frozen','python','scripts/generate-audio-fixtures.py')
Write-Output "Setup ready. Database mode: $($runtime.database_mode). Start with scripts/dev.ps1."

