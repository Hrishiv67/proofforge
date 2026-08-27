@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
set PYTHONPATH=%CD%
python -m proofforge invent --seed 1 --generations 45
echo.
echo Independently re-verifying the certificate...
python -m proofforge verify
pause
