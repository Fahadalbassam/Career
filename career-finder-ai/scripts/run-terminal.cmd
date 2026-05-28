@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0run-terminal.ps1"
exit /b %ERRORLEVEL%
