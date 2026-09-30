# LinkedIn Post Draft Adaptive Chess Research Update

I have reached an important boundary in my Adaptive Chess Engine project: the
opponent model is now running inside the C++ engine, but I still do not have
evidence that it wins more games against the person it models.

That distinction has shaped the latest work.

I trained models on my historical Chess.com games to predict whether I would
lose at least 100 centipawns on my next decision. On chronologically later
games, personalized gradient boosting predicted my errors better than the same
model trained on a population sample. The personal model reached 0.3935 log
loss versus 0.4000 for the population model, with a game-level bootstrap
interval supporting the predictive improvement.

But better prediction is not the same as causal exploitation.

The model has now been exported into the C++ root selector with exact
Python-to-C++ probability parity. Every arm receives the same searched
candidates. The adaptive policy can only choose within a 35-centipawn safety
boundary, and mate protection remains absolute.

I then used only chronological validation positions to select the final
probability-to-score policy. Across 231 usable positions, the selected policy
changed 23 moves, increased predicted error probability by about 5 percentage
points when it intervened, and sacrificed only 0.68 centipawns on average over
all positions. On a separate 64-position replay, the personal selector changed
5 moves, with zero candidate mismatches between experimental arms.

The most interesting diagnostic was not a win rate: population and personal
models disagreed on the highest-risk candidate in 64% of validation positions.
So personalization is changing the ranking in a real way. Whether those
rankings actually cause more mistakes remains unproven.

Small safety matches against limited-strength Stockfish were statistically
inconclusive. I am preserving that negative result rather than presenting the
personal arm's higher point estimate as a success.

The next experiment is now preregistered: a blinded, blocked N-of-1 study with
neutral, population, personal, and deterministic random-control arms. The
engine receives identical fixed-node compute in every arm, and the active arm
is hidden by a UCI proxy. An eight-game pilot is excluded from analysis,
followed by a planned 160 confirmatory games.

The research question is finally narrow and falsifiable:

Can historical information about one recurring player improve an engine's game
score against that player when search, candidates, openings, colors, and
hardware are held constant?

The answer may be yes, no, or still too uncertain. Any of those outcomes is
useful if the experiment is honest.

#MachineLearning #ChessProgramming #ArtificialIntelligence #CPlusPlus
#DataScience #Research #ExplainableAI
