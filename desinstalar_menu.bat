@echo off
title Desinstalar Menu de Contexto - Leitor de DFe

:: ──────────────────────────────────────────────
:: Solicita elevação de privilégio (UAC)
:: ──────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando permissao de administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo.
echo ========================================
echo   Leitor de DFe - Desinstalar Menu
echo ========================================
echo.

python src/instalar_menu.py --desinstalar

echo.
pause
