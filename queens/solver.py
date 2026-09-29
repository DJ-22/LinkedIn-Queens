from queens.rules import neighbors


def has_matching(groups):
    owner = {}

    def assign(group, seen):
        for target in groups[group]:
            if target not in seen:
                seen.add(target)
                if target not in owner or assign(owner[target], seen):
                    owner[target] = group
                    return True
        return False

    return all(assign(group, set()) for group in groups)


class Search:

    def __init__(self, n, regions, region_map):
        self.n = n
        self.regions = regions
        self.region_map = region_map
        self.region_used = set()
        self.col_used = set()
        self.blocked = set()
        self.queens = [-1] * n

    def is_valid(self, r, c):
        reg = self.region_map[(r, c)]

        if c in self.col_used:
            return False
        if reg in self.region_used:
            return False
        if (r, c) in self.blocked:
            return False

        return True

    def valid_columns(self, r):
        return [c for c in range(self.n) if self.is_valid(r, c)]

    def count_constraints(self, r, c):
        n = self.n
        eliminated = {
            cell
            for cell in self.regions[self.region_map[(r, c)]]
            if cell[0] != r
        }

        for other_row in range(n):
            if other_row == r:
                continue

            cols = (c - 1, c, c + 1) if abs(other_row - r) == 1 else (c,)
            eliminated.update(
                (other_row, other_col)
                for other_col in cols
                if 0 <= other_col < n
            )

        return sum(
            1
            for (rr, cc) in eliminated
            if self.queens[rr] == -1 and self.is_valid(rr, cc)
        )

    def most_constrained_cells(self):
        n = self.n
        by_row, by_col, by_region = {}, {}, {}

        for r in range(n):
            if self.queens[r] != -1:
                continue

            cols = self.valid_columns(r)
            if not cols:
                return []

            by_row[r] = [(r, c) for c in cols]
            for c in cols:
                by_col.setdefault(c, []).append((r, c))
                by_region.setdefault(self.region_map[(r, c)], []).append(
                    (r, c)
                )

        if not by_row:
            return None

        if (
            len(by_col) + len(self.col_used) < n
            or len(by_region) + len(self.region_used) < n
        ):
            return []

        if not (
            has_matching(
                {
                    reg: {r for r, _ in cells}
                    for reg, cells in by_region.items()
                }
            )
            and has_matching(
                {
                    reg: {c for _, c in cells}
                    for reg, cells in by_region.items()
                }
            )
            and has_matching(
                {r: {c for _, c in cells} for r, cells in by_row.items()}
            )
        ):
            return []

        return min(
            (*by_row.values(), *by_col.values(), *by_region.values()), key=len
        )

    def backtrack(self):
        cells = self.most_constrained_cells()
        if cells is None:
            return True

        cell_valid = [(r, c, self.count_constraints(r, c)) for r, c in cells]

        cell_valid.sort(key=lambda x: x[2])
        for r, c, _ in cell_valid:
            reg = self.region_map[(r, c)]
            self.queens[r] = c
            self.col_used.add(c)
            self.region_used.add(reg)
            blocked_add = [
                cell
                for cell in neighbors(r, c, self.n)
                if cell not in self.blocked
            ]
            self.blocked.update(blocked_add)

            if self.backtrack():
                return True

            self.queens[r] = -1
            self.col_used.remove(c)
            self.region_used.remove(reg)

            for cell in blocked_add:
                self.blocked.discard(cell)

        return False


def solve(n, regions):
    region_map = {}
    for name, cells in regions.items():
        for r, c in cells:
            region_map[(r, c)] = name

    all_cells = {(r, c) for r in range(n) for c in range(n)}
    if len(regions) != n:
        raise ValueError(
            f"Board has {len(regions)} regions; "
            f"a {n}x{n} board needs exactly {n}"
        )
    if (
        region_map.keys() != all_cells
        or sum(map(len, regions.values())) != n * n
    ):
        raise ValueError(
            "Regions must cover every cell of the board exactly once"
        )

    search = Search(n, regions, region_map)
    if search.backtrack():
        return [[search.queens[r] == c for c in range(n)] for r in range(n)]

    return None
