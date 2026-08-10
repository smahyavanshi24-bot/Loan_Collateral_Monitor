@echo off

cd /d C:\Users\Acer\Loan_Collateral_Monitor

chcp 65001 > nul

set PYTHONIOENCODING=utf-8

python main.py >> logs\scheduled_run.log 2>&1