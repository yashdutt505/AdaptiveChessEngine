# Adaptive Root Selector

The C++ selector reranks only candidates from a fully completed, all-root
MultiPV iteration. Neutral search scores remain authoritative eligibility gates.

1. Candidate zero is the neutral move.
2. Alternatives must be complete, must not allow a forced mate, and must be no
   more than 35 cp below the neutral score.
3. Each feature is measured relative to the neutral candidate and normalized by
   a fixed feature-specific scale, clamped to `[-1000, 1000]`.
4. Utility is the deterministic sum of normalized difference × profile weight ×
   confidence. Only a strictly positive improvement over neutral changes move.
5. Ties preserve neutral MultiPV order. Invalid profiles, incomplete searches,
   terminal positions, and mate-score neutral results fall back to neutral.

UCI adaptation is opt-in with `Adaptive Mode` (default `false`). `Adaptive
Profile` selects the neutral profile or one of the four versioned synthetic
profiles. Adaptive searches use at least four root candidates. Profile state is
copied into the search task, so option changes cannot mutate an active search.

This step selects moves but does not yet emit a full decision audit. Structured
candidate-by-candidate explanations are roadmap step 7.
