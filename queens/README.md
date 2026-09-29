# queens

The solver, the level generator, the replay recorder and the pygame app.

| Module            | What it does                                                     |
| ----------------- | ---------------------------------------------------------------- |
| `solver.py`       | Solves a board with backtracking search                          |
| `rules.py`        | The Queens rules, shared by the solver, generator and app        |
| `board_parser.py` | Turns a grid of colours into the regions the solver takes        |
| `generator.py`    | Generates random levels that are guaranteed to be solvable       |
| `replay.py`       | Records every step the solver takes, for the app's replay        |
| `app.py`          | The pygame app: menu, size picker, play screen and solver screen |
| `visualizer.py`   | Draws the board, queens and ✕ marks, with their animations       |
| `widgets.py`      | Animated buttons and status pills                                |
| `effects.py`      | Easing curves, colour helpers, gradients and confetti            |
| `config.py`       | The 20 region colours used by generated levels                   |

## Board representation

A board starts as a grid: a list of rows, each a list of region colour names. `parse_regions(grid)` turns it into what the solver works with:

- `regions`: a dict from each region's name to the list of its `(row, column)` cells
- `n`: the board size

```python
regions, n = parse_regions(grid)
solution = solve(n, regions)  # n x n list of booleans, or None if unsolvable
```

## The solver (`solver.py`)

`solve(n, regions)` first checks the input: there must be exactly n regions, and together they must cover every cell exactly once. Otherwise it raises `ValueError`. It then runs a depth-first backtracking search, kept in a `Search` object.

### State

| Field         | Meaning                                                       |
| ------------- | ------------------------------------------------------------- |
| `queens`      | The column of the queen in each row, or `-1` for an empty row |
| `col_used`    | Columns that already hold a queen                             |
| `region_used` | Regions that already hold a queen                             |
| `blocked`     | Cells touching a placed queen                                 |

A cell is **open** when its row is empty, its column and region are unused, and it isn't blocked. Rows are handled by the `queens` list itself: each row gets at most one queen.

### Each step

`backtrack()` asks `most_constrained_cells()` which cells to try next. That method works in five stages:

1. **Collect the open cells** of every empty row. If some empty row has no open cell, the branch is a dead end.
2. **Group the open cells** three ways: by row, by column and by region. Every empty row, unused column and unused region still needs exactly one queen.
3. **Check that nothing is stranded.** If an unused column or region has no open cell left, it can never get its queen, so the branch is a dead end.
4. **Check that everything can be satisfied at once.** Each group needs its own queen, so three pairings must all be possible:

   - every unused region to a different empty row
   - every unused region to a different unused column
   - every empty row to a different unused column

   `has_matching()` checks each pairing with a bipartite matching built from augmenting paths. This is Hall's condition from graph theory. It catches dead ends that step 3 can't see. For example, three regions whose open cells all sit in the same two rows can't all get a queen, even though each one still has open cells.
5. **Pick the smallest group.** The row, column or region with the fewest open cells must hold exactly one of them, so trying each of its cells covers every possibility with the fewest branches. A group with a single open cell is a forced move.

If every row already has its queen, `most_constrained_cells()` returns `None` and the search has found a solution.

### Trying cells

The chosen cells are tried in order of `count_constraints()`: how many open cells in other empty rows a queen there would rule out, through its region, its column, or by touching the rows directly above and below. Cells that rule out the least go first, because they leave the most room for the queens still to be placed.

Placing a queen writes its column into `queens`, marks its column and region as used, and blocks the cells around it. Only the newly blocked cells are remembered, so the move can be undone exactly. If the recursive search fails, the move is undone and the next cell is tried. If no cell works, the search backtracks to the previous step.

### Speed

Measured on 250 random 10×10 boards and 250 random 20×20 boards, made by `generate_level` with seeds 0 to 249, on an Intel Core i7-14700HX with Python 3.13. Every board was solved correctly. Times cover `solve()` alone.

