@echo off
setlocal
set "ACE_ROOT=%~dp0"
"%ACE_ROOT%.venv\Scripts\python.exe" "%ACE_ROOT%tools\blinded_uci_proxy.py" --engine "%ACE_ROOT%cpp\adaptive_chess_engine.exe" --schedule "%ACE_ROOT%experiments\private\blinded_match_schedule.json" --commitment "%ACE_ROOT%experiments\blinded_match_commitment.json" --state "%ACE_ROOT%experiments\blinded_match_state.json" --log "%ACE_ROOT%experiments\blinded_match_run_log.jsonl"
