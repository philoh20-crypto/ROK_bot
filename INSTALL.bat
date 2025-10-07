@echo off
REM ============================================================
REM  Rise of Kingdoms Bot - Easy Installation Script
REM  This script installs all required dependencies automatically.
REM ============================================================

color 0A
title Rise of Kingdoms Bot - Installation

echo.
echo ============================================================
echo        Rise of Kingdoms Bot - Installation
echo ============================================================
echo.

REM ------------------------------------------------------------
REM STEP 1: Check if Python is installed
REM ------------------------------------------------------------
echo [STEP 1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, check the box that says:
    echo   "Add Python to PATH"
    echo.
    echo After installing Python, run this script again.
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] Python detected: %PY_VER%
echo.

REM ------------------------------------------------------------
REM STEP 2: Upgrade pip to the latest version
REM ------------------------------------------------------------
echo [STEP 2/4] Upgrading pip package manager...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [WARNING] Could not upgrade pip, continuing with existing version...
) else (
    echo [OK] Pip upgraded successfully.
)
echo.

REM ------------------------------------------------------------
REM STEP 3: Install Python dependencies
REM ------------------------------------------------------------
echo [STEP 3/4] Installing bot dependencies...
echo This may take several minutes depending on your internet speed.
echo Please be patient and do not close this window.
echo.

if exist requirements.txt (
    pip install -r requirements.txt --upgrade
) else (
    color 0C
    echo [ERROR] Missing 'requirements.txt' file!
    echo Please ensure it exists in the current directory.
    pause
    exit /b 1
)

if errorlevel 1 (
    color 0C
    echo.
    echo [ERROR] Dependency installation failed!
    echo.
    echo Common issues and solutions:
    echo - No internet connection: Check your network
    echo - Antivirus blocking downloads: Temporarily disable antivirus
    echo - Insufficient permissions: Run as Administrator
    echo - Corrupted pip cache: Run "pip cache purge" and try again
    echo.
    echo Try running this script as Administrator if issues persist.
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] All Python dependencies installed successfully!
echo.

REM ------------------------------------------------------------
REM STEP 4: Create necessary directories
REM ------------------------------------------------------------
echo [STEP 4/4] Creating necessary directories...
set DIRS=templates logs screenshots

for %%D in (%DIRS%) do (
    if not exist "%%D" (
        mkdir "%%D"
        echo [OK] Created %%D directory
    )
)
echo.

REM ------------------------------------------------------------
REM Create README inside templates directory
REM ------------------------------------------------------------
if not exist "templates\README.txt" (
    (
        echo Template images will be placed in this directory.
        echo These are UI element images that the bot uses to recognize game elements.
        echo.
        echo Required templates:
        echo - map_button.png
        echo - gather_button.png
        echo - barracks.png
        echo - and other game UI elements...
    ) > "templates\README.txt"
    echo [OK] Created templates\README.txt
)
echo.

REM ------------------------------------------------------------
REM Completion message
REM ------------------------------------------------------------
color 0A
echo ============================================================
echo   Installation Complete Successfully!
echo ============================================================
echo.
echo ✓ Python runtime verified and working
echo ✓ All Python dependencies installed
echo ✓ Required directories created
echo ✓ Installation completed successfully
echo.
echo ============================================================
echo   NEXT STEPS FOR SETUP:
echo ============================================================
echo.
echo 1. Ensure BlueStacks is installed and running.
echo 2. Install Rise of Kingdoms inside BlueStacks.
echo 3. Enable ADB Debugging in BlueStacks:
echo    - Open BlueStacks Settings (gear icon)
echo    - Go to the Advanced tab
echo    - Enable "Android Debug Bridge (ADB)"
echo    - Restart BlueStacks after enabling.
echo.
echo 4. Double-click START_BOT.bat to launch the bot.
echo 5. Follow on-screen instructions in the GUI.
echo.
echo ============================================================
echo   TROUBLESHOOTING:
echo ============================================================
echo.
echo If the bot doesn't start:
echo - Ensure BlueStacks is running before starting the bot.
echo - Run START_BOT.bat as Administrator.
echo - Verify ADB is enabled in BlueStacks settings.
echo - Confirm Rise of Kingdoms is installed in BlueStacks.
echo.
echo ============================================================
echo.
echo Press any key to exit this installation...
pause >nul
