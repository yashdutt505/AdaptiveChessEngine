"""Show the next public blinded-match instruction without reading arm identity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("--commitment",type=Path,required=True)
    parser.add_argument("--state",type=Path,required=True);args=parser.parse_args()
    public=json.loads(args.commitment.read_text(encoding="utf-8"));index=0
    if args.state.exists():index=int(json.loads(args.state.read_text(encoding="utf-8"))["next_index"])
    if index>=len(public["sessions"]):print("schedule complete");return
    item=public["sessions"][index]
    print(json.dumps({"next_schedule_index":index,**item},indent=2))


if __name__=="__main__":main()
