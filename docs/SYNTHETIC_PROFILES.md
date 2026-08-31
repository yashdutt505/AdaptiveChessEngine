# Synthetic Opponent Profiles

Synthetic profiles are controlled experimental policies, not claims about real
players. They provide deliberately different, reproducible feature weights so
the future root selector can be tested before PGN-derived modelling exists.

| Profile | Intended pressure |
|---|---|
| `synthetic-tactical-pressure-v1` | Checks, captures, fewer replies, open and imbalanced play |
| `synthetic-simplification-pressure-v1` | Exchanges, reduced material and tension, safe conversion |
| `synthetic-complexity-pressure-v1` | More pieces, choices, tension, imbalance and commitment |
| `synthetic-positional-restriction-v1` | Mobility, king safety, structure, center control and restricted replies |

Only explicitly relevant features receive nonzero weights. Their confidence is
`1000`; unused features have zero weight and confidence. All profiles declare
zero analyzed games and positions because they are hypotheses rather than
learned evidence.

The authoritative definitions live in `engine/synthetic_profiles.py`. Run
`tools/create_synthetic_profiles.py` from the repository root to regenerate the
checked-in JSON files. Tests require byte-independent semantic equality between
the generated definitions and stored artifacts.

These profiles do not affect play yet. Roadmap step 6 will add the bounded root
selector that consumes them, while the experiment contract continues to limit
eligible moves by objective score and mate safety.
