"""Start Potter Airlines with: python main.py"""

import importlib.util
from pathlib import Path
import subprocess
import sys


def main():
    project_folder = Path(__file__).resolve().parent

    if importlib.util.find_spec("streamlit") is None:
        print("Streamlit is missing. Run this in the project folder first:")
        print(f'"{sys.executable}" -m pip install -r requirements.txt')
        return 1

    # Use the same Python environment and the correct folder for database/CSV paths.
    return subprocess.call(
        [sys.executable, "-m", "streamlit", "run", "app.py"] + sys.argv[1:],
        cwd=project_folder,
    )


if __name__ == "__main__":
    raise SystemExit(main())
