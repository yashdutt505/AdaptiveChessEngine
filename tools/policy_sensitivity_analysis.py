"""Validation-only calibration and diagnostics for learned root selection."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.fen import load_fen, position_to_fen  # noqa: E402
from engine.move import move_to_string  # noqa: E402
from engine.movegen import generate_legal_moves  # noqa: E402
from engine.opponent_model_features import MODEL_FEATURE_NAMES, extract_position_features  # noqa: E402
from engine.position import Position  # noqa: E402
from tools.compare_adaptive_policies import Engine, position_suite  # noqa: E402


SCALES = (50, 100, 200, 400)
CAPS = (10, 20, 35)
CANDIDATE_COUNTS = (4, 8)
LOSS_BOUND_CP = 35
TARGET_CHANGE_LOW = 0.10
TARGET_CHANGE_HIGH = 0.25


def resulting_features(fen: str, move_text: str, target_rating: int, engine_rating: int) -> list[float]:
    position = Position();load_fen(position, fen)
    matches = [move for move in generate_legal_moves(position) if move_to_string(move) == move_text]
    if len(matches) != 1:
        raise ValueError(f"expected one legal move {move_text}")
    position.make_move(matches[0])
    values = extract_position_features(position_to_fen(position), target_rating, engine_rating)
    return [float(values[name]) for name in MODEL_FEATURE_NAMES]


def select(scores: np.ndarray, probabilities: np.ndarray, scale: int, cap: int, count: int) -> tuple[int, int]:
    best_score = int(scores[0]);best_adjusted = best_score;selected = 0;selected_bonus = 0
    for index in range(1, min(count, len(scores))):
        if best_score - int(scores[index]) > LOSS_BOUND_CP:
            continue
        bonus = int(np.rint((probabilities[index] - probabilities[0]) * scale))
        bonus = max(-cap, min(cap, bonus));adjusted = int(scores[index]) + bonus
        if adjusted > best_adjusted:
            best_adjusted = adjusted;selected = index;selected_bonus = bonus
    return selected, selected_bonus


def evaluate_config(records: list[dict], probability_key: str, scale: int, cap: int, count: int) -> dict:
    changes = 0;losses=[];lifts=[];changed_lifts=[];bonuses=[];indices=[]
    for record in records:
        scores=np.asarray(record["scores"]);probabilities=np.asarray(record[probability_key])
        index,bonus=select(scores,probabilities,scale,cap,count);indices.append(index)
        loss=int(scores[0]-scores[index]);lift=float(probabilities[index]-probabilities[0])
        changes += index != 0;losses.append(loss);lifts.append(lift);bonuses.append(bonus)
        if index != 0:changed_lifts.append(lift)
    return {
        "scale_cp_per_probability":scale,"maximum_bonus_cp":cap,"candidate_count":count,
        "changed_moves":changes,"change_rate":changes/len(records),
        "mean_score_loss_cp":float(np.mean(losses)),"maximum_score_loss_cp":max(losses),
        "mean_probability_lift_all_positions":float(np.mean(lifts)),
        "mean_probability_lift_changed_positions":float(np.mean(changed_lifts)) if changed_lifts else 0.0,
        "mean_applied_bonus_cp":float(np.mean(bonuses)),"selected_indices":indices,
    }


def choose_configuration(configurations: list[dict]) -> tuple[dict, str]:
    eligible=[item for item in configurations if TARGET_CHANGE_LOW <= item["change_rate"] <= TARGET_CHANGE_HIGH]
    if eligible:
        selected=max(eligible,key=lambda item:(item["mean_probability_lift_all_positions"],-item["mean_score_loss_cp"],-item["maximum_bonus_cp"],-item["candidate_count"],-item["scale_cp_per_probability"]))
        return selected,"maximum mean personal-probability lift among policies changing 10-25% of validation positions"
    selected=min(configurations,key=lambda item:(abs(item["change_rate"]-.175),item["mean_score_loss_cp"],item["maximum_bonus_cp"],item["candidate_count"],item["scale_cp_per_probability"]))
    return selected,"fallback closest to the midpoint of the preregistered 10-25% intervention range"


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--engine",type=Path,required=True);parser.add_argument("--positions",type=Path,required=True)
    parser.add_argument("--personal-rows",type=Path,required=True);parser.add_argument("--population-model",type=Path,required=True)
    parser.add_argument("--personal-model",type=Path,required=True);parser.add_argument("--recent-model",type=Path,required=True)
    parser.add_argument("--decayed-model",type=Path,required=True);parser.add_argument("--count",type=int,default=256)
    parser.add_argument("--nodes",type=int,default=20_000);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()

    suite=position_suite(args.positions,args.count,"validation")
    engine=Engine(args.engine,None,max(CANDIDATE_COUNTS));records=[]
    try:
        for number,row in enumerate(suite,1):
            analysis=engine.analyze(row["fen_before"],row.get("opponent_rating") or 0,row.get("player_rating") or 0,args.nodes)
            if len(analysis["candidates"]) < max(CANDIDATE_COUNTS):
                continue
            moves=[move for move,_ in analysis["candidates"]];scores=[score for _,score in analysis["candidates"]]
            matrix=np.asarray([resulting_features(row["fen_before"],move,row.get("opponent_rating") or 0,row.get("player_rating") or 0) for move in moves])
            records.append({"moves":moves,"scores":scores,"features":matrix.tolist()})
            print(f"candidate corpus {number}/{len(suite)}",flush=True)
    finally:engine.close()
    models={
        "population":joblib.load(args.population_model),"personal":joblib.load(args.personal_model),
        "recent":joblib.load(args.recent_model),"decayed":joblib.load(args.decayed_model),
    }
    for record in records:
        matrix=np.asarray(record["features"])
        for name,model in models.items():record[f"{name}_probabilities"]=model.predict_proba(matrix)[:,1].tolist()

    configurations=[evaluate_config(records,"personal_probabilities",scale,cap,count) for scale in SCALES for cap in CAPS for count in CANDIDATE_COUNTS]
    selected,rule=choose_configuration(configurations)
    selected_indices=selected["selected_indices"]
    comparison={}
    for name in ("population","recent","decayed"):
        other=evaluate_config(records,f"{name}_probabilities",selected["scale_cp_per_probability"],selected["maximum_bonus_cp"],selected["candidate_count"])
        comparison[name]={key:value for key,value in other.items() if key!="selected_indices"}
        comparison[name]["move_agreement_with_lifetime_personal"]=float(np.mean(np.asarray(other["selected_indices"])==np.asarray(selected_indices)))

    all_features=np.asarray([candidate for record in records for candidate in record["features"]])
    training=[json.loads(line) for line in args.personal_rows.read_text(encoding="utf-8").splitlines() if line.strip()]
    training=np.asarray([[row["features"][name] for name in MODEL_FEATURE_NAMES] for row in training if row["split"] in ("train","validation")],dtype=float)
    below=all_features<training.min(axis=0);above=all_features>training.max(axis=0)
    ood_by_feature={name:int((below[:,index]|above[:,index]).sum()) for index,name in enumerate(MODEL_FEATURE_NAMES)}
    personal=np.asarray([record["personal_probabilities"] for record in records]);population=np.asarray([record["population_probabilities"] for record in records])
    within_ranges=personal.max(axis=1)-personal.min(axis=1)
    report={
        "experiment":"validation_only_policy_sensitivity_v1","selection_data_boundary":"chronological validation games only",
        "positions_requested":args.count,"positions_analyzed":len(records),"nodes_per_position":args.nodes,"loss_bound_cp":LOSS_BOUND_CP,
        "candidate_counts":list(CANDIDATE_COUNTS),"probability_scales":list(SCALES),"maximum_bonuses_cp":list(CAPS),
        "selection_rule":rule,"selected_configuration":{key:value for key,value in selected.items() if key!="selected_indices"},
        "all_configurations":[{key:value for key,value in item.items() if key!="selected_indices"} for item in configurations],
        "selected_policy_model_comparison":comparison,
        "candidate_discrimination":{
            "mean_personal_probability_range":float(within_ranges.mean()),"median_personal_probability_range":float(np.median(within_ranges)),
            "positions_with_range_below_0_01":int((within_ranges<.01).sum()),
            "population_personal_probability_correlation":float(np.corrcoef(personal.ravel(),population.ravel())[0,1]),
            "highest_probability_candidate_disagreement_rate":float(np.mean(personal.argmax(axis=1)!=population.argmax(axis=1))),
        },
        "out_of_distribution":{
            "candidate_rows":len(all_features),"rows_outside_any_historical_range":int((below|above).any(axis=1).sum()),
            "rate_outside_any_historical_range":float((below|above).any(axis=1).mean()),"counts_by_feature":ood_by_feature,
        },
        "selected_rank_counts":dict(Counter(str(index+1) for index in selected_indices)),
    }
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":main()
