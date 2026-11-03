@echo off
setlocal
echo Rendering native Qt menus: panel/ring, light/dark.
echo Output: "%~dp0output\menu-concepts\native-current"
if not exist "%~dp0.build-envs\qt6-cp313\Scripts\python.exe" (
    echo ERROR: Project Qt6 Python was not found.
    pause
    exit /b 1
)
"%~dp0.build-envs\qt6-cp313\Scripts\python.exe" "%~dp0scripts\render_native_menus.py" --output "%~dp0output\menu-concepts\native-current" --theme both --lang ru --force
set "capture_result=%errorlevel%"
if "%capture_result%"=="0" (
    echo Done. Four native menu PNGs are in the output folder above.
) else (
    echo ERROR: Native menu capture failed. Exit code: %capture_result%
)
pause
exit /b %capture_result%
