# Opponent Profile Schema v1

Opponent profiles are JSON documents validated before use. Version 1 binds a
profile to position-feature set version 1 and provides one signed preference
weight plus one confidence value for every feature.

- Weights range from `-1000` to `1000`. Positive means a future selector may
  prefer more of that characteristic; negative means it may prefer less.
- Confidence ranges from `0` to `1000` and represents evidential strength.
- Missing features, unknown fields, duplicate JSON keys, non-integer values,
  non-finite values, unsupported versions, and out-of-range values are rejected.
- Profile IDs are stable lowercase identifiers. Creation timestamps must include
  a timezone. Provenance records the source and analyzed sample counts.
- Profile data cannot override the engine's safety limits. The 35 cp eligibility
  bound and mate protections remain engine-owned.

The canonical zero-effect fallback is `profiles/neutral_v1.json`. It is valid
only with zero weights, zero confidence, and zero analyzed samples. Synthetic
profiles introduced in roadmap step 5 will use the same schema with `synthetic`
provenance; learned profiles will use `pgn` provenance.

The machine-readable contract is `schemas/opponent_profile_v1.schema.json`, and
`engine/adaptive_profile.py` is the strict runtime validator and serializer.
Changing feature meanings requires a new `feature_set_version`; changing the
document structure or validation semantics requires a new `schema_version`.
