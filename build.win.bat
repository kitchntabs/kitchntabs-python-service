@echo off
REM Windows Build Script for KitchenTabs Python Services
REM Builds all 3 services: kt_service, print_service, tts_service
REM
REM Prerequisites:
REM   - Python 3.9 installed
REM   - Virtual environment created: python -m venv pw_env
REM   - Dependencies installed: pw_env\Scripts\pip install -r requirements.txt
REM   - PyInstaller installed: pw_env\Scripts\pip install pyinstaller
REM
REM Usage: build.win.bat [config_file]
REM   config_file: Optional config file (default: config.kitchntabs.prod.yaml)

SETLOCAL EnableDelayedExpansion

echo.
echo ========================================
echo  KitchenTabs Python Service Builder
echo  Windows Build Script
echo ========================================
echo.

REM Set config file (default or from argument)
SET CONFIG_FILE=%1
IF "%CONFIG_FILE%"=="" SET CONFIG_FILE=config.kitchntabs.prod.yaml

echo Configuration: %CONFIG_FILE%
echo.

REM Check if config file exists
IF NOT EXIST "%CONFIG_FILE%" (
    echo ERROR: Config file not found: %CONFIG_FILE%
    echo Available config files:
    dir /b config.*.yaml
    exit /b 1
)

REM Copy config file to config.yaml for bundling
echo Copying %CONFIG_FILE% to config.yaml...
copy /Y "%CONFIG_FILE%" config.yaml >nul

REM Set Python executable path
SET PYTHON_EXE=pw_env\Scripts\python.exe
SET PYINSTALLER=pw_env\Scripts\pyinstaller.exe

REM Check if virtual environment exists
IF NOT EXIST "%PYTHON_EXE%" (
    echo ERROR: Virtual environment not found at pw_env\
    echo Please create it first:
    echo   python -m venv pw_env
    echo   pw_env\Scripts\pip install -r requirements.txt
    echo   pw_env\Scripts\pip install pyinstaller
    exit /b 1
)

REM Clean previous builds
echo Cleaning previous builds...
IF EXIST "kt_service" rmdir /s /q kt_service
IF EXIST "build" rmdir /s /q build
IF EXIST "dist" rmdir /s /q dist

REM Create output directory
mkdir kt_service 2>nul

echo.
echo ----------------------------------------
echo Building kt_service (WebSocket Service)
echo ----------------------------------------
%PYINSTALLER% ./src/kt_service.py ^
    --onefile ^
    --distpath ./kt_service ^
    --add-data "config.yaml;." ^
    --add-data "pw_env/Lib/site-packages/escpos/*.json;escpos" ^
    --collect-data escpos ^
    --noconfirm ^
    --clean

IF ERRORLEVEL 1 (
    echo ERROR: kt_service build failed!
    exit /b 1
)
echo kt_service built successfully!

echo.
echo ----------------------------------------
echo Building print_service (Printing Service)
echo ----------------------------------------
%PYINSTALLER% ./src/print_service.py ^
    --onefile ^
    --distpath ./kt_service ^
    --add-data "config.yaml;." ^
    --add-data "pw_env/Lib/site-packages/escpos/*.json;escpos" ^
    --collect-data escpos ^
    --noconfirm ^
    --clean

IF ERRORLEVEL 1 (
    echo ERROR: print_service build failed!
    exit /b 1
)
echo print_service built successfully!

echo.
echo ----------------------------------------
echo Building tts_service (Text-to-Speech)
echo ----------------------------------------
%PYINSTALLER% ./src/tts_service.py ^
    --onefile ^
    --distpath ./kt_service ^
    --noconfirm ^
    --clean

IF ERRORLEVEL 1 (
    echo ERROR: tts_service build failed!
    exit /b 1
)
echo tts_service built successfully!

REM Clean up temporary config file
del config.yaml 2>nul

echo.
echo ========================================
echo  Build Complete!
echo ========================================
echo.
echo Output directory: kt_service\
echo.
echo Built executables:
dir /b kt_service\*.exe
echo.

ENDLOCAL