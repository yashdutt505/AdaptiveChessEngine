@echo off
set "ACE_ENGINE=%~dp0cpp\adaptive_chess_engine.exe"
if not exist "%ACE_ENGINE%" (
    echo The C++ engine has not been built. Run build_cpp_engine.bat first. 1>&2
    exit /b 1
)
"%ACE_ENGINE%"
