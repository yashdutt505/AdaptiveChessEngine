# Personal dataset drift report

The exact 10-minute corpus contains 1,166 usable games and 36,039 `YashDutt7`
decisions from 16 December 2022 through 27 June 2026. The committed summarizer
counts each game once rather than treating correlated decisions as games.

## Chronological regimes

| Split | Dates | Games | Decisions | Mean rating | Median rating | Rating range |
|---|---|---:|---:|---:|---:|---:|
| Train | 2022-12-16 to 2024-06-12 | 695 | 20,320 | 772.5 | 792 | 370-950 |
| Validation | 2024-06-13 to 2025-01-21 | 235 | 7,735 | 985.1 | 971 | 897-1,095 |
| Test | 2025-01-21 to 2026-06-27 | 236 | 7,984 | 1,186.1 | 1,201.5 | 1,056-1,296 |

The player improved by roughly 414 rating points between the train and test
means. There is no overlap between the train maximum (950) and the test minimum
(1,056). This is substantial covariate and likely behavioural drift.

## Consequences for claims

- A random decision or game split would leak later-strength behaviour into
  training and answer an easier, less realistic question. It must not be used
  for the primary result.
- The chronological test measures forward personalization under improvement,
  not stationary interpolation. Weak test performance may mean the historical
  profile is stale rather than that opponent modelling is impossible.
- Rating and rating difference are legitimate pre-move inputs, but they do not
  magically solve extrapolation. Tree models in particular cannot extrapolate a
  smooth rating trend beyond their fitted thresholds.
- Learning curves and recent-window sensitivity analyses are required. These
  are secondary analyses; the untouched chronological test remains primary.
- Any future engine-vs-human experiment needs a recent update window before the
  profile is frozen, matching the actual deployment information boundary.

Other corpus facts: 596 games as White and 570 as Black; 621 wins, 60 draws,
and 485 losses; median 29 decisions per game. The raw summary remains under the
ignored personal-data directory.
