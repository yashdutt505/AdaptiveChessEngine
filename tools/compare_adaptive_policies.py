"""Replay one frozen position suite through all adaptive selector policies."""

from __future__ import annotations

import argparse
import json
import queue
import re
import subprocess
import threading
import time
from pathlib import Path


ARMS = {
    "neutral": None,
    "population": "population-error-v1",
    "personal": "personal-yashdutt7-lifetime-v1",
    "random": "random-safe-v1",
}
MULTIPV = re.compile(r"\bmultipv (\d+) score (?:cp|mate) (-?\d+).*\bpv ([a-h][1-8][a-h][1-8][qrbn]?)")


class Engine:
    def __init__(self, path: Path, profile: str | None):
        self.process = subprocess.Popen([str(path.resolve())], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.lines: queue.Queue[str] = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()
        self.send("uci");self.wait("uciok")
        self.option("Hash", "64");self.option("MultiPV", "4")
        if profile:
            self.option("Adaptive Mode", "true");self.option("Adaptive Profile", profile)
        self.send("isready");self.wait("readyok")

    def _reader(self):
        for line in self.process.stdout:self.lines.put(line.strip())

    def send(self, line: str):
        self.process.stdin.write(line + "\n");self.process.stdin.flush()

    def wait(self, prefix: str, timeout: float = 30.0):
        deadline=time.monotonic()+timeout;seen=[]
        while time.monotonic()<deadline:
            line=self.lines.get(timeout=max(.01,deadline-time.monotonic()));seen.append(line)
            if line.startswith(prefix):return line,seen
        raise TimeoutError(prefix)

    def option(self, name: str, value: str):self.send(f"setoption name {name} value {value}")

    def analyze(self, fen: str, target_rating: int, engine_rating: int, nodes: int) -> dict:
        self.send("ucinewgame");self.option("Target Rating", str(target_rating));self.option("Engine Rating", str(engine_rating))
        self.send(f"position fen {fen}");self.send(f"go nodes {nodes}")
        best, lines=self.wait("bestmove ")
        candidates={}
        selection=None
        for line in lines:
            match=MULTIPV.search(line)
            if match:candidates[int(match.group(1))]=(match.group(3),int(match.group(2)))
            if line.startswith("info string adaptive profile "):selection=line
        return {"bestmove":best.split()[1],"candidates":[candidates[key] for key in sorted(candidates)],"selection":selection}

    def close(self):
        if self.process.poll() is None:self.send("quit");self.process.wait(5)


def position_suite(path: Path, count: int) -> list[dict]:
    rows=[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows=[row for row in rows if row.get("split")=="test"]
    if len(rows)<count:raise ValueError("not enough test positions")
    indices=[round(index*(len(rows)-1)/(count-1)) for index in range(count)] if count>1 else [0]
    return [rows[index] for index in indices]


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--engine",type=Path,required=True);parser.add_argument("--positions",type=Path,required=True)
    parser.add_argument("--count",type=int,default=64);parser.add_argument("--nodes",type=int,default=20_000)
    parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    suite=position_suite(args.positions,args.count);results={arm:[] for arm in ARMS}
    for arm,profile in ARMS.items():
        engine=Engine(args.engine,profile)
        try:
            for index,row in enumerate(suite):
                results[arm].append(engine.analyze(row["fen_before"],row.get("opponent_rating") or 0,row.get("player_rating") or 0,args.nodes))
                print(f"{arm} {index+1}/{len(suite)}",flush=True)
        finally:engine.close()
    mismatches=[]
    for index in range(len(suite)):
        baseline=results["neutral"][index]["candidates"]
        for arm in ("population","personal","random"):
            if results[arm][index]["candidates"]!=baseline:mismatches.append({"position":index,"arm":arm})
    report={
        "experiment":"identical_candidate_policy_replay_v1","positions":len(suite),"nodes_per_position":args.nodes,
        "candidate_mismatches":mismatches,"arms":{},"position_source":str(args.positions),
    }
    for arm,records in results.items():
        changes=sum(record["bestmove"]!=results["neutral"][index]["bestmove"] for index,record in enumerate(records))
        losses=[]
        for index,record in enumerate(records):
            candidates=dict(results["neutral"][index]["candidates"])
            if record["bestmove"] in candidates:losses.append(candidates[results["neutral"][index]["bestmove"]]-candidates[record["bestmove"]])
        report["arms"][arm]={"changed_moves":changes,"change_rate":changes/len(records),
                              "mean_selected_score_loss_cp":sum(losses)/len(losses) if losses else None,
                              "maximum_selected_score_loss_cp":max(losses) if losses else None}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":main()
