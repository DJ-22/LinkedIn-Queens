# tests

The unittest suite: 42 tests in five files. Run it from the repo root:

```sh
python -m unittest                      # everything
python -m unittest tests.test_solver    # one file
python -m unittest -v                   # list each test as it runs
```

`tests/__init__.py` runs before any test and switches pygame to its dummy video driver, so the app tests never open a real window. It also hides pygame's welcome banner.

## test_solver.py

Checks `solve()` from `queens/solver.py`. Every solution is checked independently: one queen per row, column and region, and no two queens in neighbouring rows touching.

| Test | What it checks |
| --- | --- |
| `test_solves_generated_boards` | Solves 45 generated boards (5 each from 4×4 to 12×12) and checks every solution is valid |
| `test_boards_that_used_to_take_seconds_solve_quickly` | Three boards that took 5 s, 23 s and over 30 s before the solver was improved now solve in under a second, correctly |
| `test_returns_none_when_unsolvable` | A board where two regions both sit entirely in row 0 returns `None`, because one row can't hold two queens |
| `test_rejects_wrong_region_count` | A 4×4 board with only two regions raises `ValueError` |
| `test_rejects_regions_that_miss_cells` | Regions that leave most of the board uncovered raise `ValueError` |

## test_generator.py

Checks `generate_level()` from `queens/generator.py`.

| Test | What it checks |
| --- | --- |
| `test_levels_have_n_connected_regions` | For every size from 4 to 20 (3 seeds each): the grid is square, has exactly n regions, and every region is one connected piece |
| `test_levels_are_solvable` | 35 generated levels (4×4 to 10×10) all have a solution |
| `test_same_seed_gives_same_level` | Two levels generated from the same seed are identical |
| `test_needs_a_color_per_region` | Asking for an 8×8 level with only 7 colours raises `ValueError` |

## test_rules.py

Checks the shared rules in `queens/rules.py` on a small hand-made 4×4 board.

| Test | What it checks |
| --- | --- |
| `test_conflicts` | Two queens clash in the same row, column or region, or when touching (diagonals included), and don't otherwise |
| `test_covered_cells_skips_the_queens_themselves` | A queen in the corner rules out exactly its row, its column, the diagonal cell next to it and its region, but not its own cell |
| `test_touching_includes_diagonals_but_not_the_cell_itself` | Diagonal and side neighbours touch; a cell doesn't touch itself or a cell two rows away |
| `test_neighbors_matches_touching` | For every cell of a 4×4 board, `neighbors()` lists exactly the cells `touching()` agrees with, edges and corners included |

## test_replay.py

Checks the step recorder in `queens/replay.py`.

| Test | What it checks |
| --- | --- |
| `test_round_trips_every_cell_of_a_32_wide_board` | Encoding then decoding a step gives back the same row, column and placed flag, for every cell of the widest board the recorder supports |
| `test_replaying_the_steps_ends_on_the_solvers_answer` | Replaying the recorded steps on an empty board ends exactly on the solver's own answer (6×6, 8×8 and 10×10 boards) |
| `test_stops_early_at_max_steps` | With a 5-step limit, recording stops early and reports that it's incomplete |
| `test_refuses_boards_too_wide_to_encode` | A 33-wide board is refused with a clear error, instead of being recorded wrongly |
| `test_missing_queens_list_raises_runtime_error` | If the solver's `queens` list can't be found (simulated with a stand-in class), recording raises a clear `RuntimeError` |
| `test_sends_the_timed_answer_then_the_steps` | `solve_and_record` sends the timed answer first, then the complete list of steps |
| `test_child_process_does_not_load_pygame` | A solver process started the way the app starts it doesn't import pygame, so it starts quickly |

## test_app.py

Checks the pygame app in `queens/app.py`, its widgets and the board drawing, all headless.

### Drawing crowns

| Test | What it checks |
| --- | --- |
| `test_without_a_shadow_only_the_crown_is_drawn` | A plain crown paints its own colour and nothing below it |
| `test_shadow_shows_below_the_crown` | With a shadow, the crown stays on top and the shadow shows beneath it |
| `test_scaled_shadow_forms_a_halo` | A slightly larger shadow shows around the crown's edges as a halo |

### App and event loop

| Test | What it checks |
| --- | --- |
| `test_presses_left_on_a_screen_that_was_switched_away_are_dropped` | Pressing Esc then N in quick succession switches screens only once; the second press doesn't fire after the first has left the screen |
| `test_first_screen_is_entered_like_any_other` | The menu shown at startup goes through the same set-up as every other screen |
| `test_dispatch_stops_at_quit_and_drops_later_events` | A quit event stops the app, and events after it aren't handled |
| `test_idle_screen_waits_for_the_next_event` | When nothing is animating, the loop waits for the next event instead of redrawing at 60 fps |
| `test_animating_screen_runs_at_full_frame_rate` | While something is animating, the loop runs at 60 fps |

### Menu, size picker and widgets

| Test | What it checks |
| --- | --- |
| `test_says_the_website_opened_only_when_it_did` | "Opened … in your browser" appears only when the browser actually opened |
| `test_reports_when_no_browser_could_open` | When no browser opens, a red "Couldn't open a browser" message appears instead |
| `test_one_dot_per_size_centered_on_the_window` | The size picker has one dot per size from 4 to 20, centred in the window |
| `test_clicking_a_dot_picks_that_size` | Clicking the dot for 13 sets the size to 13 |
| `test_box_shadow_is_built_once_the_box_stops_growing` | The size box's shadow is reused across frames instead of being rebuilt every frame |
| `test_clicking_between_dots_changes_nothing` | A click that misses every dot leaves the size unchanged |
| `test_pill_is_centered_where_asked` | A status pill is drawn centred on the point it's given |

### Solver screen

| Test | What it checks |
| --- | --- |
| `test_broken_pipe_while_solving_fails_instead_of_crashing` | If the solver process dies mid-message while solving, the screen shows a failure instead of crashing the app |
| `test_broken_pipe_while_recording_shows_the_answer` | If it dies mid-message while recording, the screen still shows the answer it already has |

### Play screen

| Test | What it checks |
| --- | --- |
| `test_full_valid_board_wins` | Placing the solver's answer by clicking wins the level |
| `test_clashing_queens_are_flagged` | Two queens in the same row are both flagged as clashing, and the level isn't won |
| `test_auto_x_keeps_crosses_until_every_covering_queen_is_gone` | With auto X on, removing one queen clears only the ✕ marks no other queen covers |
| `test_covered_cells_are_reused_until_the_queens_change` | The covered cells are cached for the same set of queens, in any order, and recomputed when the queens change |
| `test_auto_x_never_removes_the_players_own_crosses` | A ✕ you placed yourself stays when the queen that covered it is removed |
