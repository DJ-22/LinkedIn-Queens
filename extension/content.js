// Adds a "Solve" button above the board on queensgame.vercel.app.

const BUTTON_ID = "queens-solver-button";
const CONNECT_MESSAGE = "queens-solver-connect";
const LOAD_TIMEOUT_MS = 30000;

let solver = null;
let boardPath = null;

function getSolver() {
    solver ??= connectSolver().catch((err) => {
        solver = null;
        throw err;
    });
    return solver;
}

function connectSolver() {
    const frame = document.createElement("iframe");
    frame.src = chrome.runtime.getURL("solver/frame.html");
    frame.hidden = true;

    const connected = new Promise((resolve, reject) => {
        const timeout = setTimeout(
            () => reject(new Error("Solver did not load in time")),
            LOAD_TIMEOUT_MS,
        );
        let pending = null;

        frame.addEventListener(
            "load",
            () => {
                const { port1, port2 } = new MessageChannel();

                port1.onmessage = ({ data }) => {
                    if (data.type === "ready") {
                        clearTimeout(timeout);
                        resolve({
                            solve: (grid) =>
                                new Promise((res, rej) => {
                                    pending = { res, rej };
                                    port1.postMessage({ type: "solve", grid });
                                }),
                        });
                    } else if (data.type === "load-error") {
                        clearTimeout(timeout);
                        reject(new Error(data.message));
                    } else if (data.type === "solved") {
                        pending.res(data);
                    } else if (data.type === "solve-error") {
                        pending.rej(new Error(data.message));
                    }
                };

                frame.contentWindow.postMessage(
                    CONNECT_MESSAGE,
                    new URL(frame.src).origin,
                    [port2],
                );
            },
            { once: true },
        );
    });

    document.body.append(frame);
    return connected.catch((err) => {
        frame.remove();
        throw err;
    });
}

const cellAt = (r, c) =>
    document.querySelector(`.game .square[data-row="${r}"][data-col="${c}"]`);
const hasQueen = (cell) => cell.querySelector('[aria-label="queen"]') !== null;
const tick = () => new Promise((resolve) => setTimeout(resolve));

function readBoard() {
    const cells = document.querySelectorAll(
        ".game .square[data-row][data-col]",
    );
    const n = Math.round(Math.sqrt(cells.length));
    if (n === 0 || n * n !== cells.length) {
        throw new Error(
            `Found ${cells.length} cells, which is not a square board`,
        );
    }

    const grid = Array.from({ length: n }, () => Array(n).fill(null));
    for (const cell of cells) {
        const r = Number(cell.dataset.row);
        const c = Number(cell.dataset.col);
        if (!(r >= 0 && r < n && c >= 0 && c < n)) {
            throw new Error(
                `Cell (${cell.dataset.row}, ${cell.dataset.col}) is outside the ${n}x${n} board`,
            );
        }

        grid[r][c] =
            cell.style.backgroundColor ||
            getComputedStyle(cell).backgroundColor;
    }

    return grid;
}

async function clickCell(cell) {
    const rect = cell.getBoundingClientRect();
    const init = {
        bubbles: true,
        cancelable: true,
        composed: true,
        clientX: rect.left + rect.width / 2,
        clientY: rect.top + rect.height / 2,
        pointerId: 1,
        pointerType: "mouse",
        isPrimary: true,
        button: 0,
    };

    cell.dispatchEvent(
        new PointerEvent("pointerdown", { ...init, buttons: 1 }),
    );
    await tick();
    cell.dispatchEvent(new PointerEvent("pointerup", { ...init, buttons: 0 }));
    await tick();
}

// Cells cycle empty -> cross -> queen -> empty
async function setQueen(r, c, wanted) {
    for (let clicks = 0; clicks < 3; clicks++) {
        if (hasQueen(cellAt(r, c)) === wanted) return;
        await clickCell(cellAt(r, c));
    }

    if (hasQueen(cellAt(r, c)) !== wanted) {
        throw new Error(
            `Could not ${wanted ? "place" : "remove"} the queen at (${r}, ${c})`,
        );
    }
}

async function applySolution(solution) {
    const cells = solution.flatMap((row, r) =>
        row.map((isQueen, c) => ({ r, c, isQueen })),
    );

    for (const { r, c, isQueen } of cells) {
        if (!isQueen && hasQueen(cellAt(r, c))) await setQueen(r, c, false);
    }
    for (const { r, c, isQueen } of cells) {
        if (isQueen) await setQueen(r, c, true);
    }
}

function setStatus(button, state, label) {
    button.dataset.state = state;
    button.disabled = state === "loading" || state === "busy";
    button.textContent = label;
    button.title = label;
}

async function onSolveClick(event) {
    const button = event.currentTarget;
    const path = location.pathname;
    setStatus(button, "busy", "Solving...");

    try {
        const client = await getSolver();
        const { solution, elapsed } = await client.solve(readBoard());
        if (location.pathname !== path) {
            setStatus(button, "idle", "Solve");
            return;
        }
        if (!solution) {
            setStatus(button, "error", "No solution found");
            return;
        }

        await applySolution(solution);
        setStatus(
            button,
            "done",
            `Solved in ${(elapsed / 1000).toFixed(5)} seconds`,
        );
    } catch (err) {
        console.error("[Queens Solver]", err);
        setStatus(button, "error", err.message);
    }
}

function createButton() {
    const button = document.createElement("button");
    button.id = BUTTON_ID;
    button.type = "button";
    button.addEventListener("click", onSolveClick);
    return button;
}

function showReadyState(button) {
    setStatus(button, "loading", "Loading solver...");
    getSolver().then(
        () =>
            button.dataset.state === "loading" &&
            setStatus(button, "idle", "Solve"),
        (err) =>
            button.dataset.state === "loading" &&
            setStatus(button, "error", err.message),
    );
}

function syncButton() {
    const game = document.querySelector(".game");
    const onLevel =
        game?.querySelector(".square") &&
        !location.pathname.startsWith("/level-builder");
    let button = document.getElementById(BUTTON_ID);

    if (!onLevel) {
        button?.remove();
        return;
    }

    if (!button) {
        button = createButton();
        boardPath = null;
    }
    if (button.nextElementSibling !== game) {
        game.before(button);
    }

    if (boardPath !== location.pathname && button.dataset.state !== "busy") {
        boardPath = location.pathname;
        showReadyState(button);
    }
}

new MutationObserver(syncButton).observe(document.body, {
    childList: true,
    subtree: true,
});
syncButton();
