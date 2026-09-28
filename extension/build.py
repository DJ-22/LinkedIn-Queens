"""Run this once before loading the extension, and again after editing anything
in queens/ (then hit "Reload" on the extension).
"""

import io
import shutil
import tarfile
import urllib.request
from pathlib import Path

PYODIDE_VERSION = "314.0.7"
PYODIDE_URL = (
    f"https://registry.npmjs.org/pyodide/-/pyodide-{PYODIDE_VERSION}.tgz"
)
PYODIDE_FILES = (
    "pyodide.mjs",
    "pyodide.asm.mjs",
    "pyodide.asm.wasm",
    "python_stdlib.zip",
    "pyodide-lock.json",
)
DOWNLOAD_TIMEOUT = 120

QUEENS_FILES = ("__init__.py", "board_parser.py", "solver.py")

EXTENSION_DIR = Path(__file__).resolve().parent
QUEENS_DIR = EXTENSION_DIR.parent / "queens"
VENDOR_DIR = EXTENSION_DIR / "vendor"


def fetch_pyodide(dest: Path):
    marker = dest / ".version"
    complete = all((dest / name).exists() for name in PYODIDE_FILES)
    if complete and marker.exists() and marker.read_text() == PYODIDE_VERSION:
        print(f"Pyodide {PYODIDE_VERSION} already present")
        return

    print(f"Downloading Pyodide {PYODIDE_VERSION}...")
    with urllib.request.urlopen(
        PYODIDE_URL, timeout=DOWNLOAD_TIMEOUT
    ) as response:
        archive = io.BytesIO(response.read())

    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)

    with tarfile.open(fileobj=archive, mode="r:gz") as tar:
        for name in PYODIDE_FILES:
            try:
                source = tar.extractfile(f"package/{name}")
            except KeyError:
                source = None

            if source is None:
                raise RuntimeError(
                    f"{name} is missing from the Pyodide {PYODIDE_VERSION} "
                    "package"
                )

            (dest / name).write_bytes(source.read())

    marker.write_text(PYODIDE_VERSION)


def copy_solver(dest: Path):
    dest.mkdir(parents=True, exist_ok=True)

    for name in QUEENS_FILES:
        shutil.copyfile(QUEENS_DIR / name, dest / name)

    print(f"Copied {', '.join(QUEENS_FILES)} from {QUEENS_DIR}")


def main():
    fetch_pyodide(VENDOR_DIR / "pyodide")
    copy_solver(VENDOR_DIR / "queens")
    print(f"Done. Load {EXTENSION_DIR} as an unpacked extension.")


if __name__ == "__main__":
    main()
