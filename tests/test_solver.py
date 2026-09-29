import random
import time
import unittest

from queens.board_parser import parse_regions
from queens.config import COLORS
from queens.generator import generate_level
from queens.solver import solve


def assert_valid_solution(test, grid, solution):
    n = len(grid)
    test.assertEqual([row.count(True) for row in solution], [1] * n)

    queens = [(r, row.index(True)) for r, row in enumerate(solution)]
    test.assertEqual(
        len({c for _, c in queens}), n, "two queens share a column"
    )
    test.assertEqual(
        len({grid[r][c] for r, c in queens}), n, "two queens share a region"
    )
    for (r1, c1), (r2, c2) in zip(queens, queens[1:]):
        test.assertGreater(
            abs(c1 - c2), 1, f"queens in rows {r1} and {r2} touch"
        )


class SolveTest(unittest.TestCase):
    def test_solves_generated_boards(self):
        for n in range(4, 13):
            for seed in range(5):
                with self.subTest(n=n, seed=seed):
                    grid = generate_level(n, list(COLORS), random.Random(seed))
                    regions, size = parse_regions(grid)
                    solution = solve(size, regions)

                    self.assertIsNotNone(solution)
                    assert_valid_solution(self, grid, solution)

    def test_boards_that_used_to_take_seconds_solve_quickly(self):
        for n, seed in ((20, 5), (20, 9), (16, 8)):
            with self.subTest(n=n, seed=seed):
                grid = generate_level(n, list(COLORS), random.Random(seed))
                regions, size = parse_regions(grid)

                start = time.perf_counter()
                solution = solve(size, regions)
                self.assertLess(time.perf_counter() - start, 1.0)
                assert_valid_solution(self, grid, solution)

    def test_returns_none_when_unsolvable(self):
        grid = [
            ["a", "a", "b", "b"],
            ["c", "c", "c", "c"],
            ["d", "d", "d", "d"],
            ["d", "d", "d", "d"],
        ]
        regions, n = parse_regions(grid)

        self.assertIsNone(solve(n, regions))

    def test_rejects_wrong_region_count(self):
        regions, n = parse_regions([["a", "a", "b", "b"]] * 4)

        with self.assertRaises(ValueError):
            solve(n, regions)

    def test_rejects_regions_that_miss_cells(self):
        regions = {"a": [(0, 0)], "b": [(0, 1)], "c": [(1, 0)], "d": [(3, 3)]}

        with self.assertRaises(ValueError):
            solve(4, regions)


if __name__ == "__main__":
    unittest.main()
