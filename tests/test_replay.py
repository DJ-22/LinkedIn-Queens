import multiprocessing
import random
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from queens import replay
from queens.board_parser import parse_regions
from queens.config import COLORS
from queens.generator import generate_level
from queens.replay import decode, encode, record_steps, solve_and_record
from queens.solver import solve


class SearchWithoutQueens:

    def __init__(self, n):
        self.placed = [-1] * n

    def backtrack(self):
        self.placed[0] = 0
        return True


def solve_without_a_queens_list(n, _regions):
    SearchWithoutQueens(n).backtrack()


def random_board(n, seed):
    return parse_regions(generate_level(n, list(COLORS), random.Random(seed)))


class EncodingTest(unittest.TestCase):
    def test_round_trips_every_cell_of_a_32_wide_board(self):
        for r in range(32):
            for c in range(32):
                for placed in (0, 1):
                    self.assertEqual(
                        decode(encode(r, c, placed)), (r, c, placed)
                    )


class RecordStepsTest(unittest.TestCase):
    def test_replaying_the_steps_ends_on_the_solvers_answer(self):
        for n, seed in ((6, 0), (8, 1), (10, 2)):
            with self.subTest(n=n, seed=seed):
                regions, size = random_board(n, seed)
                answer = [row.index(True) for row in solve(size, regions)]

                steps, complete = record_steps(size, regions)
                board = [-1] * size
                for step in steps:
                    r, c, placed = decode(step)
                    board[r] = c if placed else -1

                self.assertTrue(complete)
                self.assertEqual(board, answer)

    def test_stops_early_at_max_steps(self):
        regions, n = random_board(14, 7)
        steps, complete = record_steps(n, regions, max_steps=5)

        self.assertFalse(complete)
        self.assertGreaterEqual(len(steps), 5)

    def test_refuses_boards_too_wide_to_encode(self):
        with self.assertRaisesRegex(RuntimeError, "up to 32x32"):
            record_steps(33, {})

    def test_missing_queens_list_raises_runtime_error(self):
        with (
            mock.patch.object(replay, "solve", solve_without_a_queens_list),
            mock.patch.object(replay, "Search", SearchWithoutQueens),
            self.assertRaisesRegex(RuntimeError, "no queens list"),
        ):
            record_steps(4, {})


class SolveAndRecordTest(unittest.TestCase):
    def test_sends_the_timed_answer_then_the_steps(self):
        grid = generate_level(7, list(COLORS), random.Random(0))
        receiver, sender = multiprocessing.Pipe(duplex=False)

        solve_and_record(grid, sender)
        kind, solution, elapsed = receiver.recv()
        steps_kind, steps, complete = receiver.recv()

        self.assertEqual(kind, "solved")
        self.assertIsNotNone(solution)
        self.assertGreaterEqual(elapsed, 0)
        self.assertEqual((steps_kind, complete), ("steps", True))
        self.assertTrue(steps)

    def test_child_process_does_not_load_pygame(self):
        code = (
            "import runpy, sys\n"
            "runpy.run_path('main.py', run_name='__mp_main__')\n"
            "from queens import replay\n"
            "print('pygame' in sys.modules)\n"
        )
        repo_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertEqual(result.stdout.strip(), "False")


if __name__ == "__main__":
    unittest.main()
