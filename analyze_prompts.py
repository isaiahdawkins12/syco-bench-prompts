"""Analysis pipeline for the system-prompts experiment.

Reads experiment_manifest.csv, loads per-test item-level CSVs from each cell's
output directory, computes per-cell statistics (bootstrap CIs, paired Wilcoxon
vs. baseline, Cliff's delta), and writes Figures 1-5 + Tables 1-4 specified in
EXPERIMENT_PLAN.md §5-6.

Outputs go to figures/ (PNGs) and tables/ (CSVs).
"""
import argparse
import csv
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

plt.style.use("seaborn-v0_8-darkgrid")

RESULTS_ROOT = "experiment_results"
MANIFEST_PATH = f"{RESULTS_ROOT}/manifest.csv"
FIG_DIR = f"{RESULTS_ROOT}/figures"
TBL_DIR = f"{RESULTS_ROOT}/tables"

PROMPT_ORDER = ["none", "agreeable", "direct", "principle", "role", "reasoning"]
ANTI_SYCO_PROMPTS = ["direct", "principle", "role", "reasoning"]
PROMPT_PALETTE = {
    "none":      "#7f7f7f",
    "agreeable": "#d62728",
    "direct":    "#1f77b4",
    "principle": "#2ca02c",
    "role":      "#9467bd",
    "reasoning": "#ff7f0e",
}

# Sub-test → (csv filename, columns to read, item-level metric fn, direction)
# direction: +1 means higher = more sycophantic; for delusion same.
SUBTESTS = {
    "pickside": dict(
        csv="pickside_results.csv",
        cols=["score1", "score2"],
        item_metric=lambda r: float(r["score1"]) + float(r["score2"]),
        ylabel="Pickside (sum of two-ordering scores)",
        higher_is_more_sycophantic=True,
    ),
    "mirror": dict(
        csv="mirror_results.csv",
        cols=["score1", "score2"],
        item_metric=lambda r: abs(float(r["score1"]) - float(r["score2"])),
        ylabel="Mirror (|score₁ − score₂|)",
        higher_is_more_sycophantic=True,
    ),
    "whosaid": dict(
        csv="whosaid_results.csv",
        cols=["score_self", "score_friend"],
        item_metric=lambda r: float(r["score_self"]) - float(r["score_friend"]),
        ylabel="Whosaid (self − online attribution)",
        higher_is_more_sycophantic=True,
    ),
    "delusion": dict(
        csv="delusion_results.csv",
        cols=["median_score"],
        item_metric=lambda r: float(r["median_score"]),
        ylabel="Delusion acceptance (0–5)",
        higher_is_more_sycophantic=True,
    ),
}


# ---------- data loading ----------

def load_manifest() -> pd.DataFrame:
    if not os.path.exists(MANIFEST_PATH):
        raise SystemExit(f"Manifest not found: {MANIFEST_PATH}. Run run_experiment.py first.")
    df = pd.read_csv(MANIFEST_PATH)
    df = df[df["status"] == "completed"].copy()
    if df.empty:
        raise SystemExit("No completed cells in manifest.")
    return df


def load_cell_items(output_dir: str, subtest: str) -> list[float]:
    """Return list of item-level metric values for one cell × sub-test."""
    spec = SUBTESTS[subtest]
    path = os.path.join(output_dir, spec["csv"])
    if not os.path.exists(path):
        return []
    items = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                if any(str(row.get(c, "")).strip() in ("", "n/a") for c in spec["cols"]):
                    continue
                if any(math.isnan(float(row[c])) for c in spec["cols"]):
                    continue
                items.append(spec["item_metric"](row))
            except (ValueError, TypeError):
                continue
    return items


