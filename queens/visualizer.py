import math

import pygame

from queens.effects import ease_out_back, lighten, progress, soft_shadow

THIN_LINE = (70, 70, 70)
THICK_LINE = (25, 20, 40)
CLASH = (230, 40, 60)

CROWN = (
    (0.2, 0.74),
    (0.2, 0.36),
    (0.36, 0.54),
    (0.5, 0.26),
    (0.64, 0.54),
    (0.8, 0.36),
    (0.8, 0.74),
)
CROWN_TIPS = ((0.2, 0.34), (0.5, 0.24), (0.8, 0.34))

INTRO_SPREAD = 0.45
CELL_POP = 0.35
MARK_POP = 0.28
RIPPLE_STEP = 0.035
SHAKE_TIME = 0.45
WAVE_SPREAD, WAVE_TIME = 0.6, 0.5
HOP_STEP, HOP_TIME = 0.07, 0.45


def draw_crown(
    surface,
    center,
    size,
    color,
    shadow=None,
    shadow_offset=0,
    shadow_scale=1.0,
):
    if shadow is not None:
        draw_crown(
            surface,
            (center[0], center[1] + shadow_offset),
            size * shadow_scale,
            shadow,
        )

    cx, cy = center
    pygame.draw.polygon(
        surface,
        color,
        [(cx + (fx - 0.5) * size, cy + (fy - 0.5) * size) for fx, fy in CROWN],
    )
    for fx, fy in CROWN_TIPS:
        pygame.draw.circle(
            surface,
            color,
            (cx + (fx - 0.5) * size, cy + (fy - 0.5) * size),
            max(1, size * 0.055),
        )


def contrast(rgb):
    r, g, b = rgb
    return (
        (0, 0, 0)
        if 0.299 * r + 0.587 * g + 0.114 * b > 128
        else (255, 255, 255)
    )


