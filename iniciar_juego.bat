@echo off
setlocal
chcp 65001 >nul
title Zoonauta
set "PYTHONUTF8=1"
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
  py -3 -m codigo.interfaz.iniciar %*
  goto :fin
)

where python >nul 2>&1
if %errorlevel%==0 (
  python -m codigo.interfaz.iniciar %*
  goto :fin
)

echo No se encontro Python 3. Instala Python 3.10 o posterior para ejecutar Zoonauta.
:fin
pause
