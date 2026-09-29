import random

from queens.rules import touching


def place_queens(n, rng):
    cols = []
    used = set()

    def backtrack(r):
        if r == n:
            return True

        options = [
            c
            for c in range(n)
            if c not in used
            and (r == 0 or not touching((r - 1, cols[-1]), (r, c)))
        ]
        rng.shuffle(options)

        for c in options:
            cols.append(c)
            used.add(c)

            if backtrack(r + 1):
                return True

            cols.pop()
            used.remove(c)

        return False

    if not backtrack(0):
        raise ValueError(f"A {n}x{n} board has no valid queen placement")

    return cols


def grow_regions(n, queens, rng):
    region = [[None] * n for _ in range(n)]
    frontier = []

    for r, c in enumerate(queens):
        region[r][c] = r
        frontier.append((r, c))

    while frontier:
        i = rng.randrange(len(frontier))
        r, c = frontier[i]
        open_cells = [
            (rr, cc)
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            if 0 <= rr < n and 0 <= cc < n and region[rr][cc] is None
        ]

        if not open_cells:
            frontier[i] = frontier[-1]
            frontier.pop()
            continue

        rr, cc = rng.choice(open_cells)
        region[rr][cc] = region[r][c]
        frontier.append((rr, cc))

    return region


def generate_level(n, color_names, rng=random):
    if len(color_names) < n:
        raise ValueError(
            f"A {n}x{n} board needs {n} colors "
            f"but only {len(color_names)} are available"
        )

    queens = place_queens(n, rng)
    region = grow_regions(n, queens, rng)
    colors = rng.sample(color_names, n)

    return [[colors[i] for i in row] for row in region]
