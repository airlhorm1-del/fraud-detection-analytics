"""Run the whole pipeline in order: load, profile, clean + rules, evaluate, charts.

Run: uv run python scripts/run_all.py   (the PaySim CSV must be in data/raw/)
"""
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["01_load.py", "02_profile.py", "03_build.py", "04_evaluate.py", "06_charts.py"]

if __name__ == "__main__":
    for step in STEPS:
        print(f"\n=== {step} ===")
        runpy.run_path(str(HERE / step), run_name="__main__")
