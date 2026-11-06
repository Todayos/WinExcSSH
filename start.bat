@echo off
setlocal
cd /d "%~dp0"
uv run --locked python start.py
set "SSH_SERVICE_RUNNER_EXIT_CODE=%ERRORLEVEL%"
if not "%SSH_SERVICE_RUNNER_EXIT_CODE%"=="0" (
    echo.
    echo Startup failed. Check uv installation, local configuration, and the error above.
)
pause
exit /b %SSH_SERVICE_RUNNER_EXIT_CODE%