def build_long_table(manifest: pd.DataFrame) -> pd.DataFrame:
    """Long-format table: one row per (cell, subtest) with item-level array stored as list."""
    rows = []
    for _, m_row in manifest.iterrows():
        for subtest in SUBTESTS:
            items = load_cell_items(m_row["output_dir"], subtest)
            rows.append({
                "model": m_row["model"],
                "prompt": m_row["prompt"],
                "subtest": subtest,
                "n_items": len(items),
                "items": items,
                "mean": float(np.mean(items)) if items else float("nan"),
            })
    return pd.DataFrame(rows)


# ---------- statistics ----------

def bootstrap_ci(items: list[float], n_resamples: int = 1000,
                 alpha: float = 0.05, rng_seed: int = 0) -> tuple[float, float]:
    if not items:
        return float("nan"), float("nan")
    rng = np.random.default_rng(rng_seed)
    arr = np.asarray(items, dtype=float)
    means = rng.choice(arr, size=(n_resamples, len(arr)), replace=True).mean(axis=1)
    lo = float(np.percentile(means, 100 * alpha / 2))
    hi = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return lo, hi


def cliffs_delta(x: list[float], y: list[float]) -> float:
    """Cliff's delta in [-1, +1]. Positive = x tends to exceed y."""
    if not x or not y:
        return float("nan")
    nx, ny = len(x), len(y)
    gt = lt = 0
    for xi in x:
        for yj in y:
            if xi > yj:
                gt += 1
            elif xi < yj:
                lt += 1
    return (gt - lt) / (nx * ny)


def holm_bonferroni(pvals: list[float]) -> list[float]:
    """Holm step-down adjustment of p-values, preserving input order."""
    n = len(pvals)
    order = sorted(range(n), key=lambda i: pvals[i])
    adjusted = [0.0] * n
    running = 0.0
    for rank, idx in enumerate(order):
        adj = (n - rank) * pvals[idx]
        running = max(running, min(1.0, adj))
        adjusted[idx] = running
    return adjusted


# ---------- table builders ----------

def build_cell_table(long: pd.DataFrame) -> pd.DataFrame:
    """Table 1: mean ± 95% CI for every (model, prompt, subtest) cell."""
    rows = []
    for _, r in long.iterrows():
        lo, hi = bootstrap_ci(r["items"])
        rows.append({
            "model": r["model"],
            "prompt": r["prompt"],
            "subtest": r["subtest"],
            "n": r["n_items"],
            "mean": r["mean"],
            "ci_lo": lo,
            "ci_hi": hi,
        })
    return pd.DataFrame(rows)


def build_pairwise_table(long: pd.DataFrame) -> pd.DataFrame:
    """Table 2/3: per (model, subtest), Wilcoxon p, Holm-corrected p, Cliff's δ
    for each anti-syco prompt vs. `none` baseline."""
    rows = []
    for (model, subtest), grp in long.groupby(["model", "subtest"]):
        baseline = grp[grp["prompt"] == "none"]
        if baseline.empty:
            continue
        baseline_items = baseline.iloc[0]["items"]
        if not baseline_items:
            continue
        comp_prompts = [p for p in PROMPT_ORDER if p != "none"]
        block = []
        for p in comp_prompts:
            sub = grp[grp["prompt"] == p]
            if sub.empty:
                continue
            arr = sub.iloc[0]["items"]
            if len(arr) != len(baseline_items):
                pval = float("nan")
            else:
                try:
                    _, pval = stats.wilcoxon(arr, baseline_items, zero_method="wilcox")
                except ValueError:
                    pval = 1.0  # all zero differences
            delta = cliffs_delta(arr, baseline_items)
            block.append({
                "model": model,
                "subtest": subtest,
                "prompt": p,
                "mean_diff_vs_none": (np.mean(arr) - np.mean(baseline_items)) if arr else float("nan"),
                "cliffs_delta_vs_none": delta,
                "wilcoxon_p_raw": pval,
            })
        # Holm within this (model, subtest) family
        raw = [b["wilcoxon_p_raw"] for b in block]
        valid_idx = [i for i, p in enumerate(raw) if not math.isnan(p)]
        if valid_idx:
            adj = holm_bonferroni([raw[i] for i in valid_idx])
            for i, ai in zip(valid_idx, adj):
                block[i]["wilcoxon_p_holm"] = ai
            for i in range(len(block)):
                if i not in valid_idx:
                    block[i]["wilcoxon_p_holm"] = float("nan")
        rows.extend(block)
    return pd.DataFrame(rows)


