# Detiene instancias del dashboard ECOPUNTOS IA en ejecucion
# Uso: .\scripts\stop_dashboard.ps1

$ErrorActionPreference = "SilentlyContinue"
Set-Location (Split-Path $PSScriptRoot -Parent)

$detenidos = 0
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*streamlit*' -and $_.CommandLine -like '*dashboard*' } |
    ForEach-Object {
        Write-Host "Deteniendo dashboard (PID $($_.ProcessId))..." -ForegroundColor Yellow
        Stop-Process -Id $_.ProcessId -Force
        $detenidos++
    }

if ($detenidos -eq 0) {
    Write-Host "No habia instancias del dashboard en ejecucion." -ForegroundColor DarkGray
} else {
    Write-Host "Listo: $detenidos instancia(s) detenida(s)." -ForegroundColor Green
    Start-Sleep -Seconds 2
}
