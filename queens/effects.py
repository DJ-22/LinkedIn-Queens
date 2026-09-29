import math
import random

import pygame


def progress(start, duration, now):
    if start is None:
        return 1.0

    return min(1.0, max(0.0, (now - start) / duration))


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_out_back(t, overshoot=1.7):
    t -= 1
    return 1 + (overshoot + 1) * t**3 + overshoot * t**2


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def lighten(rgb, t):
    return mix(rgb, (255, 255, 255), t)


def darken(rgb, t):
    return mix(rgb, (0, 0, 0), t)


def vertical_gradient(size, top, bottom):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    width, height = size

    for y in range(height):
        pygame.draw.line(
            surface,
            (*mix(top, bottom, y / max(1, height - 1)), 255),
            (0, y),
            (width, y),
        )

    return surface


def rounded(surface, radius):
    mask = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(
        mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius
    )
    surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return surface


def soft_shadow(size, radius, alpha=45, spread=6):
    width, height = size
    surface = pygame.Surface(
        (width + 2 * spread, height + 2 * spread), pygame.SRCALPHA
    )

    for i in range(spread, 0, -1):
        rect = pygame.Rect(
            spread - i, spread - i, width + 2 * i, height + 2 * i
        )
        pygame.draw.rect(
            surface,
            (40, 20, 70, alpha // spread),
            rect,
            border_radius=radius + i,
        )

    return surface


def blit_scaled(surface, image, center, scale, alpha=255):
    if scale <= 0.02 or alpha <= 0:
        return

    if abs(scale - 1) > 0.001:
        size = (
            max(1, round(image.get_width() * scale)),
            max(1, round(image.get_height() * scale)),
        )
        image = pygame.transform.smoothscale(image, size)

    if alpha < 255:
        image = image.copy()
        image.set_alpha(alpha)

    surface.blit(image, image.get_rect(center=center))


class Confetti:

    GRAVITY = 1100
    TERMINAL = 230

    def __init__(self, cannons, colors, now, per_cannon=90):
        self.last = now
        self.pieces = []

        for x, y, direction in cannons:
            for _ in range(per_cannon):
                angle = math.radians(random.uniform(58, 84))
                speed = random.uniform(750, 1250)
                self.pieces.append(
                    {
                        "x": x,
                        "y": y,
                        "vx": math.cos(angle) * speed * direction,
                        "vy": -math.sin(angle) * speed,
                        "w": random.uniform(7, 12),
                        "h": random.uniform(10, 16),
                        "color": random.choice(colors),
                        "phase": random.uniform(0, math.tau),
                        "spin": random.uniform(5, 12),
                    }
                )

    def alive(self):
        return bool(self.pieces)

    def draw(self, surface, now):
        dt = min(now - self.last, 1 / 30)
        self.last = now
        bottom = surface.get_height() + 30

        for p in self.pieces:
            p["vx"] *= 1 - 1.6 * dt
            p["vy"] = min(p["vy"] + self.GRAVITY * dt, self.TERMINAL)
            p["phase"] += p["spin"] * dt
            p["x"] += (p["vx"] + math.sin(p["phase"] * 0.6) * 40) * dt
            p["y"] += p["vy"] * dt

            width = max(1.5, abs(math.cos(p["phase"])) * p["w"])
            pygame.draw.rect(
                surface,
                p["color"],
                (p["x"] - width / 2, p["y"] - p["h"] / 2, width, p["h"]),
            )

        self.pieces = [p for p in self.pieces if p["y"] < bottom]
