import unittest

from queens import rules

GRID = [
    ["a", "a", "b", "b"],
    ["a", "c", "c", "b"],
    ["d", "c", "c", "b"],
    ["d", "d", "d", "b"],
]


class RulesTest(unittest.TestCase):
    def test_conflicts(self):
        self.assertTrue(rules.conflicts(GRID, (0, 0), (0, 3)))
        self.assertTrue(rules.conflicts(GRID, (0, 0), (3, 0)))
        self.assertTrue(rules.conflicts(GRID, (0, 0), (1, 1)))
        self.assertTrue(rules.conflicts(GRID, (1, 1), (2, 2)))
        self.assertTrue(rules.conflicts(GRID, (0, 2), (3, 3)))
        self.assertFalse(rules.conflicts(GRID, (0, 1), (2, 2)))
        self.assertFalse(rules.conflicts(GRID, (0, 0), (2, 3)))

    def test_covered_cells_skips_the_queens_themselves(self):
        covered = rules.covered_cells(GRID, [(0, 0)])

        self.assertNotIn((0, 0), covered)
        self.assertEqual(
            covered,
            {
                (0, 1),
                (0, 2),
                (0, 3),
                (1, 0),
                (2, 0),
                (3, 0),
                (1, 1),
            },
        )

    def test_touching_includes_diagonals_but_not_the_cell_itself(self):
        self.assertTrue(rules.touching((2, 2), (1, 1)))
        self.assertTrue(rules.touching((2, 2), (2, 3)))
        self.assertFalse(rules.touching((2, 2), (2, 2)))
        self.assertFalse(rules.touching((2, 2), (0, 2)))

    def test_neighbors_matches_touching(self):
        n = 4
        for r in range(n):
            for c in range(n):
                expected = {
                    (rr, cc)
                    for rr in range(n)
                    for cc in range(n)
                    if rules.touching((r, c), (rr, cc))
                }
                self.assertEqual(set(rules.neighbors(r, c, n)), expected)


if __name__ == "__main__":
    unittest.main()
