# Prospective Blinded Human Experiment Protocol

## Confirmatory question

Against YashDutt7, does the frozen lifetime-personal selector produce a higher
engine game score than the compute-identical neutral rank-one selector?

This is the primary hypothesis. Population and deterministic random-safe arms
test whether any effect comes from general human-error knowledge,
player-specific information, or merely changing moves.

## Frozen engine policy

- Engine commit: the commit containing this protocol and final frozen policy.
- Candidates: MultiPV 8, complete all-root search.
- Compute: 5,000 target nodes per engine move in every arm.
- Objective loss bound: 35 cp.
- Learned conversion: 400 cp per unit probability difference, capped at 35 cp.
- Personal model: lifetime histogram gradient boosting trained before the match.
- Population model: same model class trained on the population sample.
- Random control: deterministic hash adjustment in the same -35 to +35 cp range.
- No model, feature, bonus, opening, or stopping-rule updates during the study.

The 5,000-node level was selected before human outcomes. It scored 8/16 against
Stockfish limited to 1164 in calibration and 20/32 in confirmation, or 28/48
combined (58.3%). This corresponds to approximately 1223 on that local protocol,
with substantial uncertainty. It is not a Chess.com rating equivalence.

## Blinding and randomization

The GUI connects only to `run_blinded_experiment.bat`. The proxy consumes the
next hidden schedule entry, forces all protected UCI options, replaces every GUI
time command with `go nodes 5000`, and removes adaptive-profile explanation
lines. The user sees only an opaque session code.

The schedule has one excluded eight-game pilot block followed by twenty
confirmatory eight-game blocks. Within every block, each of the four arms occurs
once with Yash as White and once with Yash as Black. One fixed four-ply opening
is shared across all eight games in a block. Assignment order is randomized.
The private schedule is Git-ignored; its SHA-256 commitment and public session
instructions are versioned before play begins.

The active pre-pilot private-schedule commitment is
`c4561ecd32237ea09e90ba75447cc144847e0ceceba070b66328d7df1094f703`.

## Pilot

The first eight games test only GUI operation, session logging, color/opening
instructions, legal play, and blinding. Pilot outcomes are excluded from every
confirmatory analysis. Any protocol or software change after the pilot requires
a new private schedule, new commitment, and a fresh confirmatory start.

## Confirmatory sample and endpoint

The confirmatory sample is fixed at 160 games: 40 per arm, 20 as each color.
There is no efficacy stopping. A safety failure, corrupted schedule, revealed
arm, illegal engine move, or reproducible software defect pauses the experiment;
the affected game is documented before deciding whether it is replayed.

The primary outcome is engine game score, coded win 1, draw 0.5, loss 0. The
primary contrast is personal minus neutral, estimated across the twenty blocked
opening/color sets with a 95% block-bootstrap interval and an exact blocked
randomization test. All games and all arms are reported regardless of result.

Secondary contrasts are personal minus population, population minus neutral,
and personal minus random. These are interpreted as secondary and are not used
to replace an unfavorable primary result.

## Mechanism outcomes

After the schedule is locked and games are complete, every Yash decision that
immediately follows an engine move is labelled by the fixed 100,000-node
reference process. Secondary outcomes are mean centipawn loss, errors of at
least 50, 100, and 200 cp, calibration of predicted 100-cp error probability,
and outcomes restricted to turns where an adaptive arm would differ from the
neutral move.

Decision-level observations do not replace the game-level primary endpoint.
They test the proposed mechanism: selected positions should increase Yash's
error rate, which should in turn improve engine score.

## Interpretation rules

- A positive primary estimate with an interval excluding zero supports the
  main hypothesis for this player, engine version, time control, and protocol.
- An interval overlapping zero is inconclusive, not proof of no effect.
- A precise estimate near zero would argue that predictive personalization does
  not translate into match advantage under these constraints.
- Better error prediction without better match score supports the narrower
  conclusion that prediction is easier than causal exploitation.
- Results do not automatically generalize to other players or time controls.
