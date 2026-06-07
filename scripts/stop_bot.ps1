# Detiene instancias del bot ECOPUNTOS IA en ejecucion
# Uso: .\scripts\stop_bot.ps1

$ErrorActionPreference = "SilentlyContinue"
Set-Location (Split-Path $PSScriptRoot -Parent)

$detenidos = 0
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*src.bot.telegram_bot*' } |
    ForEach-Object {
        Write-Host "Deteniendo bot (PID $($_.ProcessId))..." -ForegroundColor Yellow
        Stop-Process -Id $_.ProcessId -Force
        $detenidos++
    }

if (Test-Path "data\bot.lock") {
    Remove-Item "data\bot.lock" -Force
}

if ($detenidos -eq 0) {
    Write-Host "No habia instancias del bot en ejecucion." -ForegroundColor DarkGray
} else {
    Write-Host "Listo: $detenidos instancia(s) detenida(s)." -ForegroundColor Green
    Start-Sleep -Seconds 2
}
