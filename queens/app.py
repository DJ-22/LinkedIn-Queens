import itertools
import math
import multiprocessing
import time
import webbrowser
from collections import deque

import pygame

from queens.config import COLORS
from queens.effects import (
    Confetti,
    blit_scaled,
    darken,
    ease_out_back,
    ease_out_cubic,
    lighten,
    mix,
    progress,
    rounded,
    soft_shadow,
    vertical_gradient,
)
from queens.generator import generate_level
from queens.replay import decode, solve_and_record
from queens.rules import conflicts, covered_cells
from queens.visualizer import CLASH, Board, draw_crown
from queens.widgets import ENTRANCE, Button, Pill, draw_pills, scaled_rect

WEBSITE_URL = "https://queensgame.vercel.app"
MIN_SIZE, MAX_SIZE = 4, 20
SIZES = range(MIN_SIZE, MAX_SIZE + 1)

WIDTH, HEIGHT = 720, 820
BOARD_TOP, BOARD_PX = 122, 580

TEXT = (40, 30, 70)
MUTED = (115, 105, 140)
PURPLE = (124, 92, 255)
CORAL = (255, 107, 107)
ORANGE = (255, 159, 28)
YELLOW = (255, 200, 40)
GREEN = (38, 190, 110)
TEAL = (0, 180, 170)
BLUE = (60, 130, 255)
PINK = (255, 95, 180)
SLATE = (100, 104, 135)
GOLD = (255, 196, 30)
ERROR = CLASH
POP = [CORAL, ORANGE, YELLOW, GREEN, TEAL, BLUE, PURPLE, PINK]

TICK = pygame.USEREVENT + 1
FPS = 60


def load_font(size, bold=True):
    return pygame.font.SysFont("segoeui,trebuchetms,arial", size, bold=bold)


def format_clock(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}:{seconds:02d}"


class Screen:
    def __init__(self, app):
        self.app = app
        self.buttons = []
        self.started = time.monotonic()

    def handle(self, event):
        return any(button.handle(event) for button in self.buttons)

    def update(self, now):
        for button in self.buttons:
            if self.app.screen is not self:
                return

            button.update(now)

    def draw(self, surface, now):
        for button in self.buttons:
            button.draw(surface, self.app.button_font, now, self.started)

    def animating(self, now):
        return any(
            button.animating(now, self.started) for button in self.buttons
        )

    def clickable(self, pos):
        return any(button.rect.collidepoint(pos) for button in self.buttons)

    def enter(self):
        pass

    def leave(self):
        pass


class MenuScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.toast_at = None
        self.browser_opened = False
        x = WIDTH // 2 - 220
        self.buttons = [
            Button(
                "1   Open the website",
                (x, 310, 440, 66),
                self.open_website,
                (pygame.K_1, pygame.K_KP1),
                CORAL,
                0.35,
            ),
            Button(
                "2   Play a random level",
                (x, 400, 440, 66),
                lambda: app.show(
                    SizeScreen(app, "Play a random level", PlayScreen)
                ),
                (pygame.K_2, pygame.K_KP2),
                PURPLE,
                0.42,
            ),
            Button(
                "3   Watch the solver",
                (x, 490, 440, 66),
                lambda: app.show(
                    SizeScreen(app, "Watch the solver", SolveScreen)
                ),
                (pygame.K_3, pygame.K_KP3),
                TEAL,
                0.49,
            ),
            Button(
                "Quit",
                (WIDTH // 2 - 100, 600, 200, 54),
                app.quit,
                (pygame.K_ESCAPE,),
                SLATE,
                0.56,
            ),
        ]

        self.letters = [
            (
                app.hero_font.render(letter, True, color),
                app.hero_font.render(letter, True, darken(color, 0.45)),
            )
            for letter, color in zip("Queens", POP[::-1])
        ]
        self.toast = Pill(bump=False)

    def open_website(self):
        self.browser_opened = webbrowser.open(WEBSITE_URL)
        self.toast_at = time.monotonic()

    def toast_message(self):
        if self.browser_opened:
            return f"Opened {WEBSITE_URL} in your browser", GREEN

        return f"Couldn't open a browser; visit {WEBSITE_URL}", ERROR

    def animating(self, now):
        toast = self.toast_at is not None and now < self.toast_at + 2.8
        return super().animating(now) or now < self.started + 1.0 or toast

    def draw(self, surface, now):
        crown_in = ease_out_back(progress(self.started, 0.55, now))
        draw_crown(
            surface,
            (WIDTH // 2, 80 - (1 - crown_in) * 80),
            92,
            GOLD,
            shadow=darken(GOLD, 0.25),
            shadow_offset=6,
        )

        total = sum(letter.get_width() for letter, _ in self.letters)
        x = WIDTH // 2 - total // 2
        for i, (letter, shadow) in enumerate(self.letters):
            t = progress(self.started + 0.1 + i * 0.06, 0.5, now)
            if t > 0:
                y = 172 - (1 - ease_out_back(t)) * 70
                alpha = round(255 * ease_out_cubic(t))
                blit_scaled(
                    surface,
                    shadow,
                    (x + letter.get_width() // 2, y + 6),
                    1,
                    alpha,
                )
                blit_scaled(
                    surface, letter, (x + letter.get_width() // 2, y), 1, alpha
                )
            x += letter.get_width()

        fade = round(255 * progress(self.started + 0.3, 0.4, now))
        self.app.text(
            "Pick an option with the mouse or the number keys",
            262,
            color=MUTED,
            alpha=fade,
        )
        super().draw(surface, now)

        if self.toast_at is not None:
            visible = min(
                progress(self.toast_at, 0.25, now),
                1 - progress(self.toast_at + 2.4, 0.4, now),
            )
            if visible > 0:
                draw_pills(
                    surface,
                    self.app.pill_font,
                    now,
                    WIDTH // 2,
                    715,
                    [(self.toast, *self.toast_message())],
                    ease_out_back(visible),
                )


class SizeScreen(Screen):
    DOT_GAP = 24

    def __init__(self, app, title, next_screen):
        super().__init__(app)
        self.title = title
        self.next_screen = next_screen
        self.value = str(app.last_size)
        self.replace_value = True
        self.error = ""
        self.changed_at = None
        self.error_at = None
        self.shadow = None

        self.box = pygame.Rect(WIDTH // 2 - 90, 250, 180, 116)
        self.buttons = [
            Button(
                "-",
                (self.box.x - 96, self.box.centery - 34, 68, 68),
                lambda: self.step(-1),
                (pygame.K_DOWN,),
                CORAL,
                0.25,
                instant=True,
            ),
            Button(
                "+",
                (self.box.right + 28, self.box.centery - 34, 68, 68),
                lambda: self.step(1),
                (pygame.K_UP,),
                TEAL,
                0.3,
                instant=True,
            ),
            Button(
                "Start",
                (WIDTH // 2 - 215, 480, 205, 58),
                self.start,
                (pygame.K_RETURN, pygame.K_KP_ENTER),
                GREEN,
                0.35,
            ),
            Button(
                "Back",
                (WIDTH // 2 + 10, 480, 205, 58),
                lambda: app.show(MenuScreen(app)),
                (pygame.K_ESCAPE,),
                SLATE,
                0.4,
            ),
        ]

    def dot_center(self, size):
        left = WIDTH // 2 - (len(SIZES) - 1) * self.DOT_GAP // 2
        return left + (size - MIN_SIZE) * self.DOT_GAP, 412

    def dot_at(self, pos):
        for size in SIZES:
            x, y = self.dot_center(size)
            if (pos[0] - x) ** 2 + (pos[1] - y) ** 2 <= 12**2:
                return size

        return None

    def set_value(self, value):
        if value != self.value:
            self.value = value
            self.changed_at = time.monotonic()
        self.error = ""

    def step(self, delta):
        current = (
            int(self.value) if self.value.isdigit() else self.app.last_size
        )
        self.set_value(str(min(MAX_SIZE, max(MIN_SIZE, current + delta))))
        self.replace_value = False

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.unicode.isdigit() and (
                self.replace_value or len(self.value) < 2
            ):
                self.set_value(
                    event.unicode
                    if self.replace_value
                    else self.value + event.unicode
                )
            elif event.key == pygame.K_BACKSPACE:
                self.set_value(self.value[:-1])

            self.replace_value = False
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and (size := self.dot_at(event.pos))
        ):
            self.set_value(str(size))
            self.replace_value = True
            return True

        return super().handle(event)

    def start(self):
        if (
            not self.value.isdigit()
            or not MIN_SIZE <= int(self.value) <= MAX_SIZE
        ):
            self.error = f"Enter a whole number from {MIN_SIZE} to {MAX_SIZE}"
            self.error_at = time.monotonic()
            return

        self.app.last_size = int(self.value)
        self.app.show(self.next_screen(self.app, self.app.last_size))

    def clickable(self, pos):
        return super().clickable(pos) or self.dot_at(pos) is not None

    def animating(self, now):
        recent = max(self.changed_at or 0, self.error_at or 0)
        return (
            super().animating(now)
            or now < self.started + 0.8
            or now < recent + 0.5
        )

    def draw(self, surface, now):
        intro = ease_out_back(progress(self.started, ENTRANCE, now))
        self.app.text(
            self.title,
            130 - (1 - intro) * 40,
            self.app.title_font,
            alpha=round(255 * min(1, intro)),
        )
        self.app.text(
            f"Board size from {MIN_SIZE} to {MAX_SIZE}",
            190,
            color=MUTED,
            alpha=round(255 * progress(self.started + 0.15, 0.3, now)),
        )

        shake = progress(self.error_at, 0.45, now) if self.error_at else 1
        box = self.box.move(
            round(math.sin(shake * math.pi * 8) * (1 - shake) * 14), 0
        )
        box = scaled_rect(
            box, ease_out_back(progress(self.started + 0.1, ENTRANCE, now))
        )
        if box.width > 4:
            if self.shadow is None or self.shadow[0] != box.size:
                self.shadow = (box.size, soft_shadow(box.size, 22, alpha=60))
            surface.blit(
                self.shadow[1],
                self.shadow[1].get_rect(center=(box.centerx, box.centery + 5)),
            )
            pygame.draw.rect(surface, (255, 255, 255), box, border_radius=22)
            pygame.draw.rect(
                surface,
                ERROR if self.error else PURPLE,
                box,
                4,
                border_radius=22,
            )

            bump = (
                1
                + 0.25
                * (1 - ease_out_cubic(progress(self.changed_at, 0.25, now)))
                if self.changed_at
                else 1
            )
            color = ERROR if self.error else TEXT
            blit_scaled(
                surface,
                self.app.number_font.render(self.value or " ", True, color),
                box.center,
                bump * box.width / self.box.width,
            )

        chosen = int(self.value) if self.value.isdigit() else None
        for size in SIZES:
            t = progress(
                self.started + 0.2 + (size - MIN_SIZE) * 0.02, 0.3, now
            )
            if t <= 0:
                continue

            spot = (size - MIN_SIZE) / (len(SIZES) - 1) * (len(POP) - 1)
            color = mix(
                POP[int(spot)], POP[min(len(POP) - 1, int(spot) + 1)], spot % 1
            )
            center = self.dot_center(size)
            radius = (10 if size == chosen else 6) * ease_out_back(t)
            if size == chosen:
                pygame.draw.circle(
                    surface, lighten(color, 0.55), center, radius + 5
                )
            pygame.draw.circle(surface, color, center, max(1, radius))

        super().draw(surface, now)

        hint = (
            self.error
            or "Type a number, click a dot, or use the arrow keys, "
            "then press Enter"
        )
        self.app.text(
            hint,
            590,
            self.app.small_font,
            ERROR if self.error else MUTED,
            alpha=round(255 * progress(self.started + 0.4, 0.3, now)),
        )


class LevelScreen(Screen):

    def __init__(self, app, n, extra_buttons=()):
        super().__init__(app)
        self.n = n
        self.board = Board(
            generate_level(n, list(COLORS)),
            COLORS,
            WIDTH // 2,
            BOARD_TOP,
            BOARD_PX,
        )
        self.covered_for = None
        self.covered_now = set()

        specs = [
            (
                "New level (N)",
                lambda: app.show(type(self)(app, n)),
                (pygame.K_n,),
                ORANGE,
            ),
            *extra_buttons,
            (
                "Menu (Esc)",
                lambda: app.show(MenuScreen(app)),
                (pygame.K_ESCAPE,),
                SLATE,
            ),
        ]
        width, gap = 210, 15
        left = WIDTH // 2 - (len(specs) * width + (len(specs) - 1) * gap) // 2
        y = BOARD_TOP + BOARD_PX + 28
        self.buttons = [
            Button(
                label,
                (left + i * (width + gap), y, width, 54),
                action,
                keys,
                color,
                0.3 + i * 0.06,
            )
            for i, (label, action, keys, color) in enumerate(specs)
        ]

    def covered(self, queens):
        key = frozenset(queens)
        if key != self.covered_for:
            self.covered_for, self.covered_now = key, covered_cells(
                self.board.grid, key
            )
        return self.covered_now

    def draw_header(self, now, title, pills):
        intro = progress(self.started, ENTRANCE, now)
        self.app.text(
            title,
            42 - (1 - ease_out_back(intro)) * 40,
            self.app.title_font,
            alpha=round(255 * ease_out_cubic(intro)),
        )
        return draw_pills(
            self.app.surface,
            self.app.pill_font,
            now,
            WIDTH // 2,
            90,
            pills,
            ease_out_back(progress(self.started + 0.15, ENTRANCE, now)),
        )

    def draw_hint(self, now, hint):
        self.app.text(
            hint,
            HEIGHT - 16,
            self.app.small_font,
            MUTED,
            alpha=round(255 * progress(self.started + 0.5, 0.4, now)),
        )

    def animating(self, now):
        return (
            super().animating(now)
            or self.board.animating(now)
            or now < self.started + 0.9
        )


class PlayScreen(LevelScreen):
    def __init__(self, app, n):
        super().__init__(
            app, n, [("Auto X", self.toggle_auto_x, (pygame.K_a,), SLATE)]
        )
        self.auto_x_button = self.buttons[1]
        self.marks = {}
        self.clashes = set()
        self.last_queen = None
        self.finished_at = None
        self.panel = None
        self.panel_hidden = False
        self.confetti = None
        self.pills = [Pill(bump=False), Pill(), Pill()]

    def enter(self):
        pygame.time.set_timer(TICK, 500)

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            cell = self.board.cell_at(event.pos)
            if cell is not None and self.finished_at is None:
                self.click(cell, clear=event.button == 3)
                return True
            if self.finished_at is not None and self.panel_rect().collidepoint(
                event.pos
            ):
                self.panel_hidden = not self.panel_hidden
                return True

        return super().handle(event)

    @property
    def queens(self):
        return [cell for cell, mark in self.marks.items() if mark == "queen"]

    @property
    def win_time(self):
        return self.finished_at - self.started

    def toggle_auto_x(self):
        self.app.auto_x = not self.app.auto_x
        self.board.ripple_from = self.last_queen

    def auto_crosses(self, queens):
        return self.covered(queens) if self.app.auto_x else set()

    def click(self, cell, clear):
        # Left click cycles empty -> cross -> queen -> empty
        shown = self.marks.get(cell) or (
            "cross" if cell in self.auto_crosses(self.queens) else None
        )
        mark = (
            None
            if clear
            else {None: "cross", "cross": "queen", "queen": None}[shown]
        )
        if mark:
            self.marks[cell] = mark
        else:
            self.marks.pop(cell, None)

        if mark == "queen":
            self.last_queen = cell
        self.board.ripple_from = cell

        queens = self.queens
        self.clashes = self.find_clashes(queens)

        if len(queens) == self.n and not self.clashes:
            self.win()

    def find_clashes(self, queens):
        clashes = set()

        for a, b in itertools.combinations(queens, 2):
            if conflicts(self.board.grid, a, b):
                clashes.update({a, b})

        return clashes

    def win(self):
        now = time.monotonic()
        self.finished_at = now
        pygame.time.set_timer(TICK, 0)

        self.board.celebrate(now)
        self.confetti = Confetti(
            [(0, HEIGHT, 1), (WIDTH, HEIGHT, -1)], POP + [GOLD], now
        )
        self.panel = self.build_panel()

    def panel_rect(self):
        rect = pygame.Rect(0, 0, 400, 250)
        rect.center = self.board.rect.center
        return rect

    def build_panel(self):
        rect = self.panel_rect()
        size, center_x = rect.size, rect.width // 2
        card = rounded(vertical_gradient(size, PURPLE, PINK), 30)
        draw_crown(
            card,
            (center_x, 48),
            70,
            GOLD,
            shadow=darken(GOLD, 0.3),
            shadow_offset=4,
        )

        for text, font, color, y in (
            ("You win!", self.app.panel_font, (255, 255, 255), 118),
            (
                f"Time  {format_clock(self.win_time)}",
                self.app.button_font,
                (255, 255, 255),
                175,
            ),
            (
                "N for a new level  -  click to hide",
                self.app.small_font,
                (255, 255, 255),
                216,
            ),
        ):
            rendered = font.render(text, True, color)
            card.blit(rendered, rendered.get_rect(center=(center_x, y)))

        shadow = soft_shadow(size, 30, alpha=90, spread=12)
        panel = pygame.Surface(shadow.get_size(), pygame.SRCALPHA)
        panel.blit(shadow, (0, 8))
        panel.blit(card, (12, 12))
        return panel

    def clickable(self, pos):
        if self.finished_at is None:
            return (
                super().clickable(pos) or self.board.cell_at(pos) is not None
            )

        return super().clickable(pos) or self.panel_rect().collidepoint(pos)

    def animating(self, now):
        panel = self.finished_at is not None and now < self.finished_at + 1.2
        confetti = self.confetti is not None and self.confetti.alive()
        return (
            super().animating(now)
            or panel
            or confetti
            or any(pill.animating(now) for pill in self.pills)
        )

    def draw(self, surface, now):
        queens = self.queens
        if self.finished_at is not None:
            pills = [
                (self.pills[0], f"Time {format_clock(self.win_time)}", GREEN),
                (self.pills[1], "Solved!", GREEN),
            ]
        else:
            pills = [
                (
                    self.pills[0],
                    f"Time {format_clock(now - self.started)}",
                    BLUE,
                ),
                (self.pills[1], f"Queens {len(queens)}/{self.n}", PURPLE),
            ]
            if self.clashes:
                pills.append((self.pills[2], "Clash!", ERROR))
        self.draw_header(now, f"{self.n} x {self.n}", pills)

        crosses = {
            cell for cell, mark in self.marks.items() if mark == "cross"
        } | self.auto_crosses(queens)
        self.board.draw(surface, now, queens, crosses, self.clashes)

        self.auto_x_button.label = (
            f"Auto X: {'On' if self.app.auto_x else 'Off'} (A)"
        )
        self.auto_x_button.color = TEAL if self.app.auto_x else SLATE
        super().draw(surface, now)
        self.draw_hint(
            now,
            "Left click: cross, then queen, then clear.  "
            "Right click: clear.  A: auto X.",
        )

        if self.panel is not None and not self.panel_hidden:
            t = progress(self.finished_at + 0.45, 0.5, now)
            blit_scaled(
                surface,
                self.panel,
                self.panel_rect().center,
                ease_out_back(t),
                round(255 * min(1, t * 2)),
            )

        if self.confetti is not None:
            self.confetti.draw(surface, now)

    def leave(self):
        pygame.time.set_timer(TICK, 0)


class SolveScreen(LevelScreen):

    REPLAY_TIME = 5.0
    GHOST_TIME = 0.3

    def __init__(self, app, n):
        super().__init__(
            app, n, [("Replay (R)", self.replay, (pygame.K_r,), SLATE)]
        )
        self.replay_button = self.buttons[1]
        self.phase = "solving"
        self.process = None
        self.conn = None
        self.result = None
        self.solution = None
        self.steps = None
        self.complete = True
        self.note = None

        self.replay_start = None
        self.current = []
        self.applied = 0
        self.backtracks = 0
        self.ghosts = deque(maxlen=24)

        self.progress_pill = Pill(bump=False)
        self.result_pill = Pill()
        self.step_pill = Pill(bump=False)
        self.backtrack_pill = Pill(bump=False)

    def enter(self):
        self.conn, child_conn = multiprocessing.Pipe(duplex=False)
        self.process = multiprocessing.Process(
            target=solve_and_record,
            args=(self.board.grid, child_conn),
            daemon=True,
        )
        self.process.start()
        child_conn.close()

    def update(self, now):
        if self.phase in ("solving", "recording"):
            self.check_solver(now)
        if self.phase == "replay":
            self.advance(now)

        super().update(now)

    def check_solver(self, now):
        alive = self.process.is_alive()
        received = False

        try:
            while self.phase in ("solving", "recording") and self.conn.poll():
                received = True
                self.receive(self.conn.recv(), now)
        except (EOFError, OSError):
            alive = received = False

        if not received and not alive:
            if self.phase == "solving":
                self.fail(now, "The solver process stopped unexpectedly")
            elif self.phase == "recording":
                self.finish(
                    now,
                    "The solver's steps couldn't be recorded, "
                    "so here's just the answer",
                )

    def receive(self, message, now):
        kind, *payload = message

        if kind == "solved":
            solution, elapsed = payload
            if solution is None:
                self.fail(now, "No solution found!")
                return

            self.solution = [row.index(True) for row in solution]
            self.result = (f"Solved in {elapsed:.5f} seconds", GREEN)
            self.result_pill.changed_at = now
            self.phase = "recording"
        elif kind == "steps":
            self.steps, self.complete = payload
            self.start_replay(max(now, self.board.ready_at(now)))
        elif kind == "no-steps":
            self.finish(now, f"{payload[0]}, so here's just the answer")

    def fail(self, now, message):
        self.result = (message, ERROR)
        self.result_pill.changed_at = now
        self.phase = "failed"

    def start_replay(self, at):
        self.replay_start = at
        self.current = [-1] * self.n
        self.applied = 0
        self.backtracks = 0
        self.ghosts.clear()
        self.board.celebrate_at = None
        self.phase = "replay"

    def replay(self):
        if self.phase == "done" and self.steps:
            self.start_replay(time.monotonic())

    def advance(self, now):
        elapsed = (now - self.replay_start) / self.REPLAY_TIME
        if elapsed < 0:
            return

        total = len(self.steps)
        target = (
            total if elapsed >= 1 else min(total, int(elapsed * total) + 1)
        )

        while self.applied < target:
            r, c, placed = decode(self.steps[self.applied])
            self.current[r] = c if placed else -1
            if not placed:
                self.backtracks += 1
                self.ghosts.append(((r, c), now))
            self.applied += 1

        if elapsed >= 1:
            note = (
                None
                if self.complete
                else f"Showing the solver's first {total:,} steps, "
                "then its answer"
            )
            self.finish(now, note)

    def finish(self, now, note):
        self.current = list(self.solution)
        self.note = note
        self.phase = "done"
        self.board.celebrate(now)

    def animating(self, now):
        busy = self.phase in ("solving", "recording", "replay")
        ghosts = any(now < start + self.GHOST_TIME for _, start in self.ghosts)
        return (
            super().animating(now)
            or busy
            or ghosts
            or self.result_pill.animating(now)
        )

    def draw(self, surface, now):
        title = f"Solver on {self.n} x {self.n}"
        if self.phase == "solving":
            pills = [
                (
                    self.progress_pill,
                    f"Solving...  {now - self.started:.1f} s",
                    TEAL,
                )
            ]
        elif self.phase == "recording":
            pills = [
                (self.result_pill, *self.result),
                (self.progress_pill, "Recording steps...", TEAL),
            ]
        elif self.steps is not None and self.phase in ("replay", "done"):
            pills = [
                (self.result_pill, *self.result),
                (
                    self.step_pill,
                    f"Step {self.applied:,} / {len(self.steps):,}",
                    PURPLE,
                ),
                (
                    self.backtrack_pill,
                    f"Backtracks {self.backtracks:,}",
                    CORAL,
                ),
            ]
        else:
            pills = [(self.result_pill, *self.result)]

        left = self.draw_header(now, title, pills)
        if self.phase in ("solving", "recording"):
            spinner = pygame.Rect(0, 0, 26, 26)
            spinner.center = (left - 24, 90)
            angle = now * 7
            pygame.draw.arc(surface, TEAL, spinner, angle, angle + 4.2, 4)

        queens = [(r, c) for r, c in enumerate(self.current) if c != -1]
        crosses = self.covered(queens) if self.phase == "replay" else ()
        self.board.draw(surface, now, queens, crosses)
        self.draw_ghosts(surface, now)

        can_replay = self.phase == "done" and bool(self.steps)
        self.replay_button.color = PURPLE if can_replay else SLATE
        super().draw(surface, now)

        self.draw_hint(
            now,
            {
                "solving": "Some random boards take the solver a while. "
                "N skips to a new level.",
                "recording": "Solving again while recording every step "
                "for the replay...",
                "replay": "Every queen the solver placed and took back, "
                f"squeezed into {self.REPLAY_TIME:g} seconds",
                "done": self.note
                or (
                    "R replays the solver's steps.  N for a new level."
                    if can_replay
                    else ""
                ),
                "failed": "N for a new level",
            }[self.phase],
        )

    def draw_ghosts(self, surface, now):
        for (r, c), start in self.ghosts:
            t = progress(start, self.GHOST_TIME, now)
            if t < 1:
                center, size = self.board.cell_rect(
                    r, c
                ).center, self.board.cell * (1 - 0.6 * t)
                draw_crown(
                    surface,
                    center,
                    size,
                    CLASH,
                    shadow=(255, 255, 255),
                    shadow_scale=1.18,
                )

    def leave(self):
        if self.process is None:
            return

        if self.process.is_alive():
            self.process.terminate()
        self.process.join()
        self.conn.close()


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Colored Queens")

        self.surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
        self.background = self.build_background()

        self.small_font = load_font(17, bold=False)
        self.font = load_font(20, bold=False)
        self.pill_font = load_font(18)
        self.button_font = load_font(22)
        self.title_font = load_font(40)
        self.panel_font = load_font(56)
        self.number_font = load_font(76)
        self.hero_font = load_font(104)

        self.last_size = 8
        self.auto_x = False
        self.hand_cursor = False
        self.screen = None
        self.running = True
        self.show(MenuScreen(self))

    @staticmethod
    def build_background():
        background = vertical_gradient(
            (WIDTH, HEIGHT), (255, 243, 226), (236, 228, 255)
        )

        for (x, y), radius, color in (
            ((70, 90), 190, CORAL),
            ((670, 180), 150, YELLOW),
            ((60, 700), 170, TEAL),
            ((680, 780), 210, PURPLE),
        ):
            blob = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for i in range(8):
                pygame.draw.circle(
                    blob, (*color, 9), (radius, radius), radius * (1 - i * 0.1)
                )
            background.blit(blob, (x - radius, y - radius))

        return background.convert()

    def show(self, screen):
        if self.screen is not None:
            self.screen.leave()
        screen.started = time.monotonic()
        self.screen = screen
        screen.enter()

    def quit(self):
        self.running = False

    def text(self, message, center_y, font=None, color=TEXT, alpha=255):
        if message:
            rendered = (font or self.font).render(message, True, color)
            blit_scaled(
                self.surface, rendered, (WIDTH // 2, center_y), 1, alpha
            )

    def update_cursor(self):
        wanted = self.screen.clickable(pygame.mouse.get_pos())
        if wanted != self.hand_cursor:
            self.hand_cursor = wanted
            try:
                pygame.mouse.set_cursor(
                    pygame.SYSTEM_CURSOR_HAND
                    if wanted
                    else pygame.SYSTEM_CURSOR_ARROW
                )
            except pygame.error:
                pass

    def run(self):
        clock = pygame.time.Clock()

        try:
            while self.running:
                now = time.monotonic()
                self.screen.update(now)
                if not self.running:
                    break

                self.surface.blit(self.background, (0, 0))
                self.screen.draw(self.surface, now)
                self.update_cursor()
                pygame.display.flip()

                self.dispatch(self.next_events(clock))
        finally:
            self.screen.leave()
            pygame.quit()

    def next_events(self, clock):
        if self.screen.animating(time.monotonic()):
            clock.tick(FPS)
            return pygame.event.get()

        return [pygame.event.wait(), *pygame.event.get()]

    def dispatch(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.quit()
            elif self.running:
                self.screen.handle(event)


def run():
    App().run()
