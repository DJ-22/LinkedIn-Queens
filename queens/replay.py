import inspect
import sys
import time
from array import array

from queens.board_parser import parse_regions
from queens.solver import Search, solve

MAX_STEPS = 1_000_000
MAX_SECONDS = 10
MAX_RECORD_SIZE = 32


class StopRecording(Exception):
    pass


def encode(r, c, placed):
    return (r << 6) | (c << 1) | placed


def decode(step):
    return step >> 6, (step >> 1) & 31, step & 1


def _backtrack_code():
    backtrack = getattr(Search, "backtrack", None)
    if backtrack is None:
        raise RuntimeError("Search has no backtrack() method to watch")

    return backtrack.__code__


def _log_changes(seen, watched, steps):
    for r, (old, new) in enumerate(zip(seen, watched)):
        if old != new:
            if old != -1:
                steps.append(encode(r, old, 0))
            if new != -1:
                steps.append(encode(r, new, 1))


def record_steps(n, regions, max_steps=MAX_STEPS, max_seconds=MAX_SECONDS):
    if not hasattr(sys, "monitoring"):
        raise RuntimeError(
            "Recording the solver's steps needs Python 3.12 or newer"
        )
    if n > MAX_RECORD_SIZE:
        raise RuntimeError(
            "Recording supports boards up to "
            f"{MAX_RECORD_SIZE}x{MAX_RECORD_SIZE}, not {n}x{n}"
        )

    monitoring = sys.monitoring
    tool = next((i for i in range(6) if monitoring.get_tool(i) is None), None)
    if tool is None:
        raise RuntimeError(
            "No free sys.monitoring tool slot to watch the solver with"
        )

    code = _backtrack_code()
    steps = array("i")
    watched = seen = None
    deadline = time.perf_counter() + max_seconds

    def on_line(_code, _line):
        nonlocal watched, seen

        if watched is None:
            try:
                watched = inspect.currentframe().f_back.f_locals["self"].queens
            except (KeyError, AttributeError):
                raise RuntimeError(
                    "backtrack() has no queens list to watch"
                ) from None
            seen = list(watched)
            return

        if watched == seen:
            return

        _log_changes(seen, watched, steps)
        seen = list(watched)

        if len(steps) >= max_steps or time.perf_counter() > deadline:
            raise StopRecording

    monitoring.use_tool_id(tool, "queens-replay")
    try:
        monitoring.register_callback(tool, monitoring.events.LINE, on_line)
        monitoring.set_local_events(tool, code, monitoring.events.LINE)
        solve(n, regions)
        complete = True
    except StopRecording:
        complete = False
    finally:
        monitoring.set_local_events(tool, code, 0)
        monitoring.register_callback(tool, monitoring.events.LINE, None)
        monitoring.free_tool_id(tool)

    return steps, complete


def solve_and_record(grid, conn):
    regions, n = parse_regions(grid)
    start = time.perf_counter()
    solution = solve(n, regions)
    conn.send(("solved", solution, time.perf_counter() - start))

    if solution is None:
        return

    try:
        conn.send(("steps", *record_steps(n, regions)))
    except RuntimeError as err:
        conn.send(("no-steps", str(err)))