def build_best_prompt_table(pairwise: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    """Table 2: best (most sycophancy-reducing) prompt per (model, subtest)."""
    rows = []
    anti = pairwise[pairwise["prompt"].isin(ANTI_SYCO_PROMPTS)]
    for (model, subtest), grp in anti.groupby(["model", "subtest"]):
        # Most negative mean_diff = biggest reduction (assuming higher = more syco)
        best = grp.loc[grp["mean_diff_vs_none"].idxmin()]
        baseline = cells[(cells.model == model) & (cells.prompt == "none") &
                         (cells.subtest == subtest)]
        baseline_mean = baseline.iloc[0]["mean"] if not baseline.empty else float("nan")
        rows.append({
            "model": model,
            "subtest": subtest,
            "baseline_mean": baseline_mean,
            "best_prompt": best["prompt"],
            "best_mean_diff": best["mean_diff_vs_none"],
            "best_cliffs_delta": best["cliffs_delta_vs_none"],
            "best_p_holm": best.get("wilcoxon_p_holm", float("nan")),
        })
    return pd.DataFrame(rows)


# ---------- figures ----------

def fig1_grouped_bars(cells: pd.DataFrame, path: str) -> None:
    """Figure 1: 2x2 grouped bar chart, one panel per sub-test."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    subtests = list(SUBTESTS.keys())
    models = sorted(cells["model"].unique())
    width = 0.13
    x = np.arange(len(models))
    for ax, st in zip(axes.flat, subtests):
        for j, prompt in enumerate(PROMPT_ORDER):
            sub = cells[(cells.subtest == st) & (cells.prompt == prompt)]
            sub = sub.set_index("model").reindex(models)
            offsets = (j - (len(PROMPT_ORDER) - 1) / 2) * width
            yerr = np.array([
                sub["mean"] - sub["ci_lo"],
                sub["ci_hi"] - sub["mean"],
            ])
            ax.bar(x + offsets, sub["mean"], width,
                   label=prompt, color=PROMPT_PALETTE[prompt],
                   yerr=yerr, capsize=2,
                   edgecolor="black", linewidth=0.4)
        ax.set_title(f"{st.capitalize()}", fontsize=13, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([m.split("/")[-1] for m in models], rotation=15, ha="right")
        ax.set_ylabel(SUBTESTS[st]["ylabel"])
        ax.axhline(0, color="grey", linestyle="--", linewidth=0.7)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(PROMPT_ORDER),
               bbox_to_anchor=(0.5, 1.02), frameon=False)
    fig.suptitle("Sycophancy by system prompt × model × sub-test",
                 fontsize=15, fontweight="bold", y=1.06)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig2_heatmaps(cells: pd.DataFrame, path: str) -> None:
    """Figure 2: 2x2 prompt × model heatmaps, one per sub-test, diverging palette
    centered on the per-model `none` baseline."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    subtests = list(SUBTESTS.keys())
    for ax, st in zip(axes.flat, subtests):
        sub = cells[cells.subtest == st]
        pivot = sub.pivot(index="prompt", columns="model", values="mean")
        pivot = pivot.reindex(PROMPT_ORDER)
        baseline = pivot.loc["none"] if "none" in pivot.index else pivot.mean()
        delta = pivot.subtract(baseline, axis=1)
        vmax = max(abs(delta.min().min()), abs(delta.max().max()), 1e-6)
        sns.heatmap(delta, annot=pivot.round(2), fmt="", cmap="RdBu_r",
                    center=0, vmin=-vmax, vmax=vmax, ax=ax,
                    cbar_kws={"label": "Δ vs. `none` baseline"})
        ax.set_title(f"{st.capitalize()}", fontsize=13, fontweight="bold")
        ax.set_xticklabels([m.split("/")[-1] for m in pivot.columns],
                           rotation=15, ha="right")
        ax.set_ylabel("System prompt")
        ax.set_xlabel("")
    fig.suptitle("Prompt × model interaction (cell color = Δ vs. baseline; annotation = absolute mean)",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig3_reduction_lines(cells: pd.DataFrame, path: str) -> None:
    """Figure 3: change vs. `none` baseline, one line per model, four panels."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    subtests = list(SUBTESTS.keys())
    models = sorted(cells["model"].unique())
    non_baseline = [p for p in PROMPT_ORDER if p != "none"]
    for ax, st in zip(axes.flat, subtests):
        sub = cells[cells.subtest == st]
        for model in models:
            ms = sub[sub.model == model].set_index("prompt").reindex(PROMPT_ORDER)
            baseline = ms.loc["none", "mean"]
            deltas = ms["mean"] - baseline
            ax.plot(non_baseline, deltas.loc[non_baseline].values,
                    marker="o", linewidth=2, label=model.split("/")[-1])
        ax.axhline(0, color="grey", linestyle="--", linewidth=0.7)
        ax.set_title(f"{st.capitalize()}", fontsize=13, fontweight="bold")
        ax.set_ylabel("Δ score vs. `none`")
        ax.tick_params(axis="x", rotation=15)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(models),
               bbox_to_anchor=(0.5, 1.02), frameon=False)
    fig.suptitle("Intervention effect: change in sycophancy vs. `none` baseline",
                 fontsize=14, fontweight="bold", y=1.05)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig4_correlation_matrices(cells: pd.DataFrame, path: str) -> None:
    """Figure 4: cross-test correlations, baseline-only vs. all-conditions pooled."""
    pivot = cells.pivot_table(index=["model", "prompt"], columns="subtest", values="mean")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    titles = [
        ("`none` baseline only (replicates Duffy Fig 1 design)", pivot.xs("none", level="prompt")),
        ("All 18 conditions pooled", pivot),
    ]
    for ax, (title, df) in zip(axes, titles):
        if len(df) < 2:
            ax.text(0.5, 0.5, "Not enough rows for correlation",
                    ha="center", va="center")
            continue
        corr = df.corr()
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
                    center=0, vmin=-1, vmax=1, ax=ax,
                    cbar_kws={"label": "Pearson r"})
        ax.set_title(title, fontsize=12, fontweight="bold")
    fig.suptitle("Cross-test correlations of sycophancy metrics",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig5_tradeoff_scatter(cells: pd.DataFrame, path: str) -> None:
    """Figure 5: Pickside × Delusion scatter. One marker per cell."""
    pivot = cells.pivot_table(index=["model", "prompt"], columns="subtest",
                              values="mean").reset_index()
    if "pickside" not in pivot.columns or "delusion" not in pivot.columns:
        return
    fig, ax = plt.subplots(figsize=(9, 7))
    markers = {m: mk for m, mk in zip(sorted(cells.model.unique()), ["o", "s", "^", "D", "v"])}
    for _, r in pivot.iterrows():
        ax.scatter(r["pickside"], r["delusion"],
                   color=PROMPT_PALETTE[r["prompt"]],
                   marker=markers[r["model"]],
                   s=150, edgecolor="black", linewidth=0.6,
                   alpha=0.85)
        ax.annotate(r["prompt"][:3], (r["pickside"], r["delusion"]),
                    fontsize=7, ha="center", va="center", color="white")
    ax.axvline(0, color="grey", linestyle="--", linewidth=0.7)
    ax.set_xlabel("Pickside score (higher = more sycophantic; <0 = contrarian)")
    ax.set_ylabel("Delusion acceptance (lower = more often corrects)")
    ax.set_title("Sycophancy ⇄ contrarianism trade-off (one point per model × prompt)",
                 fontsize=13, fontweight="bold")
    # Two custom legends: prompt (color) + model (marker)
    from matplotlib.lines import Line2D
    prompt_legend = [Line2D([0], [0], marker="o", color="w",
                            markerfacecolor=c, markersize=12, label=p)
                     for p, c in PROMPT_PALETTE.items()]
    model_legend = [Line2D([0], [0], marker=markers[m], color="black",
                           markerfacecolor="white", markersize=10,
                           label=m.split("/")[-1])
                    for m in sorted(cells.model.unique())]
    leg1 = ax.legend(handles=prompt_legend, title="prompt",
                     loc="upper left", bbox_to_anchor=(1.02, 1.0))
    ax.add_artist(leg1)
    ax.legend(handles=model_legend, title="model",
              loc="lower left", bbox_to_anchor=(1.02, 0.0))
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig6_violins(long: pd.DataFrame, path: str) -> None:
    """Figure 6 (stretch): item-level distributions per (prompt, sub-test)."""
    long_explode = long.explode("items").rename(columns={"items": "score"})
    long_explode["score"] = pd.to_numeric(long_explode["score"], errors="coerce")
    long_explode = long_explode.dropna(subset=["score"])
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for ax, st in zip(axes.flat, SUBTESTS):
        sub = long_explode[long_explode.subtest == st]
        sns.violinplot(data=sub, x="prompt", y="score", ax=ax,
                       order=PROMPT_ORDER, palette=PROMPT_PALETTE,
                       inner="quartile", cut=0)
        ax.set_title(f"{st.capitalize()}", fontsize=13, fontweight="bold")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=15)
    fig.suptitle("Item-level score distributions by prompt (pooled over models)",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------- main ----------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-fig6", action="store_true",
                        help="Skip the stretch violin figure.")
    args = parser.parse_args()

    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(TBL_DIR, exist_ok=True)

    manifest = load_manifest()
    print(f"Loading {len(manifest)} completed cells from manifest...")
    long = build_long_table(manifest)
    print(f"Loaded {len(long)} (cell, sub-test) rows")

    cells = build_cell_table(long)
    cells.to_csv(os.path.join(TBL_DIR, "table1_cells_with_ci.csv"), index=False)

    pairwise = build_pairwise_table(long)
    pairwise.to_csv(os.path.join(TBL_DIR, "table3_pairwise_vs_none.csv"), index=False)

    best = build_best_prompt_table(pairwise, cells)
    best.to_csv(os.path.join(TBL_DIR, "table2_best_prompt_per_cell.csv"), index=False)

    print("Generating figures...")
    fig1_grouped_bars(cells, os.path.join(FIG_DIR, "fig1_grouped_bars.png"))
    fig2_heatmaps(cells, os.path.join(FIG_DIR, "fig2_heatmaps.png"))
    fig3_reduction_lines(cells, os.path.join(FIG_DIR, "fig3_reduction_lines.png"))
    fig4_correlation_matrices(cells, os.path.join(FIG_DIR, "fig4_correlations.png"))
    fig5_tradeoff_scatter(cells, os.path.join(FIG_DIR, "fig5_tradeoff.png"))
    if not args.skip_fig6:
        fig6_violins(long, os.path.join(FIG_DIR, "fig6_violins.png"))

    # Quick console summary
    print("\nHeadline cell means:")
    pivot = cells.pivot_table(index=["model", "prompt"], columns="subtest", values="mean")
    pivot = pivot.reindex([(m, p) for m in sorted(cells.model.unique())
                           for p in PROMPT_ORDER])
    print(pivot.round(2).to_string())
    print(f"\nFigures saved to {FIG_DIR}/, tables saved to {TBL_DIR}/")


if __name__ == "__main__":
    main()
