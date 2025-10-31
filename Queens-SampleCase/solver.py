def solve(n, regions):
    region_map = {}
    for name, cells in regions.items():
        for (r, c) in cells:
            region_map[(r, c)] = name

    reqd = {}
    for name in regions.keys():
        reqd[name] = 1

    col_used = set()
    blocked = set()
    queens = [-1] * n

    def isValid(r, c):
        reg = region_map[(r, c)]

        if c in col_used:
            return False
        if reqd[reg] == 0:
            return False
        if (r, c) in blocked:
            return False

        return True

    def countOptions(r):
        cnt = 0
        for c in range(n):
            if isValid(r, c):
                cnt += 1
        
        return cnt

    def countConstraints(r, c):
        cnt = 0

        for next_row in range(r + 1, n):
            if c not in col_used:
                next_reg = region_map[(next_row, c)]
                if reqd[next_reg] > 0 and (next_row, c) not in blocked:
                    cnt += 1

            for dc in (-1, 0, 1):
                next_col = c + dc
                if 0 <= next_col < n:
                    if (next_row, next_col) not in blocked:
                        next_reg = region_map[(next_row, next_col)]
                        if next_col not in col_used and reqd[next_reg] > 0:
                            cnt += 1

        return cnt

    def getMostConstrainedRow():
        best_row = -1
        min_opt = float('inf')

        for r in range(n):
            opts = countOptions(r)

            if queens[r] != -1:
                continue
            if opts == 0:
                return r
            if opts < min_opt:
                min_opt = opts
                best_row = r

        return best_row

    def backtrack(placed):
        r = getMostConstrainedRow()
        if r == -1:
            return True
        if placed == n:
            return True

        col_valid = []
        for c in range(n):
            if isValid(r, c):
                col_valid.append((c, countConstraints(r, c)))

        if not col_valid:
            return False

        col_valid.sort(key=lambda x: x[1])
        for c, _ in col_valid:
            reg = region_map[(r, c)]
            queens[r] = c
            col_used.add(c)
            reqd[reg] -= 1
            blocked_add = []

            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue

                    rr, cc = r + dr, c + dc
                    if 0 <= rr < n and 0 <= cc < n:
                        if (rr, cc) not in blocked:
                            blocked.add((rr, cc))
                            blocked_add.append((rr, cc))

            if backtrack(placed + 1):
                return True

            queens[r] = -1
            col_used.remove(c)
            reqd[reg] += 1

            for cell in blocked_add:
                blocked.discard(cell)

        return False

    if backtrack(0):
        sol = [[False] * n for _ in range(n)]

        for r in range(n):
            c = queens[r]
            sol[r][c] = True

        return sol
    else:
        return None
