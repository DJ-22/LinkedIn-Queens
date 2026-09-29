# LinkedIn Queens

[![CI](https://github.com/DJ-22/LinkedIn-Queens/actions/workflows/ci.yml/badge.svg)](https://github.com/DJ-22/LinkedIn-Queens/actions/workflows/ci.yml)

A solver for the Queens puzzle from LinkedIn's daily games. It comes with a pygame app for playing and watching random levels, and a Chromium extension that solves levels on [queensgame.vercel.app](https://queensgame.vercel.app).

> This is an unofficial project. It isn't affiliated with, endorsed by or connected to LinkedIn.

## The puzzle

An n×n board is split into n coloured regions. Place n queens so that every row, every column and every region holds exactly one queen, and no two queens touch, not even diagonally.

## What's in the repo

- **Desktop app** (`python main.py`): a pygame menu with three options.
  1. **Open the website** opens queensgame.vercel.app in your browser.
  2. **Play a random level** asks for a size from 4 to 20 and generates a level to solve yourself. Left click cycles a cell through ✕, queen and empty; right click clears it. **Auto X** marks every cell your queens rule out, and clashing queens are outlined in red.
  3. **Watch the solver** generates a level, times the solver on it, then replays every queen the solver placed and took back, squeezed into 5 seconds.
- **Browser extension** (`extension/`): adds a **Solve** button to levels on queensgame.vercel.app. See [extension/README.md](extension/README.md).
- **Solver, generator and app code** (`queens/`): see [queens/README.md](queens/README.md) for how the solver works.
- **Tests** (`tests/`): see [tests/README.md](tests/README.md) for what each test checks.

## Requirements

- Python 3.12 or newer. The solver replay uses `sys.monitoring`, which arrived in 3.12.
- pygame, from `requirements.txt`, to run the app. Development also needs pylint; see [Test and lint](#test-and-lint).

## Setup

```sh
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS and Linux
pip install -r requirements.txt
```

## Run

```sh
python main.py
```

| Screen           | Keys                                                                                   |
| ---------------- | -------------------------------------------------------------------------------------- |
| Menu             | **1**, **2**, **3** pick an option; **Esc** quits                                      |
| Board size       | Type a number or use **Up**/**Down**; **Enter** starts; **Esc** goes back              |
| Play             | **A** toggles auto X; **N** makes a new level; **Esc** returns to the menu             |
| Watch the solver | **R** replays the solver's steps; **N** makes a new level; **Esc** returns to the menu |

## Test and lint

Install the development tools once, then run both from the repo root:

```sh
pip install -e ".[dev]"
python -m unittest
python -m pylint main.py queens tests
```

The tests run headless, so no window opens.

## Project layout

```text
main.py            Starts the pygame app
queens/            Solver, level generator, replay recorder and the pygame app
tests/             unittest suite
extension/         Chromium extension for queensgame.vercel.app
requirements.txt   pygame, to run the app
pyproject.toml     Project metadata, dependencies, dev tools and pylint settings
.github/           CI workflow: tests and pylint on every push
```

## License

MIT. See [LICENSE](LICENSE).
