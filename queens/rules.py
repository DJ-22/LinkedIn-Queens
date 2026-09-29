def touching(a, b):
    (r1, c1), (r2, c2) = a, b
    return a != b and abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1


def neighbors(r, c, n):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            if (dr or dc) and 0 <= rr < n and 0 <= cc < n:
                yield rr, cc


def conflicts(grid, a, b):
    (r1, c1), (r2, c2) = a, b
    return (
        r1 == r2 or c1 == c2 or grid[r1][c1] == grid[r2][c2] or touching(a, b)
    )


def covered_cells(grid, queens):
    n = len(grid)
    cells = [(r, c) for r in range(n) for c in range(n)]
    return {
        cell
        for queen in queens
        for cell in cells
        if conflicts(grid, queen, cell)
    } - set(queens)
