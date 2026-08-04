"""Fixed-size transposition table keyed by Zobrist hashes."""

from dataclasses import dataclass


EXACT = 0
LOWER_BOUND = 1
UPPER_BOUND = 2
APPROX_ENTRY_BYTES = 64
CLUSTER_SIZE = 4


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
        requested = max(1024, size_mb * 1024 * 1024 // APPROX_ENTRY_BYTES)
        self.bucket_count = max(256, requested // CLUSTER_SIZE)
        self.capacity = self.bucket_count * CLUSTER_SIZE
        self.entries = [None] * self.capacity

    def clear(self):
        self.entries = [None] * self.capacity
        self.generation = 0

    def new_search(self):
        self.generation = (self.generation + 1) & 0xFFFF

    def probe(self, key):
        start = (key % self.bucket_count) * CLUSTER_SIZE
        for index in range(start, start + CLUSTER_SIZE):
            entry = self.entries[index]
            if entry is not None and entry.key == key:
                return entry
        return None

    def store(self, key, depth, score, flag, best_move):
        start = (key % self.bucket_count) * CLUSTER_SIZE
        indices = range(start, start + CLUSTER_SIZE)
        replacement = None
        for index in indices:
            current = self.entries[index]
            if current is not None and current.key == key:
                if current.generation == self.generation and depth < current.depth:
                    return
                replacement = index
                break
            if current is None:
                replacement = index
                break
        if replacement is None:
            replacement = min(
                indices,
                key=lambda index: (
                    self.entries[index].generation == self.generation,
                    self.entries[index].depth,
                    self.entries[index].flag == EXACT,
                ),
            )
        self.entries[replacement] = TTEntry(
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
