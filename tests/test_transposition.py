import unittest

from engine.constants import START_FEN
from engine.search import Searcher
from engine.transposition import EXACT, LOWER_BOUND, TranspositionTable
from tests.helpers import position_from_fen


class TranspositionTableTests(unittest.TestCase):
    def test_store_probe_and_clear(self):
        table = TranspositionTable(1)
        table.store(12345, 4, 27, EXACT, 99)
        entry = table.probe(12345)
        self.assertIsNotNone(entry)
        self.assertEqual((entry.depth, entry.score, entry.flag, entry.best_move), (4, 27, EXACT, 99))
        table.clear()
        self.assertIsNone(table.probe(12345))

    def test_deeper_entry_is_not_replaced_by_shallower_one(self):
        table = TranspositionTable(1)
        table.store(10, 5, 40, EXACT, 1)
        table.store(10, 2, 10, LOWER_BOUND, 2)
        entry = table.probe(10)
        self.assertEqual(entry.depth, 5)
        self.assertEqual(entry.best_move, 1)

    def test_resize_changes_capacity_and_clears_entries(self):
        table = TranspositionTable(1)
        original_capacity = table.capacity
        table.store(10, 1, 0, EXACT, None)
        table.resize(2)
        self.assertGreater(table.capacity, original_capacity)
        self.assertIsNone(table.probe(10))

    def test_repeated_search_reuses_exact_root_result(self):
        position = position_from_fen(START_FEN)
        table = TranspositionTable(1)
        first = Searcher(transposition_table=table).search(position, 3)
        second = Searcher(transposition_table=table).search(position, 3)
        self.assertEqual(second.best_move, first.best_move)
        self.assertEqual(second.score, first.score)
        self.assertLess(second.nodes, first.nodes)

    def test_four_colliding_keys_coexist_in_cluster(self):
        table = TranspositionTable(1)
        keys = [17 + offset * table.bucket_count for offset in range(4)]
        for depth, key in enumerate(keys, start=1):
            table.store(key, depth, depth * 10, EXACT, depth)
        self.assertEqual([table.probe(key).depth for key in keys], [1, 2, 3, 4])

    def test_cluster_replaces_shallowest_current_entry(self):
        table = TranspositionTable(1)
        keys = [23 + offset * table.bucket_count for offset in range(5)]
        for depth, key in enumerate(keys[:4], start=1):
            table.store(key, depth, 0, LOWER_BOUND, None)
        table.store(keys[4], 5, 0, EXACT, None)
        self.assertIsNone(table.probe(keys[0]))
        self.assertIsNotNone(table.probe(keys[4]))
