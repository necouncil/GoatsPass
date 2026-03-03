@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title GoatsPass Installer

echo.
echo   ██████╗  ██████╗  █████╗ ████████╗███████╗██████╗  █████╗ ███████╗███████╗
echo   ██╔════╝ ██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔════╝██╔════╝
echo   ██║  ███╗██║   ██║███████║   ██║   ███████╗██████╔╝███████║███████╗███████╗
echo   ██║   ██║██║   ██║██╔══██║   ██║   ╚════██║██╔═══╝ ██╔══██║╚════██║╚════██║
echo   ╚██████╔╝╚██████╔╝██║  ██║   ██║   ███████║██║     ██║  ██║███████║███████║
echo    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝
echo.
echo   Password Manager — Windows Installer
echo   ----------------------------------------
echo.

:: ── Check Python ──────────────────────────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    where python3 >nul 2>&1
    if %errorlevel% neq 0 (
        echo   [ERROR] Python not found!
        echo.
        echo   Please install Python 3.9+ from https://www.python.org/downloads/
        echo   Make sure to check "Add Python to PATH" during installation.
        echo.
        pause
        start https://www.python.org/downloads/
        exit /b 1
    ) else (
        set PYTHON=python3
    )
) else (
    set PYTHON=python
)

for /f "tokens=*" %%i in ('!PYTHON! -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PY_VER=%%i
echo   [OK] Python %PY_VER% found

:: ── Upgrade pip ───────────────────────────────────────────────────────────────
echo   [~] Checking pip...
!PYTHON! -m pip install --quiet --upgrade pip
echo   [OK] pip ready

:: ── Install dependencies ──────────────────────────────────────────────────────
echo   [~] Installing dependencies (cryptography, argon2-cffi, Pillow)...
!PYTHON! -m pip install --quiet cryptography argon2-cffi Pillow
if %errorlevel% neq 0 (
    echo   [ERROR] Failed to install dependencies.
    echo   Try running this script as Administrator.
    pause
    exit /b 1
)
echo   [OK] Dependencies installed

:: ── Install dir ───────────────────────────────────────────────────────────────
set INSTALL_DIR=%LOCALAPPDATA%\GoatsPass
echo   [~] Installing to %INSTALL_DIR%...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

copy /Y "%~dp0goatspass.py" "%INSTALL_DIR%\goatspass.py" >nul
if exist "%~dp0icon.png" (
    copy /Y "%~dp0icon.png" "%INSTALL_DIR%\icon.png" >nul
    echo   [OK] Icon copied
)
echo   [OK] Files installed

:: ── Create Start Menu shortcut ────────────────────────────────────────────────
set SHORTCUT_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs
set SHORTCUT=%SHORTCUT_DIR%\GoatsPass.lnk
set VBS_TMP=%TEMP%\create_shortcut.vbs

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_TMP%"
echo sLinkFile = "%SHORTCUT%" >> "%VBS_TMP%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS_TMP%"
echo oLink.TargetPath = "!PYTHON!" >> "%VBS_TMP%"
echo oLink.Arguments = """%INSTALL_DIR%\goatspass.py""" >> "%VBS_TMP%"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%VBS_TMP%"
echo oLink.Description = "GoatsPass Password Manager" >> "%VBS_TMP%"
if exist "%INSTALL_DIR%\icon.png" (
    echo oLink.IconLocation = "%INSTALL_DIR%\icon.png" >> "%VBS_TMP%"
)
echo oLink.WindowStyle = 1 >> "%VBS_TMP%"
echo oLink.Save >> "%VBS_TMP%"
cscript //nologo "%VBS_TMP%"
del "%VBS_TMP%" >nul 2>&1
echo   [OK] Start Menu shortcut created

:: ── Desktop shortcut ──────────────────────────────────────────────────────────
set DESK_SHORTCUT=%USERPROFILE%\Desktop\GoatsPass.lnk
set VBS_TMP2=%TEMP%\create_desk.vbs
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_TMP2%"
echo Set oLink = oWS.CreateShortcut("%DESK_SHORTCUT%") >> "%VBS_TMP2%"
echo oLink.TargetPath = "!PYTHON!" >> "%VBS_TMP2%"
echo oLink.Arguments = """%INSTALL_DIR%\goatspass.py""" >> "%VBS_TMP2%"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%VBS_TMP2%"
echo oLink.Description = "GoatsPass Password Manager" >> "%VBS_TMP2%"
if exist "%INSTALL_DIR%\icon.png" (
    echo oLink.IconLocation = "%INSTALL_DIR%\icon.png" >> "%VBS_TMP2%"
)
echo oLink.WindowStyle = 1 >> "%VBS_TMP2%"
echo oLink.Save >> "%VBS_TMP2%"
cscript //nologo "%VBS_TMP2%"
del "%VBS_TMP2%" >nul 2>&1
echo   [OK] Desktop shortcut created

echo.
echo   ============================================
echo    GoatsPass installed successfully!
echo   ============================================
echo    - Start Menu: GoatsPass
echo    - Desktop shortcut created
echo    - Data stored in: %%APPDATA%%\GoatsPass
echo   ============================================
echo.
pause
