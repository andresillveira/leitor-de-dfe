@echo off
title Leitor de DFe
cd /d "%~dp0"

echo Verificando dependencias...
pip install -r requirements.txt --quiet 2>nul

echo Iniciando Leitor de DFe...
python src/main.py

if errorlevel 1 (
    echo.
    echo ERRO: Falha ao iniciar o programa.
    echo Verifique se o Python 3.9+ esta instalado.
    pause
)
