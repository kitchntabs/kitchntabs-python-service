@echo off
setlocal

REM Try to find python311.dll from common locations
set DLLPATH=
REM Try Python from PATH
for /f "delims=" %%P in ('where python') do (
    if exist "%%~dpPpython311.dll" (
        set DLLPATH=%%~dpPpython311.dll
        goto :found
    )
)
REM Try user install location
if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python311.dll" (
    set DLLPATH=%USERPROFILE%\AppData\Local\Programs\Python\Python311\python311.dll
    goto :found
)
REM Try Program Files
if exist "C:\Program Files\Python311\python311.dll" (
    set DLLPATH=C:\Program Files\Python311\python311.dll
    goto :found
)

:found
if not defined DLLPATH (
    echo python311.dll not found.
    exit /b 1
)
REM Ensure destination folder exists
if not exist ".\service\_internal" (
    mkdir ".\service\_internal"
)
echo Copying %DLLPATH% to .\service\_internal\python311.dll
copy /Y "%DLLPATH%" ".\service\_internal\python311.dll"
echo Done.
endlocal