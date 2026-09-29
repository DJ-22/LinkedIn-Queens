import random
import unittest
from collections import deque

from queens.board_parser import parse_regions
from queens.config import COLORS
from queens.generator import generate_level
from queens.solver import solve


def is_connected(cells):
    cells = set(cells)
    start = next(iter(cells))
    seen = {start}
    queue = deque([start])

    while queue:
        r, c = queue.popleft()
        for neighbor in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)

    return seen == cells


class GenerateLevelTest(unittest.TestCase):
    def test_levels_have_n_connected_regions(self):
        for n in range(4, 21):
            for seed in range(3):
                with self.subTest(n=n, seed=seed):
                    grid = generate_level(n, list(COLORS), random.Random(seed))
                    regions, size = parse_regions(grid)

                    self.assertEqual(size, n)
                    self.assertTrue(all(len(row) == n for row in grid))
                    self.assertEqual(len(regions), n)
                    self.assertTrue(
                        all(is_connected(cells) for cells in regions.values())
                    )

    def test_levels_are_solvable(self):
        for n in range(4, 11):
            for seed in range(5):
                with self.subTest(n=n, seed=seed):
                    regions, size = parse_regions(
                        generate_level(n, list(COLORS), random.Random(seed))
                    )
                    self.assertIsNotNone(solve(size, regions))

    def test_same_seed_gives_same_level(self):
        first = generate_level(9, list(COLORS), random.Random(42))
        second = generate_level(9, list(COLORS), random.Random(42))

        self.assertEqual(first, second)

    def test_needs_a_color_per_region(self):
        with self.assertRaises(ValueError):
            generate_level(8, list(COLORS)[:7])


if __name__ == "__main__":
    unittest.main()
