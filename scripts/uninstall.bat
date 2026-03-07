@echo off

echo MUIOGO Uninstall / Reset
echo.

set "VENV_DIR=%USERPROFILE%\.venvs\muiogo"
set "DATA_STORAGE=%~dp0..\WebAPP\DataStorage"

echo This will remove:
echo   Virtual env: %VENV_DIR%
echo   Demo data
echo.

pause

if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
    echo Removed virtual environment.
)

if exist "%DATA_STORAGE%\CLEWs Demo" (
    rmdir /s /q "%DATA_STORAGE%\CLEWs Demo"
    echo Removed demo data.
)

if exist "%DATA_STORAGE%\.demo_data_installed.json" (
    del "%DATA_STORAGE%\.demo_data_installed.json"
)

echo.

set "GLPK_DIR=%LOCALAPPDATA%\glpk"
set "CBC_DIR=%LOCALAPPDATA%\cbc"

if exist "%GLPK_DIR%" (
    rmdir /s /q "%GLPK_DIR%"
    echo Removed GLPK manual install.
)

if exist "%CBC_DIR%" (
    rmdir /s /q "%CBC_DIR%"
    echo Removed CBC manual install.
)

echo Uninstall complete.