@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "SKILL_DIR=%SCRIPT_DIR%.."

if defined TACTILE_WINDOWS_PYTHON (
  set "PYTHON_BIN=%TACTILE_WINDOWS_PYTHON%"
) else (
  set "PYTHON_BIN=python"
)

"%PYTHON_BIN%" "%SKILL_DIR%\scripts\windows_interface.py" %*
exit /b %ERRORLEVEL%
