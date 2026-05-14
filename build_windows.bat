@echo off
setlocal enableextensions
echo ========================================================================
echo   RNV Icon Builder - Windows Build
echo ========================================================================
echo.

:: Verify the spec file is here before touching anything.
if not exist "RNV_Icon_Builder.spec" (
    echo [error] RNV_Icon_Builder.spec not found in current directory.
    echo Run this script from the project root.
    pause
    exit /b 1
)

:: Verify PyInstaller is installed.
where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo [error] pyinstaller not found on PATH.
    echo Install it with: pip install pyinstaller
    pause
    exit /b 1
)

:: ----------------------------------------------------------------------
:: 1. Clean __pycache__ and stale .pyc files so they don't get bundled.
:: ----------------------------------------------------------------------
echo [1/4] Cleaning Python cache...
for /d /r %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)
for /r %%f in (*.pyc *.pyo) do (
    if exist "%%f" del /q "%%f"
)

:: ----------------------------------------------------------------------
:: 2. Clean previous PyInstaller outputs so the new build is clean.
:: ----------------------------------------------------------------------
echo [2/4] Removing previous build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"

:: ----------------------------------------------------------------------
:: 3. Run PyInstaller using the project's .spec file.
:: ----------------------------------------------------------------------
echo [3/4] Running PyInstaller...
echo.
pyinstaller --clean --noconfirm RNV_Icon_Builder.spec
if errorlevel 1 (
    echo.
    echo [error] PyInstaller failed. See output above.
    pause
    exit /b 1
)

:: ----------------------------------------------------------------------
:: 4. Verify the exe exists and report its size.
:: ----------------------------------------------------------------------
echo.
echo [4/4] Verifying build output...
set "EXE_PATH=dist\RNV_Icon_Builder.exe"
if not exist "%EXE_PATH%" (
    echo [error] Build completed but %EXE_PATH% was not created.
    echo Check RNV_Icon_Builder.spec for the configured output name.
    pause
    exit /b 1
)

for %%A in ("%EXE_PATH%") do set "EXE_SIZE=%%~zA"
set /a "EXE_MB=%EXE_SIZE% / 1048576"

echo.
echo ========================================================================
echo   Build succeeded
echo ========================================================================
echo   Output:  %EXE_PATH%
echo   Size:    %EXE_MB% MB  (%EXE_SIZE% bytes)
echo ========================================================================
echo.
pause
endlocal
