param([switch]$Test,[switch]$ResetSavedSyntheticVisits)
. "$PSScriptRoot/common.ps1"
$runtime=Read-Runtime
if ($Test) { Set-DatabaseEnvironment $runtime -Test } else { Set-DatabaseEnvironment $runtime }
Invoke-Checked (Join-Path $ProjectRoot '.venv/Scripts/python.exe') @('-m','alembic','-c','services/backend/alembic.ini','upgrade','head')
$arguments=@('scripts/reset-demo.py')
if ($Test) { $arguments+='--test' }
if ($ResetSavedSyntheticVisits) { $arguments+='--reset-saved-synthetic-visits' }
Invoke-Checked (Join-Path $ProjectRoot '.venv/Scripts/python.exe') $arguments
