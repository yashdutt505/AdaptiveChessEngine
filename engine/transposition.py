"""Fixed-size transposition table keyed by Zobrist hashes."""

from dataclasses import dataclass


EXACT = 0
LOWER_BOUND = 1
UPPER_BOUND = 2
APPROX_ENTRY_BYTES = 64


@dataclass(slots=True)
class TTEntry:
    key: int
    depth: int
    score: int
    flag: int
    best_move: int | None
    generation: int


class TranspositionTable:
    """Direct-mapped cache with depth-preferred replacement."""

    def __init__(self, size_mb=64):
        self.generation = 0
        self.resize(size_mb)

    def resize(self, size_mb):
        size_mb = max(1, int(size_mb))
        self.size_mb = size_mb
        self.capacity = max(1024, size_mb * 1024 * 1024 // APPROX_ENTRY_BYTES)
        self.entries = [None] * self.capacity

    def clear(self):
        self.entries = [None] * self.capacity
        self.generation = 0

    def new_search(self):
        self.generation = (self.generation + 1) & 0xFFFF

    def probe(self, key):
        entry = self.entries[key % self.capacity]
        return entry if entry is not None and entry.key == key else None

    def store(self, key, depth, score, flag, best_move):
        index = key % self.capacity
        current = self.entries[index]
        if (
            current is None
            or current.key != key
            or current.generation != self.generation
            or depth >= current.depth
        ):
            self.entries[index] = TTEntry(
                key=key,
                depth=depth,
                score=score,
                flag=flag,
                best_move=best_move,
                generation=self.generation,
            )

    def hashfull(self):
        """Return approximate occupancy in per-mille, as required by UCI."""
        sample_size = min(1000, self.capacity)
        if sample_size == 0:
            return 0
        used = sum(
            entry is not None and entry.generation == self.generation
            for entry in self.entries[:sample_size]
        )
        return used * 1000 // sample_size
