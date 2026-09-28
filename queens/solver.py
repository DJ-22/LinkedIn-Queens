def neighbors(r, c, n):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            if (dr or dc) and 0 <= rr < n and 0 <= cc < n:
                yield rr, cc


def solve(n, regions):
    region_map = {}
    for name, cells in regions.items():
        for (r, c) in cells:
            region_map[(r, c)] = name

    all_cells = {(r, c) for r in range(n) for c in range(n)}
    if len(regions) != n:
        raise ValueError(f"Board has {len(regions)} regions; a {n}x{n} board needs exactly {n}")
    if region_map.keys() != all_cells or sum(map(len, regions.values())) != n * n:
        raise ValueError("Regions must cover every cell of the board exactly once")

    region_used = set()
    col_used = set()
    blocked = set()
    queens = [-1] * n

    def is_valid(r, c):
        reg = region_map[(r, c)]

        if c in col_used:
            return False
        if reg in region_used:
            return False
        if (r, c) in blocked:
            return False

        return True

    def valid_columns(r):
        return [c for c in range(n) if is_valid(r, c)]

    def count_constraints(r, c):
        # Open cells in other empty rows that a queen at (r, c) would eliminate
        # via its region, its column, or adjacency (a set, so no cell counts twice)
        eliminated = {cell for cell in regions[region_map[(r, c)]] if cell[0] != r}

        for other_row in range(n):
            if other_row == r:
                continue

            cols = (c - 1, c, c + 1) if abs(other_row - r) == 1 else (c,)
            eliminated.update((other_row, other_col) for other_col in cols if 0 <= other_col < n)

        return sum(1 for (rr, cc) in eliminated if queens[rr] == -1 and is_valid(rr, cc))

    def get_most_constrained_row():
        # Empty row with the fewest open columns; returns no columns when the
        # state is a dead end (some row or unused region has no open cell)
        best_row = -1
        best_cols = []
        min_opt = float('inf')
        open_regions = set()

        for r in range(n):
            if queens[r] != -1:
                continue

            cols = valid_columns(r)
            opts = len(cols)
            if opts == 0:
                return r, cols
            open_regions.update(region_map[(r, c)] for c in cols)
            if opts < min_opt:
                min_opt = opts
                best_row = r
                best_cols = cols

        # An unused region with no open cell left can never get its queen: dead end
        if len(open_regions) + len(region_used) < n:
            return best_row, []

        return best_row, best_cols

    def backtrack():
        r, cols = get_most_constrained_row()
        if r == -1:
            return True

        col_valid = [(c, count_constraints(r, c)) for c in cols]

        col_valid.sort(key=lambda x: x[1])
        for c, _ in col_valid:
            reg = region_map[(r, c)]
            queens[r] = c
            col_used.add(c)
            region_used.add(reg)
            blocked_add = [cell for cell in neighbors(r, c, n) if cell not in blocked]
            blocked.update(blocked_add)

            if backtrack():
                return True

            queens[r] = -1
            col_used.remove(c)
            region_used.remove(reg)

            for cell in blocked_add:
                blocked.discard(cell)

        return False

    if backtrack():
        return [[queens[r] == c for c in range(n)] for r in range(n)]

    return None
