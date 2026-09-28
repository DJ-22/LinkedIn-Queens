const SITE_ORIGIN = "https://queensgame.vercel.app";
const CONNECT_MESSAGE = "queens-solver-connect";
const QUEENS_FILES = ["__init__.py", "board_parser.py", "solver.py"];
const MISSING_FILES =
    "Solver files are missing; run python extension/build.py and reload the extension";

const solverReady = loadSolver();

async function readSolverFile(name) {
    const response = await fetch(`../vendor/queens/${name}`).catch(() => null);
    if (!response?.ok) throw new Error(MISSING_FILES);
    return response.text();
}

async function loadSolver() {
    let loadPyodide;
    try {
        ({ loadPyodide } = await import("../vendor/pyodide/pyodide.mjs"));
    } catch {
        throw new Error(MISSING_FILES);
    }

    const pyodide = await loadPyodide();

    pyodide.FS.mkdirTree("/solver/queens");
    for (const name of QUEENS_FILES) {
        pyodide.FS.writeFile(
            `/solver/queens/${name}`,
            await readSolverFile(name),
        );
    }

    const solveGrid = pyodide.runPython(`
import sys
sys.path.insert(0, "/solver")

from queens.board_parser import parse_regions
from queens.solver import solve

def solve_grid(grid):
    regions, n = parse_regions(grid)
    return solve(n, regions)

solve_grid
`);

    return (grid) => {
        const pyGrid = pyodide.toPy(grid);
        try {
            const result = solveGrid(pyGrid);
            if (!result) return null;

            const solution = result.toJs();
            result.destroy();
            return solution;
        } finally {
            pyGrid.destroy();
        }
    };
}

const describeError = (err) =>
    String(err?.message ?? err)
        .trim()
        .split("\n")
        .pop();

addEventListener("message", (event) => {
    const [port] = event.ports;
    if (
        event.origin !== SITE_ORIGIN ||
        event.data !== CONNECT_MESSAGE ||
        !port
    ) {
        return;
    }

    port.onmessage = async ({ data }) => {
        if (data.type !== "solve") return;

        try {
            const solveGrid = await solverReady;
            const start = performance.now();
            const solution = solveGrid(data.grid);
            port.postMessage({
                type: "solved",
                solution,
                elapsed: performance.now() - start,
            });
        } catch (err) {
            port.postMessage({
                type: "solve-error",
                message: describeError(err),
            });
        }
    };

    solverReady.then(
        () => port.postMessage({ type: "ready" }),
        (err) =>
            port.postMessage({
                type: "load-error",
                message: describeError(err),
            }),
    );
});
