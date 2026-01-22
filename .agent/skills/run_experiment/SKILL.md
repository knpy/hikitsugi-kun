---
name: run_experiment
description: Set up and document a new experiment
---

# Run Experiment Skill

This skill standardizes the process of running an experiment.

## Steps

1.  **Setup Directory**
    - Ask for a short experiment name (e.g., `test-whisper`).
    - Generate date-stamped folder: `experiments/YYYY-MM-DD-test-whisper/`.

2.  **Initialize Report**
    - Copy the structure from `experiments/README.md` to `experiments/YYYY-MM-DD-test-whisper/REPORT.md`.
    - Fill in "Date" and "Author".

3.  **Execute**
    - Create any necessary test scripts in the folder.
    - **IMPORTANT**: Use Python Interactive Window format (`.py` files with `# %%` cell markers) instead of Jupyter Notebooks (`.ipynb`).
        - *Reasoning*: Better for version control, AI editing, and diff readability.
        - *Example*:
          ```python
          # %%
          # Cell 1: Setup
          import os

          # %%
          # Cell 2: Test Logic
          print("Running experiment...")
          ```
    - Run the logic (e.g., specific prompt tests).

4.  **Log Results**
    - Update `REPORT.md` with "Results" and "Conclusion".

## Usage
When the user asks to "experiment", "test a prompt", or "verify a hypothesis".
