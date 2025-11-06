# LinkedIn-Queens

**LinkedIn-Queens** is a small, local Python solver for the [LinkedIn-Queens](https://www.linkedin.com/showcase/queens-game), style puzzle. It reads a sample board from `config.py`, runs a backtracking solver (`solver.py`) with a handful of search heuristics, and visualizes the result with `pygame` (`visualizer.py`).

> **Note:** This project does **not** interact with LinkedIn or any website. It solves only the puzzle data supplied locally in `config.py`.

---

## Table of Contents

1. [Quick start](#-quick-start)
2. [Project structure](#-project-structure)
3. [Important Files](#-important-files)
4. [Algorithm &amp; heuristics](#-algorithms-&-heuristics) ← *detailed*
5. [Example](#-example)
6. [Future improvements](#future-improvements)

---

## Quick Start

Requirements:

* Python 3.8+
* `pygame`

Install `pygame`:

<pre class="overflow-visible!" data-start="1114" data-end="1154"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>pip install -r requirements.txt
</span></span></code></div></div></pre>

Run the solver:

<pre class="overflow-visible!" data-start="1172" data-end="1243"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>git </span><span>clone</span><span> <this-repo-url>
</span><span>cd</span><span> LinkedIn-Queens
python main.py
</span></span></code></div></div></pre>

`main.py` loads the sample board (from `config.py`), runs the solver, prints the solve time and, if a solution is found, launches the `pygame` visualizer.

---

## Project Structure

<pre class="overflow-visible!" data-start="1430" data-end="1867"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre!"><span><span>LinkedIn-Queens/
├── Queens-SampleCase/     </span><span># example boards (if present)</span><span>
├── config.py              </span><span># sample BOARD string, color mapping and RGB palette</span><span>
├── parser.py              </span><span># parseRegions(), buildGrid()</span><span>
├── solver.py              </span><span># solve() — backtracking + heuristics</span><span>
├── visualizer.py          </span><span># pygame visualizer</span><span>
├── main.py                </span><span># entrypoint: parse -> solve -> visualize</span><span>
└── requirements.txt       </span><span># optional</span><span>
</span></span></code></div></div></pre>

---

## Important Files

* **`config.py`:** contains a multiline `BOARD` string and `COLOR_MAP`. The `BOARD` uses single characters per cell; `COLOR_MAP` maps those characters to human-readable region names (colors).
* **`parser.py`**
  * `parseRegions(board, color_map)` → returns `(regions, n)` where `regions` is a dict mapping region_name → list of `(r,c)` cells and `n` is board size.
  * `buildGrid(board, color_map)` → converts the board into a grid of color-names for visualization.
* **`solver.py`**
  * `solve(n, regions)` → attempts to find a solution and returns a `n x n` boolean grid with queens (or `None`).
* **`visualizer.py`**
  * Draws the colored board using `pygame` and overlays `"Q"` for queen positions.
* **`main.py`**
  * Calls `parseRegions`, runs `solve`, prints the elapsed time, and calls `visualize` if a solution is found.

---

## Algorithm & Heuristics

This project solves the puzzle using **recursive backtracking** with several practical heuristics and lightweight forward-checking. Below is a precise, implementation-accurate description of what the solver enforces and how it guides search.

### Problem Formulation

From the code in `solver.py`:

* The solver attempts to place exactly **one queen per row** (the `queens` array has length `n`, and the algorithm fills rows).
* The following constraints are enforced when placing a queen at cell `(r, c)`:
  1. **Column uniqueness:** no two queens share the same column. (tracked by `col_used` set)
  2. **Region requirement:** each color/region must contain exactly **one** queen. The solver initializes `reqd[region] = 1` for every region name and decrements it when a queen is placed in that region. A placement is invalid if `reqd[region] == 0`.
  3. **Blocked cells (local neighborhood):** when a queen is placed at `(r,c)`, the solver marks the 8 surrounding neighbours (one-cell king moves) as blocked (set `blocked`) and disallows future placements on those blocked cells. The solver does **not** implement full chess-style diagonal/ray attacks beyond column uniqueness and the immediate 8-cell neighborhood block.
* If all rows get filled respecting those constraints, the solver reports success and returns the boolean solution grid.

> Important: The code's notion of attack/conflict is a combination of "no same column" plus "no cell in the one-cell surrounding neighborhood". This is the exact behavior implemented (see `col_used` and `blocked`).

### Search Strategy

The solver is a depth-first backtracker with the following heuristics to reduce search:

1. **Most Constrained Row (MRV over rows):**
   * At each recursion the solver picks the row `r` that currently has the **fewest valid column choices** . This is implemented in `getMostConstrainedRow()` which calls `countOptions(r)` (counts valid columns for row `r`) and chooses the row with the minimum options that is still empty.
   * If a row has `0` options, `getMostConstrainedRow()` returns that row immediately so the backtracking layer sees the dead-end quickly. This gives early pruning.
2. **Move ordering using `countConstraints(r, c)`:**
   * For the chosen row `r`, the solver collects all valid columns `(c)` and computes `countConstraints(r, c)` for each candidate.
   * `countConstraints` estimates how many *future* cells (in rows `r+1..n-1`) would remain available (and therefore how many potential placements remain) if you were to place a queen at `(r, c)`. It iterates future rows and checks each candidate cell against `col_used`, `reqd` and `blocked` and increments a counter.
   * The solver then sorts candidate columns by that `countConstraints` value **ascending** and tries them in that order. This is an implementation detail that affects search; the sort key is `lambda x: x[1]`.
3. **Forward Checks and Local Pruning:**
   * `isValid(r,c)` already performs the quick forward checks: ***column used? region already satisfied? cell blocked?***
   * When placing a queen the solver updates:
     * `col_used` (fast column conflict tracking)
     * `reqd[region]` decrement (ensures exactly one queen per region)
     * `blocked` set for the immediate 8-neighbourhood cells (prevents placements adjacent to queens)
   * On backtracking those changes are reverted.

### Important of the Heuristics

* **MRV (fewest options row)** focuses search on the row most likely to fail, which often reduces the depth of unsuccessful exploration.
* **Counting future options** gives a (cheap) lookahead to prefer placements with predictable impacts on the remainder of the board; trying the more constraining placements first can either find a solution quickly if that placement is correct, or prune the search early if it causes a contradiction.
* **Column set & blocked set** are constant-time checks (set membership) and make validity checking cheap.

### Pseudocode

<pre class="overflow-visible!" data-start="6944" data-end="7415"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-text"><span><span>parse board -> regions (region_name -> list of cells)
init reqd[region] = 1
init col_used = {}, blocked = set(), queens = [-1]*n

backtrack(placed):
    pick row r with smallest number of valid columns (MRV)
    if all rows filled -> return True
    for each valid column c for r:
        try place queen at (r,c):
            mark queen, update col_used, reqd, blocked
            if backtrack(placed+1): return True
            undo changes
    return False
</span></span></code></div></div></pre>

---

## Example

`config.py` contains a sample 16×16 test board under the variable `BOARD` and a `COLOR_MAP`. Running `python main.py` will print something like:

<pre class="overflow-visible!" data-start="8553" data-end="8633"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre!"><span><span>Solving </span><span>16</span><span>x16 board </span><span>with</span><span></span><span>16</span><span> regions...
Solution found </span><span>in</span><span></span><span>0.12345</span><span> seconds
</span></span></code></div></div></pre>

…and then open the `pygame` window that draws each region in its color and overlays a `Q` where queens were placed.

---

## Future improvements

* Add a CLI to load different boards (JSON/CSV) and batch-run test cases.
* Add unit tests and a CI workflow.
* Make it into a chrome extension to solve the board directly in your browser