class Board:

    def __init__(self, grid, colors, center_x, top, max_px, max_cell=80):
        self.grid = grid
        self.colors = colors
        self.n = len(grid)
        self.cell = min(max_px // self.n, max_cell)
        size = self.cell * self.n
        self.rect = pygame.Rect(center_x - size // 2, top, size, size)

        self.card = self.rect.inflate(28, 28)
        self.card_shadow = soft_shadow(self.card.size, 22, alpha=70, spread=10)
        self.shown_at = None
        self.appear = {}
        self.ripple_from = None
        self.celebrate_at = None

    def cell_rect(self, r, c):
        return pygame.Rect(
            self.rect.x + c * self.cell,
            self.rect.y + r * self.cell,
            self.cell,
            self.cell,
        )

    def cell_at(self, pos):
        if not self.rect.collidepoint(pos):
            return None

        return (pos[1] - self.rect.y) // self.cell, (
            pos[0] - self.rect.x
        ) // self.cell

    def celebrate(self, now):
        self.celebrate_at = now

    def ready_at(self, now):
        return (
            (now if self.shown_at is None else self.shown_at)
            + INTRO_SPREAD
            + CELL_POP
        )

    def _celebration_end(self):
        return self.celebrate_at + max(
            WAVE_SPREAD + WAVE_TIME,
            WAVE_SPREAD * 0.3 + self.n * HOP_STEP + HOP_TIME,
        )

    def animating(self, now):
        if self.shown_at is None or now < self.ready_at(now):
            return True
        if self.celebrate_at is not None and now < self._celebration_end():
            return True

        return any(
            now < start + (SHAKE_TIME if kind == "clash" else MARK_POP)
            for (kind, _), start in self.appear.items()
        )

    def _track(self, now, queens, crosses, clashes):
        current = {("queen", cell) for cell in queens} | {
            ("cross", cell) for cell in crosses
        }
        current |= {("clash", cell) for cell in clashes}

        for key in current - self.appear.keys():
            delay = 0
            if key[0] == "cross" and self.ripple_from is not None:
                (r, c), (rr, cc) = key[1], self.ripple_from
                delay = max(abs(r - rr), abs(c - cc)) * RIPPLE_STEP
            self.appear[key] = now + delay

        for key in self.appear.keys() - current:
            del self.appear[key]

        self.ripple_from = None

    def draw(self, surface, now, queens=(), crosses=(), clashes=()):
        if self.shown_at is None:
            self.shown_at = now
        self._track(now, queens, crosses, clashes)

        surface.blit(
            self.card_shadow,
            self.card_shadow.get_rect(
                center=(self.card.centerx, self.card.centery + 6)
            ),
        )
        pygame.draw.rect(surface, (255, 255, 255), self.card, border_radius=18)

        for r in range(self.n):
            for c in range(self.n):
                self._draw_cell(surface, now, r, c)

        if now >= self.ready_at(now):
            self._draw_lines(surface)

        for cell in crosses:
            self._draw_cross(surface, now, *cell)

        hop_order = {cell: i for i, cell in enumerate(sorted(queens))}
        for cell in queens:
            self._draw_queen(
                surface,
                now,
                *cell,
                clashing=cell in clashes,
                hop_index=hop_order[cell],
            )

    def _draw_cell(self, surface, now, r, c):
        color = self.colors[self.grid[r][c]]
        diagonal = (r + c) / max(1, 2 * (self.n - 1))

        if self.celebrate_at is not None:
            flash = progress(
                self.celebrate_at + diagonal * WAVE_SPREAD, WAVE_TIME, now
            )
            color = lighten(color, math.sin(math.pi * flash) * 0.6)

        rect = self.cell_rect(r, c)
        intro = progress(
            self.shown_at + diagonal * INTRO_SPREAD, CELL_POP, now
        )
        if intro >= 1:
            pygame.draw.rect(surface, color, rect)
        elif intro > 0:
            size = self.cell * ease_out_back(intro)
            pop = pygame.Rect(0, 0, size, size)
            pop.center = rect.center
            pygame.draw.rect(
                surface,
                color,
                pop,
                border_radius=round(self.cell * 0.3 * (1 - intro)),
            )

    def _draw_lines(self, surface):
        n, s, left, top = self.n, self.cell, self.rect.x, self.rect.y

        for i in range(1, n):
            pygame.draw.line(
                surface,
                THIN_LINE,
                (left + i * s, top),
                (left + i * s, self.rect.bottom - 1),
            )
            pygame.draw.line(
                surface,
                THIN_LINE,
                (left, top + i * s),
                (self.rect.right - 1, top + i * s),
            )

        for r in range(n):
            for c in range(n):
                x, y = left + c * s, top + r * s
                if c + 1 < n and self.grid[r][c] != self.grid[r][c + 1]:
                    pygame.draw.line(
                        surface, THICK_LINE, (x + s, y), (x + s, y + s), 3
                    )
                if r + 1 < n and self.grid[r][c] != self.grid[r + 1][c]:
                    pygame.draw.line(
                        surface, THICK_LINE, (x, y + s), (x + s, y + s), 3
                    )

        pygame.draw.rect(
            surface, THICK_LINE, self.rect.inflate(4, 4), 3, border_radius=3
        )

    def _draw_cross(self, surface, now, r, c):
        t = progress(self.appear.get(("cross", (r, c))), MARK_POP, now)
        if t <= 0:
            return

        half = self.cell * 0.2 * ease_out_back(t)
        x, y = self.cell_rect(r, c).center
        color = contrast(self.colors[self.grid[r][c]])
        width = max(2, self.cell // 18)
        pygame.draw.line(
            surface, color, (x - half, y - half), (x + half, y + half), width
        )
        pygame.draw.line(
            surface, color, (x + half, y - half), (x - half, y + half), width
        )

    def _draw_queen(self, surface, now, r, c, clashing, hop_index):
        rect = self.cell_rect(r, c)
        scale = ease_out_back(
            progress(self.appear.get(("queen", (r, c))), MARK_POP, now)
        )
        dx = dy = 0

        if clashing:
            shake = progress(
                self.appear.get(("clash", (r, c))), SHAKE_TIME, now
            )
            dx = math.sin(shake * math.pi * 6) * (1 - shake) * self.cell * 0.12

            pygame.draw.rect(surface, (255, 255, 255), rect.inflate(-2, -2), 3)
            pygame.draw.rect(surface, CLASH, rect.inflate(-6, -6), 3)

        if self.celebrate_at is not None:
            hop = progress(
                self.celebrate_at + WAVE_SPREAD * 0.3 + hop_index * HOP_STEP,
                HOP_TIME,
                now,
            )
            dy = -math.sin(math.pi * hop) * self.cell * 0.3

        color = CLASH if clashing else contrast(self.colors[self.grid[r][c]])
        draw_crown(
            surface,
            (rect.centerx + dx, rect.centery + dy),
            self.cell * scale,
            color,
        )
