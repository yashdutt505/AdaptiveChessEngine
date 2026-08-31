# Position-Characteristic Features

The adaptive layer measures every completed MultiPV root candidate after making
that move. Features are deterministic integers, independent of any opponent
profile, and expressed from the root mover's point of view where a balance is
involved. Extraction restores the original position before returning.

| Field | Unit | Meaning |
|---|---:|---|
| `capture_value_cp` | cp | Value removed by the candidate |
| `promotion_gain_cp` | cp | Promoted-piece value minus pawn value |
| `gives_check` | 0/1 | Candidate checks the opponent king |
| `legal_reply_count` | moves | Opponent choices after the candidate |
| `material_balance_cp` | cp | Mover material minus opponent material |
| `material_imbalance_cp` | cp | Absolute material balance |
| `remaining_non_pawn_material_cp` | cp | Combined non-pawn, non-king material |
| `remaining_pawn_count` | pawns | Pawns left for both sides |
| `open_file_count` | files | Files containing no pawns |
| `mobility_balance` | eval units | Existing mobility measure difference |
| `king_safety_balance` | eval units | Existing king-safety measure difference |
| `pawn_structure_balance` | eval units | Existing pawn-structure measure difference |
| `center_control_balance` | squares | Difference in attacked d4/e4/d5/e5 squares |
| `pawn_tension_count` | contacts | White-black pawn capture contacts |
| `irreversible` | 0/1 | Pawn move, capture, or promotion |
| `castles` | 0/1 | Candidate castles |

These are measurements, not preferences. No weights or opponent assumptions
belong in the extractor. The versioned profile schema in roadmap step 4 will
define how a profile can value them, and the bounded selector in step 6 will
apply those values only to candidates admitted by the safety contract.
