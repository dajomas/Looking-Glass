@echo off
setlocal
cd /d "%~dp0"
if defined LG_PYTHON (
  "%LG_PYTHON%" python\launcher.py %*
  exit /b
)
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" python\launcher.py %*
  exit /b
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 python\launcher.py %*
  exit /b
)
where python >nul 2>nul
if not errorlevel 1 (
  python python\launcher.py %*
  exit /b
)
echo Python 3.12+ is required. Install Python or set LG_PYTHON. 1>&2
exit /b 1
