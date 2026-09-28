def parse_regions(grid: list) -> tuple:
    regions = {}

    for r, row in enumerate(grid):
        for c, name in enumerate(row):
            if name not in regions:
                regions[name] = []

            regions[name].append((r, c))

    return regions, len(grid)


def build_grid(board: str, color_map: dict):
    if not board.strip():
        raise ValueError("Board is empty")

    rows = board.strip().split("\n")
    grid = []

    for r, row in enumerate(rows):
        if len(row) != len(rows):
            raise ValueError(f"Row {r} has {len(row)} cells; a {len(rows)}-row board must be square")

        grid.append([])

        for c, key in enumerate(row):
            if key not in color_map:
                raise ValueError(f"Cell ({r}, {c}) has character {key!r}, which is not in the color map")

            grid[-1].append(color_map[key])

    return grid
