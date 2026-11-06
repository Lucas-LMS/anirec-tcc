param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$url = 'http://127.0.0.1:8765'
try { $ready = (Invoke-RestMethod "$url/api/health" -TimeoutSec 2).ok } catch { $ready = $false }
if (-not $ready) {
    $scriptPath = Join-Path $PSScriptRoot 'iniciar.sh'
    $linuxPath = (& wsl.exe -d Ubuntu -- wslpath -a $scriptPath).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível localizar o Ubuntu/WSL.' }
    $logs = Join-Path $PSScriptRoot '../output/prototipo/logs'
    New-Item -ItemType Directory -Force -Path $logs | Out-Null
    Start-Process -FilePath wsl.exe -ArgumentList @('-d','Ubuntu','--','bash',('"' + $linuxPath + '"')) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'servidor.log') -RedirectStandardError (Join-Path $logs 'erros.log') | Out-Null
    for ($attempt = 0; $attempt -lt 45; $attempt++) {
        Start-Sleep -Seconds 1
        try { $ready = (Invoke-RestMethod "$url/api/health" -TimeoutSec 2).ok } catch { $ready = $false }
        if ($ready) { break }
    }
    if (-not $ready) { throw "Servidor não iniciou. Consulte $logs" }
}
Write-Host "AniRec pronto: $url"
if (-not $NoBrowser) { Start-Process $url }
