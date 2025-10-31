import time
from config import BOARD, COLOR_MAP, COLORS
from parser import parseRegions, buildGrid
from solver import solve
from visualizer import visualize

regions, n = parseRegions(BOARD, COLOR_MAP)
    
print(f"Solving {n}x{n} board with {len(regions)} regions...")
start = time.time()
sol = solve(n, regions)
elapsed = time.time() - start

if sol:
    print(f"Solution found in {elapsed:.5f} seconds")
    grid = buildGrid(BOARD, COLOR_MAP)
    visualize(grid, sol, COLORS, elapsed)
else:
    print("No solution found!")
