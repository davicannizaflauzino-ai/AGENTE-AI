@echo off
title JARVIS AI Chatbot
cd /d %~dp0
echo ================================
echo     JARVIS AI CHATBOT
echo ================================
echo.
set PYTHON_CMD=
for /f "delims=" %%i in ('dir /b "%LOCALAPPDATA%\Python\pythoncore-*\python.exe" 2^>nul') do set PYTHON_CMD=%LOCALAPPDATA%\Python\%%i
if "%PYTHON_CMD%"=="" if exist "%LOCALAPPDATA%\Python\bin\python.exe" set PYTHON_CMD=%LOCALAPPDATA%\Python\bin\python.exe
if "%PYTHON_CMD%"=="" set PYTHON_CMD=python
echo [*] Usando: %PYTHON_CMD%
echo.
echo [*] Iniciando JARVIS...
"%PYTHON_CMD%" main.py
if errorlevel 1 (
  echo [ERRO] O programa fechou inesperadamente.
  pause
)