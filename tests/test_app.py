import random
import time
import unittest
import warnings
from unittest import mock

import pygame

from queens import app, rules, widgets
from queens.board_parser import parse_regions
from queens.solver import solve
from queens.visualizer import draw_crown


def make_app():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "no fast renderer available")
        return app.App()


class DrawCrownTest(unittest.TestCase):
    CROWN, SHADOW = (255, 0, 0), (0, 0, 255)

    def draw(self, **shadow):
        surface = pygame.Surface((100, 100))
        draw_crown(surface, (50, 50), 60, self.CROWN, **shadow)
        return surface

    def test_without_a_shadow_only_the_crown_is_drawn(self):
        surface = self.draw()

        self.assertEqual(surface.get_at((50, 60))[:3], self.CROWN)
        self.assertEqual(surface.get_at((50, 67))[:3], (0, 0, 0))

    def test_shadow_shows_below_the_crown(self):
        surface = self.draw(shadow=self.SHADOW, shadow_offset=6)

        self.assertEqual(surface.get_at((50, 60))[:3], self.CROWN)
        self.assertEqual(surface.get_at((50, 67))[:3], self.SHADOW)

    def test_scaled_shadow_forms_a_halo(self):
        surface = self.draw(shadow=self.SHADOW, shadow_scale=1.2)

        self.assertEqual(surface.get_at((50, 66))[:3], self.SHADOW)


class ButtonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = make_app()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def press(self, key):
        self.app.screen.handle(
            pygame.event.Event(pygame.KEYDOWN, key=key, unicode="", mod=0)
        )

    def test_presses_left_on_a_screen_that_was_switched_away_are_dropped(self):
        self.app.show(app.PlayScreen(self.app, 6))
        shown = []
        show = self.app.show
        self.app.show = lambda screen: (
            shown.append(type(screen).__name__),
            show(screen),
        )
        try:
            self.press(pygame.K_ESCAPE)
            self.press(pygame.K_n)
            self.app.screen.update(time.monotonic() + 1)
        finally:
            del self.app.show

        self.assertEqual(len(shown), 1)


class AppStartupTest(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_first_screen_is_entered_like_any_other(self):
        with mock.patch.object(app.MenuScreen, "enter") as enter:
            first = make_app().screen

        self.assertIsInstance(first, app.MenuScreen)
        enter.assert_called_once()


class EventLoopTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = make_app()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.app.running = True
        self.app.screen = mock.Mock(animating=mock.Mock(return_value=False))

    def test_dispatch_stops_at_quit_and_drops_later_events(self):
        key = pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_n, unicode="n", mod=0
        )
        self.app.dispatch([key, pygame.event.Event(pygame.QUIT), key])

        self.assertFalse(self.app.running)
        self.app.screen.handle.assert_called_once_with(key)

    def test_idle_screen_waits_for_the_next_event(self):
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(app.TICK))
        clock = mock.Mock()

        events = self.app.next_events(clock)

        self.assertEqual([event.type for event in events], [app.TICK])
        clock.tick.assert_not_called()

    def test_animating_screen_runs_at_full_frame_rate(self):
        self.app.screen.animating.return_value = True
        clock = mock.Mock()

        self.app.next_events(clock)

        clock.tick.assert_called_once_with(app.FPS)


class MenuScreenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = make_app()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def open_website(self, browser_result):
        menu = app.MenuScreen(self.app)
        with mock.patch.object(
            app.webbrowser, "open", return_value=browser_result
        ):
            menu.open_website()
        return menu.toast_message()

    def test_says_the_website_opened_only_when_it_did(self):
        self.assertIn("Opened", self.open_website(True)[0])

    def test_reports_when_no_browser_could_open(self):
        text, color = self.open_website(False)

        self.assertIn("Couldn't open a browser", text)
        self.assertEqual(color, app.ERROR)


class SizeScreenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = make_app()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.screen = app.SizeScreen(self.app, "Play", app.PlayScreen)

    def click(self, pos):
        return self.screen.handle(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)
        )

    def test_one_dot_per_size_centered_on_the_window(self):
        first, last = self.screen.dot_center(
            app.MIN_SIZE
        ), self.screen.dot_center(app.MAX_SIZE)

        self.assertEqual(len(app.SIZES), app.MAX_SIZE - app.MIN_SIZE + 1)
        self.assertEqual((first[0] + last[0]) // 2, app.WIDTH // 2)

    def test_clicking_a_dot_picks_that_size(self):
        self.assertTrue(self.click(self.screen.dot_center(13)))
        self.assertEqual(self.screen.value, "13")

    def test_box_shadow_is_built_once_the_box_stops_growing(self):
        surface = pygame.Surface((app.WIDTH, app.HEIGHT))
        settled = self.screen.started + 5
        self.screen.draw(surface, settled)
        shadow = self.screen.shadow

        self.screen.draw(surface, settled + 1)
        self.assertIs(self.screen.shadow, shadow)

    def test_clicking_between_dots_changes_nothing(self):
        x, y = self.screen.dot_center(13)
        before = self.screen.value

        self.click((x + app.SizeScreen.DOT_GAP // 2, y + 40))
        self.assertEqual(self.screen.value, before)


class PillTest(unittest.TestCase):
    def test_pill_is_centered_where_asked(self):
        pygame.font.init()
        surface = pygame.Surface((300, 100))
        font = pygame.font.Font(None, 18)
        widgets.Pill().draw(surface, font, "Hi", app.PURPLE, (150, 50), now=0)

        width = widgets.Pill().width(font, "Hi")
        left, right = 150 - width // 2, 150 + width // 2
        self.assertEqual(surface.get_at((left + 3, 50))[:3], app.PURPLE)
        self.assertEqual(surface.get_at((right - 4, 50))[:3], app.PURPLE)
        self.assertEqual(surface.get_at((left - 2, 50))[:3], (0, 0, 0))
        self.assertEqual(surface.get_at((right + 1, 50))[:3], (0, 0, 0))


class SolveScreenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = make_app()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def screen_with_broken_pipe(self, phase):
        """A solve screen whose child died partway through a message."""
        screen = app.SolveScreen(self.app, 6)
        screen.phase = phase
        screen.solution = [0] * 6
        screen.result = ("Solved in 0.00100 seconds", app.GREEN)
        screen.process = mock.Mock(is_alive=mock.Mock(return_value=True))
        screen.conn = mock.Mock(
            poll=mock.Mock(return_value=True),
            recv=mock.Mock(side_effect=EOFError),
        )
        return screen

    def test_broken_pipe_while_solving_fails_instead_of_crashing(self):
        screen = self.screen_with_broken_pipe("solving")
        screen.check_solver(time.monotonic())

        self.assertEqual(screen.phase, "failed")

    def test_broken_pipe_while_recording_shows_the_answer(self):
        screen = self.screen_with_broken_pipe("recording")
        screen.check_solver(time.monotonic())

        self.assertEqual(screen.phase, "done")
        self.assertEqual(screen.current, [0] * 6)


class PlayScreenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = make_app()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        random.seed(3)
        self.app.auto_x = False
        self.screen = app.PlayScreen(self.app, 8)
        self.app.show(self.screen)
        regions, n = parse_regions(self.screen.board.grid)
        self.answer = [
            (r, row.index(True)) for r, row in enumerate(solve(n, regions))
        ]

    def place_queen(self, cell):
        self.screen.click(cell, clear=False)
        self.screen.click(cell, clear=False)

    def test_full_valid_board_wins(self):
        for cell in self.answer:
            self.place_queen(cell)

        self.assertIsNotNone(self.screen.finished_at)

    def test_clashing_queens_are_flagged(self):
        first = self.answer[0]
        same_row = (first[0], (first[1] + 3) % 8)
        self.place_queen(first)
        self.place_queen(same_row)

        self.assertEqual(self.screen.clashes, {first, same_row})
        self.assertIsNone(self.screen.finished_at)

    def test_auto_x_keeps_crosses_until_every_covering_queen_is_gone(self):
        self.app.auto_x = True
        a, b = self.answer[0], self.answer[4]
        self.screen.marks[a] = self.screen.marks[b] = "queen"
        grid = self.screen.board.grid
        shared = rules.covered_cells(grid, [a]) & rules.covered_cells(
            grid, [b]
        )
        only_a = (
            rules.covered_cells(grid, [a])
            - rules.covered_cells(grid, [b])
            - {b}
        )

        del self.screen.marks[a]
        crosses = self.screen.auto_crosses(self.screen.queens)

        self.assertTrue(shared)
        self.assertLessEqual(shared, crosses)
        self.assertFalse(only_a & crosses)

    def test_covered_cells_are_reused_until_the_queens_change(self):
        a, b = self.answer[0], self.answer[4]
        first = self.screen.covered([a, b])

        self.assertIs(self.screen.covered([b, a]), first)
        self.assertEqual(
            self.screen.covered([a]),
            rules.covered_cells(self.screen.board.grid, [a]),
        )
        self.assertEqual(self.screen.covered([a, b]), first)

    def test_auto_x_never_removes_the_players_own_crosses(self):
        self.app.auto_x = True
        queen = self.answer[0]
        own_cross = next(
            iter(rules.covered_cells(self.screen.board.grid, [queen]))
        )
        self.screen.marks[own_cross] = "cross"
        self.screen.marks[queen] = "queen"

        del self.screen.marks[queen]

        self.assertEqual(self.screen.marks.get(own_cross), "cross")


if __name__ == "__main__":
    unittest.main()
