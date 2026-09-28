import time

from queens.config import BOARD, COLOR_MAP, COLORS
from queens.board_parser import parse_regions, build_grid
from queens.solver import solve
from queens.visualizer import visualize


def main():
    # Regions are keyed by color name, so two characters sharing a color would merge
    colors = list(COLOR_MAP.values())
    duplicates = sorted({color for color in colors if colors.count(color) > 1})
    if duplicates:
        raise ValueError(f"Color map assigns {duplicates} to more than one character")

    # The visualizer draws grid lines and queens in black
    missing = (set(colors) | {"black"}) - COLORS.keys()
    if missing:
        raise ValueError(f"Colors {sorted(missing)} are needed but have no RGB value in COLORS")

    grid = build_grid(BOARD, COLOR_MAP)
    regions, n = parse_regions(grid)

    print(f"Solving {n}x{n} board with {len(regions)} regions...")
    start = time.perf_counter()
    sol = solve(n, regions)
    elapsed = time.perf_counter() - start

    if sol:
        print(f"Solution found in {elapsed:.5f} seconds")
        visualize(grid, sol, COLORS, elapsed)
    else:
        print("No solution found!")


if __name__ == "__main__":
    main()
