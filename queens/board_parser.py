def parse_regions(grid: list) -> tuple:
    regions = {}

    for r, row in enumerate(grid):
        for c, name in enumerate(row):
            if name not in regions:
                regions[name] = []

            regions[name].append((r, c))

    return regions, len(grid)
