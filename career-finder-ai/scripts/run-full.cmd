@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0run-full.ps1"
exit /b %ERRORLEVEL%