| Result                             | 10×10     | 20×20     |
| ---------------------------------- | --------- | --------- |
| Median solve time                  | 0.49 ms   | 3.09 ms   |
| Mean solve time                    | 0.53 ms   | 3.46 ms   |
| 90th percentile                    | 0.67 ms   | 3.52 ms   |
| 99th percentile                    | 0.91 ms   | 4.53 ms   |
| Slowest board                      | 1.20 ms   | 83.8 ms   |
| Boards solved with no backtracking | 147 (59%) | 109 (44%) |
| Boards with at most 1 backtrack    | 188 (75%) | 147 (59%) |
| Boards with at most 3 backtracks   | 224 (90%) | 209 (84%) |
| Most backtracks on one board       | 20        | 1,715     |

The slowest 20×20 board is seed 65. It needs 1,715 backtracks and takes about 84 ms; the next-worst 20×20 board needs only 12. For comparison, an earlier version that only branched on rows took 5 s, 23 s and over 30 s on three boards that now solve in milliseconds. Those boards are kept as a test. Steps 4 and 5 made the difference.

## The rules (`rules.py`)

| Function                      | Returns                                                                             |
| ----------------------------- | ----------------------------------------------------------------------------------- |
| `touching(a, b)`              | Whether two different cells are neighbours, diagonals included                      |
| `neighbors(r, c, n)`          | Every cell touching `(r, c)` on an n×n board                                        |
| `conflicts(grid, a, b)`       | Whether queens on `a` and `b` break a rule: same row, column or region, or touching |
| `covered_cells(grid, queens)` | Every empty cell the given queens rule out                                          |

The solver uses `neighbors` to block cells, the generator uses `touching`, and the app uses `conflicts` to spot clashing queens and `covered_cells` for auto ✕ marks and the replay.

## The level generator (`generator.py`)

`generate_level(n, color_names, rng)` builds a level in two stages, so every level has at least one solution. It may have more than one.

1. **Place the queens.** `place_queens()` picks a column for each row with a randomised depth-first search: no two rows share a column, and queens in neighbouring rows don't touch.
2. **Grow the regions.** `grow_regions()` makes each queen the seed of its own region. It then repeatedly picks a random cell on the edge of some region and spreads that region into a random empty neighbour (up, down, left or right), until every cell belongs to a region. Each region stays connected and holds exactly one queen, so the placement from stage 1 is a valid solution.

Finally each region gets a different colour from `color_names`. Passing the same `random.Random(seed)` always produces the same level.

## The replay recorder (`replay.py`)

The "Watch the solver" screen shows every queen the solver placed and took back, without the solver knowing it's being watched.

- `record_steps(n, regions)` solves the board again while `sys.monitoring` (Python 3.12+) reports every line `Search.backtrack()` runs. On each line it compares the search's `queens` list with the last copy it saw, and logs each difference as a step: a queen placed or removed at a row and column.
- Each step is packed into one integer, `(row << 6) | (column << 1) | placed`. The column gets 5 bits, so recording refuses boards wider than 32.
- Recording stops early after 1,000,000 steps or 10 seconds and reports that it's incomplete. The app then replays the recorded part and shows the answer.
- `solve_and_record(grid, conn)` runs in a separate process. It times a plain solve first and sends `("solved", solution, seconds)`, then records and sends `("steps", steps, complete)`. If recording isn't possible, it sends `("no-steps", reason)` instead. Timing the solve without the watcher keeps the reported time accurate.

## The app (`app.py`)

`App` owns the window and swaps between screens: the menu, the size picker, the play screen and the solver screen.

- The main loop redraws at 60 frames per second only while something is animating, and otherwise sleeps until the next event, so the app uses almost no CPU while idle.
- The solver screen runs `solve_and_record` in a child process, so a slow solve never freezes the window, and **N** or **Esc** can abandon it at any time.
- The replay always takes 5 seconds. On long recordings, each frame jumps ahead to wherever the solver had got to by that point in the replay.
- Auto ✕ marks are recomputed from the queens on the board rather than stored. That's how a ✕ covered by several queens stays until the last of them is removed, while your own ✕ marks are never touched.
