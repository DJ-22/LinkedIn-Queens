import math
import time

import pygame

from queens.effects import (
    blit_scaled,
    darken,
    ease_out_back,
    lighten,
    progress,
)

PRESS_TIME = 0.12
ENTRANCE = 0.45


def scaled_rect(rect, scale):
    result = pygame.Rect(
        0, 0, round(rect.width * scale), round(rect.height * scale)
    )
    result.center = rect.center
    return result


class Button:

    def __init__(
        self, label, rect, action, keys, color, delay=0.0, instant=False
    ):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.action = action
        self.keys = keys
        self.color = color
        self.delay = delay
        self.instant = instant
        self.hover = 0.0
        self.pressed_at = None
        self.pending = False
        self.last_draw = None

    def hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def handle(self, event):
        clicked = (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )
        if (
            not (
                clicked
                or (event.type == pygame.KEYDOWN and event.key in self.keys)
            )
            or self.pending
        ):
            return False

        self.pressed_at = time.monotonic()
        if self.instant:
            self.action()
        else:
            self.pending = True
        return True

    def update(self, now):
        if self.pending and now - self.pressed_at >= PRESS_TIME:
            self.pending = False
            self.action()

    def animating(self, now, started):
        target = 1.0 if self.hovered() else 0.0
        return (
            now < started + self.delay + ENTRANCE
            or self.pending
            or (
                self.pressed_at is not None
                and now < self.pressed_at + 2 * PRESS_TIME
            )
            or abs(self.hover - target) > 0.01
        )

    def draw(self, surface, font, now, started):
        target = 1.0 if self.hovered() else 0.0
        dt = 0 if self.last_draw is None else now - self.last_draw
        self.last_draw = now
        self.hover += (target - self.hover) * min(1.0, dt * 14)
        if abs(self.hover - target) <= 0.01:
            self.hover = target

        entrance = progress(started + self.delay, ENTRANCE, now)
        if entrance <= 0:
            return

        scale = ease_out_back(entrance)
        squash = (
            math.sin(math.pi * progress(self.pressed_at, 2 * PRESS_TIME, now))
            if self.pressed_at
            else 0
        )
        face = scaled_rect(
            self.rect.move(0, round(-3 * self.hover + 5 * squash)), scale
        )
        base = scaled_rect(self.rect.move(0, 6), scale)
        radius = face.height // 2

        pygame.draw.rect(
            surface, darken(self.color, 0.3), base, border_radius=radius
        )
        pygame.draw.rect(
            surface,
            lighten(self.color, 0.14 * self.hover),
            face,
            border_radius=radius,
        )
        shine = pygame.Rect(
            face.x + radius,
            face.y + 5,
            max(0, face.width - 2 * radius),
            max(1, face.height // 9),
        )
        pygame.draw.rect(
            surface,
            lighten(self.color, 0.35),
            shine,
            border_radius=shine.height,
        )

        blit_scaled(
            surface,
            font.render(self.label, True, (255, 255, 255)),
            face.center,
            scale,
        )


class Pill:

    HEIGHT = 34

    def __init__(self, bump=True):
        self.bump = bump
        self.text = None
        self.changed_at = None

    def width(self, font, text):
        return font.size(text)[0] + 30

    def draw(self, surface, font, text, color, center, now, scale=1.0):
        if text != self.text:
            if self.text is not None and self.bump:
                self.changed_at = now
            self.text = text

        scale *= (
            1 + 0.18 * math.sin(math.pi * progress(self.changed_at, 0.3, now))
            if self.changed_at
            else 1
        )
        if scale <= 0.02:
            return

        width = self.width(font, text)
        rect = scaled_rect(
            pygame.Rect(
                center[0] - width // 2,
                center[1] - self.HEIGHT // 2,
                width,
                self.HEIGHT,
            ),
            scale,
        )
        pygame.draw.rect(
            surface,
            darken(color, 0.25),
            rect.move(0, 3),
            border_radius=rect.height // 2,
        )
        pygame.draw.rect(surface, color, rect, border_radius=rect.height // 2)
        blit_scaled(
            surface,
            font.render(text, True, (255, 255, 255)),
            rect.center,
            scale,
        )

    def animating(self, now):
        return self.changed_at is not None and now < self.changed_at + 0.3


def draw_pills(surface, font, now, center_x, y, items, scale=1.0, gap=12):
    widths = [pill.width(font, text) for pill, text, _ in items]
    left = x = center_x - (sum(widths) + gap * (len(items) - 1)) // 2

    for (pill, text, color), width in zip(items, widths):
        pill.draw(surface, font, text, color, (x + width // 2, y), now, scale)
        x += width + gap

    return left
