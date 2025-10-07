@echo off
REM =============================================================
REM  Rise of Kingdoms Bot - Main Launcher
REM  Simplified entry point to install, start, and manage the bot
REM =============================================================

setlocal EnableDelayedExpansion
color 0B
title Rise of Kingdoms Bot - Launcher

:MENU
cls
echo.
echo =============================================================
echo               🏰 RISE OF KINGDOMS BOT v1.1
echo =============================================================
echo.
echo   MAIN MENU
echo   ----------
echo   1. Install Bot (First Time Setup)
echo   2. Start Bot
echo   3. Check Requirements
echo   4. Open Logs Folder
echo   5. Help
echo   6. Exit
echo.
echo =============================================================
echo.

choice /C 123456 /N /M "Select option (1-6): " || goto INVALID_CHOICE

if errorlevel 6 goto EXIT
if errorlevel 5 goto HELP
if errorlevel 4 goto LOGS
if errorlevel 3 goto CHECK
if errorlevel 2 goto START
if errorlevel 1 goto INSTALL

:INVALID_CHOICE
echo.
echo Invalid choice! Please select a valid option (1-6).
timeout /t 2 >nul
goto MENU

:INSTALL
cls
echo.
echo =============================================================
echo                 Installing Bot...
echo =============================================================
echo.
if exist "INSTALL.bat" (
    call INSTALL.bat
) else (
    color 0C
    echo [ERROR] INSTALL.bat not found!
    echo Please ensure all bot files are in the same directory.
)
goto RETURN_TO_MENU

:START
cls
echo.
echo =============================================================
echo                 Starting Bot...
echo =============================================================
echo.
if exist "START_BOT.bat" (
    call START_BOT.bat
) else (
    color 0C
    echo [ERROR] START_BOT.bat not found!
    echo Please run installation first (Option 1).
)
goto RETURN_TO_MENU

:CHECK
cls
echo.
echo =============================================================
echo              Checking System Requirements...
echo =============================================================
echo.

set "ALL_GOOD=1"

echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python NOT installed
    echo    Download from: https://www.python.org/downloads/
    set "ALL_GOOD=0"
) else (
    for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo ✓ %%V
)
echo.

echo [2/5] Checking pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip NOT found
    set "ALL_GOOD=0"
) else (
    echo ✓ pip is installed
)
echo.

echo [3/5] Checking PyQt5...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo ❌ PyQt5 NOT installed
    echo    Run Option 1 to install dependencies.
    set "ALL_GOOD=0"
) else (
    echo ✓ PyQt5 is installed
)
echo.

echo [4/5] Checking bot files...
set "BOT_FILES_MISSING=0"
for %%F in ("bot_core.py" "config.json" "requirements.txt") do (
    if not exist "%%F" (
        echo ❌ %%F NOT found
        set "BOT_FILES_MISSING=1"
    )
)
if !BOT_FILES_MISSING!==0 echo ✓ All bot files are present
echo.

echo [5/5] Checking folders...
set "FOLDERS_MISSING=0"
for %%D in ("templates" "logs" "screenshots") do (
    if not exist "%%D" (
        echo ❌ %%D folder missing
        set "FOLDERS_MISSING=1"
    ) else (
        echo ✓ %%D folder exists
    )
)
if !FOLDERS_MISSING!==1 set "ALL_GOOD=0"
echo.

echo =============================================================
echo                   REQUIREMENTS SUMMARY
echo =============================================================
echo.
if !ALL_GOOD!==0 (
    color 0E
    echo ⚠️  Some requirements are missing or incomplete.
    echo Please review the list above and run Option 1 (Install).
) else (
    color 0A
    echo ✓ All requirements met successfully!
    echo You can now start the bot with Option 2.
)
goto RETURN_TO_MENU

:LOGS
cls
echo.
echo =============================================================
echo                 Opening Logs Folder...
echo =============================================================
echo.
if not exist "logs" (
    echo Creating logs folder...
    mkdir "logs" >nul 2>&1
)

if exist "logs" (
    start explorer.exe "logs"
    echo Logs folder opened successfully.
) else (
    color 0C
    echo [ERROR] Could not create or access logs folder!
)
goto RETURN_TO_MENU

:HELP
cls
echo.
echo =============================================================
echo               🏰 RISE OF KINGDOMS BOT - HELP
echo =============================================================
echo.

set "HELP_SECTION=FIRST TIME SETUP"
echo !HELP_SECTION!
echo ----------------
echo 1. Ensure BlueStacks is installed.
echo 2. Install Rise of Kingdoms in BlueStacks.
echo 3. Run this launcher and select Option 1 (Install).
echo 4. After installation, select Option 2 (Start Bot).
echo.

set "HELP_SECTION=BEFORE STARTING BOT"
echo !HELP_SECTION!
echo -------------------
echo 1. Open BlueStacks and start Rise of Kingdoms.
echo 2. Go to BlueStacks Settings → Advanced.
echo 3. Enable "Android Debug Bridge (ADB)".
echo 4. Restart BlueStacks if needed.
echo.

set "HELP_SECTION=USING THE BOT"
echo !HELP_SECTION!
echo -----------------
echo 1. Launch bot with Option 2.
echo 2. Click "Refresh Devices" in the GUI.
echo 3. Select your BlueStacks device.
echo 4. Click "Connect".
echo 5. Configure tasks on the left panel.
echo 6. Watch logs on the right panel.
echo 7. Click the big green "START" button.
echo.

set "HELP_SECTION=NEW FEATURES IN v1.1"
echo !HELP_SECTION!
echo --------------------
echo ✓ No more GUI freezing
echo ✓ Bigger, clearer buttons
echo ✓ Side-by-side tasks and logs
echo ✓ New Player Tutorial automation
echo ✓ Explore Fog and Gather Gems features
echo ✓ Target level tracking for buildings
echo.

set "HELP_SECTION=TROUBLESHOOTING"
echo !HELP_SECTION!
echo ----------------
echo Problem: Python not found
echo Solution: Install Python from python.org and
echo           check "Add Python to PATH" during setup.
echo.
echo Problem: No devices found
echo Solution: Enable ADB in BlueStacks settings and restart.
echo.
echo Problem: Bot won't start
echo Solution: Run Option 3 (Check Requirements) and
echo           ensure all items show ✓.
echo.

set "HELP_SECTION=SUPPORT"
echo !HELP_SECTION!
echo --------
echo - Check the 'logs' folder for error details.
echo - Read README.md for complete documentation.
echo - Contact the developer with error logs or screenshots.
echo.

echo =============================================================
goto RETURN_TO_MENU

:RETURN_TO_MENU
echo.
echo Press any key to return to the main menu...
pause >nul
goto MENU

:EXIT
cls
echo.
echo =============================================================
echo     Thank you for using Rise of Kingdoms Bot! 🤖
echo =============================================================
echo.
timeout /t 2 >nul
exit /b 0
