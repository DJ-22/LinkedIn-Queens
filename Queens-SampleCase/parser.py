def parseRegions(board: str, color_map: dict) -> tuple:
    regions = {}
    rows = board.strip().split("\n")
    size = len(rows)

    for r, row in enumerate(rows):
        for c, key in enumerate(row):
            name = color_map[key]
            if name not in regions:
                regions[name] = []

            regions[name].append((r, c))

    return regions, size

def buildGrid(board: str, color_map: dict):
    rows = board.strip().split("\n")
    grid = []

    for r, row in enumerate(rows):
        grid.append([])

        for c, key in enumerate(row):
            grid[-1].append(color_map[key])

    return grid
