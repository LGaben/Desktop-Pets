@echo off
setlocal
echo Running isolated Qt menu journeys and screenshots at 100/150/200 percent.
echo The running pet application will not be stopped or changed.
"%~dp0.build-envs\qt6-cp313\Scripts\python.exe" "%~dp0scripts\menu_e2e.py"
set "e2e_result=%errorlevel%"
echo Menu E2E exit code: %e2e_result%
echo Reports: "%~dp0reports\verification"
pause
exit /b %e2e_result%
