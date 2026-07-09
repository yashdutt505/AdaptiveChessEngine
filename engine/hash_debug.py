"""
hash_debug.py

Utilities for verifying incremental
Zobrist hashing.
"""

from .zobrist import compute_hash


def verify_incremental_hash(position):
    """
    Verifies that the incremental hash matches
    a complete recomputation.
    """

    expected = compute_hash(position)

    if expected != position.hash_key:

        print("\n========== HASH ERROR ==========\n")

        print(f"Stored Hash     : 0x{position.hash_key:016X}")
        print(f"Expected Hash   : 0x{expected:016X}")

        raise AssertionError(
            "Incremental hash does not match computed hash."
        )

    return True