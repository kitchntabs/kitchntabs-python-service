@echo off
REM Directly use the venv python, no need to activate
pyinstaller ./src/kt_service.py --onefile --distpath ./kt_service --add-data ./config.kitchntabs.prod.yaml:. --add-data pw_env/Lib/site-packages/escpos/*.json:escpos --collect-data escpos --noconfirm