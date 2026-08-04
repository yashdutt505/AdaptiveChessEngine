@echo off
setlocal
set "ACE_COMPILER=g++"
where "%ACE_COMPILER%" >nul 2>nul
if errorlevel 1 (
    if exist "C:\MinGW\bin\g++.exe" (
        set "ACE_COMPILER=C:\MinGW\bin\g++.exe"
    ) else (
        echo No C++ compiler was found. Install a modern GCC, Clang, or Visual Studio C++ toolchain. 1>&2
        exit /b 1
    )
)

"%ACE_COMPILER%" -std=c++17 -O3 -DNDEBUG -Wall -Wextra -pedantic -I"%~dp0cpp\include" "%~dp0cpp\src\main.cpp" -o "%~dp0cpp\adaptive_chess_engine.exe"
if errorlevel 1 exit /b 1
echo Built %~dp0cpp\adaptive_chess_engine.exe
