# Queens Solver extension

Adds a **Solve** button above the board on [queensgame.vercel.app](https://queensgame.vercel.app) levels. Clicking it reads the board's colour regions, runs the solver in `queens/`, and places the queens for you.

## Install (any Chromium browser)

1. Build the extension. This downloads Pyodide once (about 13 MB, so it needs internet access) and copies the solver into `extension/vendor/`:

   ```sh
   python extension/build.py
   ```

2. Open `chrome://extensions`, turn on **Developer mode**, click **Load unpacked**, and pick the `extension` folder.
3. Open any level, wait for the button to change from "Loading solver..." to "Solve", and click it.

After editing anything in `queens/`, run `build.py` again and click **Reload** on the extension.

## How it works

- `content.js` runs on the site. It adds the button, reads each cell's background colour into a grid, and clicks the solution onto the board. Any queen you placed in a wrong cell gets removed; ✕ marks are left alone.
- `solver/frame.html` is a hidden extension iframe that loads Pyodide and calls `parse_regions` and `solve` from `queens/`, the same way the desktop app does. Solving runs there, so the page doesn't freeze while it works.
