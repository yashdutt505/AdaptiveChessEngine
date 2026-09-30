"""UCI proxy that enforces the next hidden experimental arm and fixed nodes."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path


PROFILES={"neutral":None,"population":"population-error-v1","personal":"personal-yashdutt7-lifetime-v1","random":"random-safe-v1"}
HIDDEN_OPTIONS=("adaptive mode","adaptive profile","multipv","target rating","engine rating")


def reserve_session(schedule_path: Path,commitment_path: Path,state_path: Path,log_path: Path) -> tuple[dict,dict]:
    private_bytes=schedule_path.read_bytes();commitment=json.loads(commitment_path.read_text(encoding="utf-8"))
    actual=hashlib.sha256(private_bytes).hexdigest()
    if actual!=commitment["private_schedule_sha256"]:raise RuntimeError("private schedule does not match public commitment")
    schedule=json.loads(private_bytes);state={"next_index":0}
    if state_path.exists():state=json.loads(state_path.read_text(encoding="utf-8"))
    index=int(state["next_index"])
    if index>=len(schedule["sessions"]):raise RuntimeError("blinded schedule is complete")
    session=schedule["sessions"][index];state["next_index"]=index+1
    state_path.parent.mkdir(parents=True,exist_ok=True);state_path.write_text(json.dumps(state,indent=2)+"\n",encoding="utf-8")
    with log_path.open("a",encoding="utf-8") as handle:
        handle.write(json.dumps({"event":"reserved","timestamp_utc":datetime.now(timezone.utc).isoformat(),"index":index,"code":session["code"]})+"\n")
    return schedule,session


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("--engine",type=Path,required=True)
    parser.add_argument("--schedule",type=Path,required=True);parser.add_argument("--commitment",type=Path,required=True)
    parser.add_argument("--state",type=Path,required=True)
    parser.add_argument("--log",type=Path,required=True);args=parser.parse_args()
    schedule,session=reserve_session(args.schedule,args.commitment,args.state,args.log)
    child=subprocess.Popen([str(args.engine.resolve())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    configured=threading.Event()
    def read_output():
        for raw in child.stdout:
            line=raw.rstrip("\r\n")
            if line=="uciok" and not configured.is_set():
                profile=PROFILES[session["arm"]]
                child.stdin.write(f"setoption name MultiPV value {schedule['multipv']}\n")
                child.stdin.write(f"setoption name Target Rating value {schedule['target_rating']}\n")
                child.stdin.write(f"setoption name Engine Rating value {schedule['engine_rating']}\n")
                child.stdin.write(f"setoption name Adaptive Mode value {'false' if profile is None else 'true'}\n")
                if profile:child.stdin.write(f"setoption name Adaptive Profile value {profile}\n")
                child.stdin.flush();configured.set()
            if line.startswith("info string adaptive profile "):continue
            print(line,flush=True)
    reader=threading.Thread(target=read_output,daemon=True);reader.start()
    print(f"info string blinded session {session['code']} phase {session['phase']} game {session['game']}",flush=True)
    try:
        for raw in sys.stdin:
            line=raw.rstrip("\r\n");lower=line.lower()
            if lower.startswith("setoption name ") and any(f"name {name}" in lower for name in HIDDEN_OPTIONS):continue
            if lower=="go" or lower.startswith("go "):line=f"go nodes {schedule['engine_nodes']}"
            child.stdin.write(line+"\n");child.stdin.flush()
            if lower=="quit":break
    finally:
        try:child.wait(5)
        except subprocess.TimeoutExpired:child.kill()
        with args.log.open("a",encoding="utf-8") as handle:
            handle.write(json.dumps({"event":"process_closed","timestamp_utc":datetime.now(timezone.utc).isoformat(),"code":session["code"],"returncode":child.returncode})+"\n")


if __name__=="__main__":main()
