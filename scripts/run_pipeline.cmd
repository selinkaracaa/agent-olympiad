@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_pipeline.ps1" %*
exit /b %ERRORLEVEL%
