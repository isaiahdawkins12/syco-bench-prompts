# Experiment Results

All outputs from the system-prompts-vs-sycophancy experiment land here. This directory is the single artifact teammates need to review and the analysis pipeline writes to.

## Contents

| Path | Created by | Purpose |
|---|---|---|
| `manifest.csv` | `run_experiment.py` | One row per cell: model, prompt, output folder path, status, timestamps. The index of everything else. |
| `cells/<timestamp>_<model>[_<prompt>]/` | `run_all_tests.py` (per cell) | Raw per-cell output: `pickside_results.csv`, `mirror_results.csv`, `whosaid_results.csv`, `delusion_results.csv`, `master_results.csv`, `test_run.log`. Every model response and every judge score is here. |
| `logs/<cell_id>.log` | `run_experiment.py` | Combined stdout+stderr from each cell run. Useful for debugging failed cells. |
| `figures/fig{1..6}_*.png` | `analyze_prompts.py` | All charts (see `TEAMMATE_BRIEFING.md` §8 for what each shows). |
| `tables/table{1..3}_*.csv` | `analyze_prompts.py` | Headline numerical results. |

## How to inspect

- **High-level summary**: open `tables/table1_cells_with_ci.csv` — every (model, prompt, sub-test) cell with its score and 95% confidence interval.
- **Best prompt per cell**: `tables/table2_best_prompt_per_cell.csv`.
- **Statistical results**: `tables/table3_pairwise_vs_none.csv`.
- **Visualizations**: `figures/`.
- **Individual model responses**: drill into any `cells/<...>/` folder to read the actual responses the model gave to each test item.

## Reproducing

From the repository root:
```
.venv/bin/python run_experiment.py        # runs the full sweep, ~3-6 hours, ~$20 of API spend
.venv/bin/python analyze_prompts.py       # generates figures and tables from the manifest
```

Re-running `run_experiment.py` is safe: cells already marked `completed` in `manifest.csv` are skipped.
