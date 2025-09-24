@echo off
echo 🚀 启动TradingAgents-CN Web应用...
echo.

REM 激活虚拟环境
call nenv\Scripts\activate.bat

REM 启动Streamlit应用
python start_web.py

pause
