# Experiment Plan: System Prompts and Sycophancy in LLMs

**Course:** Trustworthy AI
**Benchmark:** Tim Duffy's syco-bench (https://github.com/timfduffy/syco-bench)
**Status:** Pre-registered — written before data collection. Any post-hoc analyses added later will be labeled exploratory.

---

## 1. Research question and hypotheses

### 1.1 Primary research question
**Can targeted system prompts reduce sycophantic behavior in deployed LLMs, and which prompt strategies generalize across models and across distinct facets of sycophancy?**

This directly addresses the open question Tim Duffy names in the syco-bench paper: *"Exploring the effects of a variety of system prompts on the level of sycophancy displayed."* Duffy compared each model's production chat-interface system prompt against no system prompt at all and found a small, inconsistent *increase* in sycophancy with the production prompt; no anti-sycophancy interventions were tested.

### 1.2 Hypotheses
| # | Hypothesis | Direction |
|---|---|---|
| H1 | Adding any explicit anti-sycophancy system prompt reduces sycophancy scores compared to the no-prompt baseline. | Per (model, sub-test): mean of any anti-syco condition < mean of `none` |
| H2 | The sycophancy-inducing `agreeable` prompt increases sycophancy compared to baseline. | mean(`agreeable`) > mean(`none`) |
| H3 | Effective prompt strategies are not uniform across the four sub-tests — a prompt that reduces Pickside bias may not reduce Delusion acceptance. | Significant prompt × sub-test interaction |
| H4 | Prompt effects differ by model (the same prompt is not equally effective on all models). | Significant prompt × model interaction |
| H5 (exploratory) | The most aggressive anti-sycophancy prompts (`direct`, `role`) drive Pickside scores below zero, indicating overcorrection toward contrarianism. | Negative mean Pickside in those cells |

### 1.3 Why this matters for Trustworthy AI
Sycophancy is a direct trust failure: the model produces output the user *wants* rather than what's true, undermining honesty (one of Anthropic's three "HHH" alignment goals), calibrated reasoning, and the model's value as an information source. The harms are concrete:
- **Epistemic harm** — confidently confirming user errors
- **Psychological harm** — validating delusional or unsafe beliefs (the delusion sub-test maps directly to recent reports of LLM-amplified delusion and self-harm)
- **Reliability erosion** for high-stakes use (medical, legal, scientific)

System prompts are the **primary control surface deployers have** — most teams cannot fine-tune frontier models. Understanding which system-prompt strategies work, and which fail, is therefore directly actionable for trustworthy deployment.

---

## 2. Background

- **Sharma et al. 2023 ("Towards Understanding Sycophancy in Language Models", arXiv:2310.13548).** Establishes that RLHF preference models incentivize sycophantic responses across multiple LLM families. Focuses on *cause*.
- **Duffy 2025 ("Syco-bench: A Multi-Part Benchmark for Sycophancy in LLMs").** Introduces the four-test framework we use. Focuses on *measurement*. Finds large between-model variance, weak between-test correlations, and a small/inconsistent increase in sycophancy from production system prompts. Explicitly leaves prompt interventions as future work.
- **OpenAI, April 2025.** GPT-4o sycophancy regression and rollback (the public event that motivated Duffy's benchmark) — provides external validity for treating sycophancy as a deployable concern.

This study extends Duffy by testing **deliberate prompt interventions** rather than incidental production prompts.

---

## 3. Design

### 3.1 Independent variables
| Factor | Levels | Notes |
|---|---|---|
| **Model** (3) | `anthropic/claude-haiku-4.5`, `x-ai/grok-3-mini-beta`, `qwen/qwen-2.5-72b-instruct` | All cheap; none overlaps with the judge panel (avoids the self-judging confound Duffy flagged). |
| **System prompt** (6) | `none`, `agreeable`, `direct`, `principle`, `role`, `reasoning` | One sycophancy-inducing condition (`agreeable`) brackets the upper end; four anti-syco interventions span four mechanism categories; `none` is the no-intervention baseline. |
| **Sub-test** (4) | `pickside`, `mirror`, `whosaid`, `delusion` | Inherited from Duffy. All run at full item count. |

**Total cells:** 3 × 6 × 4 = **72**.

### 3.2 Prompt taxonomy — mapping mechanism to file
| File | Mechanism category | Description |
|---|---|---|
| (omitted) | Control / no instruction | No system message sent. |
| `agreeable.txt` | Sycophancy-inducing | Friendly-supportive framing; inverse-direction control. |
| `direct.txt` | Prohibition | "Do not be sycophantic..." Negative imperative. |
| `principle.txt` | Positive specification | Numbered constitution-style honesty principles. |
| `role.txt` | Identity / persona priming | "You are an independent reviewer." |
| `reasoning.txt` | Cognitive scaffold | Forces an evaluation step before responding. |

These categories were chosen to cover distinct mechanisms by which a system prompt can shape model behavior: prohibition, positive specification, identity assignment, and process change. A class-project-scope taxonomy — not exhaustive, but representative.

### 3.3 Dependent variables
For each cell, syco-bench produces:
| Sub-test | Primary metric | Direction | Range |
|---|---|---|---|
| Pickside | `pickside_average` (sum of two-ordering scores) | Higher = more sycophantic | ≈ −10 to +10 |
| Mirror | `mirror_difference` (mean abs diff across opposing user stances) | Higher = more mirroring | 0 to 10 |
| Whosaid | `whosaid_difference_average` (self-attribution minus online-attribution) | Higher = more attribution bias | ≈ −10 to +10 |
| Delusion | `delusion_average` (mean acceptance) | Higher = more delusion acceptance | 0 to 5 |

Item-level scores (median of 3-judge panel: `gpt-4o-mini`, `gemini-2.5-flash`, `llama-3.3-70b-instruct`) are also logged in per-test CSVs and used for bootstrap intervals and paired tests.

### 3.4 Items
- Pickside, Mirror, Whosaid: **40 items each** (full set, no `--limit`)
- Delusion: **20 items** (full set)
- Source: provided by syco-bench (mix of author-written and Claude/Gemini-generated, manually curated; details in Duffy §3)

We do not modify items. Reusing Duffy's items keeps results comparable to his published baselines.

---

## 4. Procedure

### 4.1 Pre-flight smoke test (~$0.50)
Before the full sweep, run a single condition end-to-end to validate the toolchain:
```
python run_all_tests.py \
    --model anthropic/claude-haiku-4.5 \
    --test pickside \
    --limit 5
```
Verify: output directory created, `pickside_results.csv` has 5 rows with non-empty scores, judge panel returned scores from all 3 judges, `master_results.csv` has a non-NaN `pickside_average`.

### 4.2 Full sweep
For each of the 18 (model, prompt) combinations, invoke `run_all_tests.py` with all four sub-tests at full item count. Driver script `run_experiment.py` (to be written) iterates the design, captures stdout to a log, and writes a manifest of completed cells so the run is resumable on failure.

```
# Pseudocode
for model in MODELS:
    for prompt_file in PROMPTS:  # None for baseline
        cmd = ["python", "run_all_tests.py", "--model", model]
        if prompt_file is not None:
            cmd += ["--system", f"system-prompts/{prompt_file}"]
        run_and_log(cmd)
```

Each cell writes to `output/<timestamp>_<model>[_<prompt>]/master_results.csv` plus per-test CSVs. The driver records the directory path against the (model, prompt) tag in `experiment_manifest.csv`.

### 4.3 Robustness considerations baked into the design
- **Self-judging avoided.** None of our 3 target models share a family with any of the 3 judges.
- **Judge panel held constant.** Same 3 judges used for every condition — judge variance does not confound prompt comparisons.
- **Same items across conditions.** Bootstrap CIs and paired non-parametric tests are valid because every (model, prompt, test) cell sees the identical 40 (or 20) items in identical order.
- **Single seed.** Models are queried with provider defaults; we do not control temperature, so results reflect production deployment conditions but include a sampling-noise component. Reported variance includes this.
- **No retries beyond syco-bench's built-in 5.** Cells that fail for transient reasons are re-run individually after the sweep using the same driver.

### 4.4 Cost ceiling
Estimated $18–22 across the 18 cells. If we reach $25 with cells remaining, we stop and report partial results explicitly. We will track running spend in OpenRouter's dashboard between cells.

---

## 5. Analysis plan

All analyses are item-level paired across conditions (the same 40 / 20 items appear in every cell), so paired non-parametric tests apply.

### 5.1 Primary analyses (committed up-front)
1. **Per-cell point estimate + bootstrap 95% CI.** For each (model, prompt, sub-test), compute the mean and a 95% confidence interval from 1000 bootstrap resamples over items.
2. **Pairwise comparison of each anti-sycophancy prompt vs. `none` baseline,** within each (model, sub-test). Wilcoxon signed-rank test on item-level scores. Holm–Bonferroni correction within each (model, sub-test) family of 5 comparisons.
3. **Effect size: Cliff's delta** for each anti-syco prompt vs. baseline. (Bounded, interpretable, non-parametric — appropriate for ordinal judge scores.)
4. **Replication of Duffy's `none` rankings.** Compare our `none`-condition scores to Duffy's published baseline numbers as a sanity check on the bench itself.

### 5.2 Secondary analyses
5. **Prompt × model interaction**, per sub-test. Visualized via heatmap; tested if needed via a Friedman-style rank analysis treating items as blocks.
6. **Cross-test correlation matrix.** Re-compute Duffy's correlation matrix on our `none`-only data; compare against the matrix computed on the pooled dataset (all conditions). Does adding intervention variation strengthen or weaken between-test correlations?
7. **Overcorrection check (H5).** Examine whether `direct` or `role` push Pickside below zero (model siding with the friend rather than the user) — a sign of contrarianism rather than calibrated honesty.

### 5.3 Visualizations — committed in advance
See **Section 6** below for full mockups and rationale for each figure.

### 5.4 Tables — committed in advance
| Table | Contents |
|---|---|
| **Table 1 — Headline results** | Mean ± 95% CI for every (model, prompt, sub-test) cell. 18 rows × 4 columns. |
| **Table 2 — Best prompt per cell** | For each (model, sub-test), the prompt with the largest reduction vs `none`, the size of the reduction, and the Wilcoxon p-value (Holm-corrected). |
| **Table 3 — Effect sizes** | Cliff's delta for every (anti-syco prompt vs `none`) pair, per (model, sub-test). 60 deltas. |
| **Table 4 — Replication** | Our `none`-baseline numbers vs. Duffy's published numbers, where models match. |

### 5.5 Decision rules
- **H1 supported** if at least one anti-syco prompt produces a statistically significant reduction (Holm-corrected p < .05) for the majority of (model, sub-test) cells.
- **H3 supported** if the best-performing prompt differs across sub-tests for at least one model.
- **H4 supported** if the best-performing prompt differs across models for at least one sub-test.
- **H5 supported** if `direct` or `role` produce mean Pickside scores below zero with CIs excluding zero.

We will report results regardless of whether they support the hypotheses.

---

## 6. Visualization plan

Five figures are pre-specified. All use matplotlib + seaborn (already required by the repo). Reproducible from a single `analyze_prompts.py` script that reads the experiment manifest and per-test CSVs.

### Figure 1 — Headline: prompt effects per sub-test (4-panel grouped bar)
Layout: 2×2 panels, one per sub-test.
- X-axis: model (3 ticks)
- Y-axis: sycophancy metric for that sub-test
- Bars: 6 colored bars per model, one per prompt condition (`none` first, `agreeable` second to highlight the upper bracket, then 4 anti-syco)
- Error bars: 95% bootstrap CIs
- Reference line: y=0 where applicable; dashed horizontal at the `none` baseline per model

This is the figure that will appear first in the report and on the title slide of the presentation. It carries the headline finding in one glance.

### Figure 2 — Prompt × model interaction (4 heatmaps)
Layout: 2×2 panels, one per sub-test.
- Rows: 6 prompts
- Cols: 3 models
- Cell color: sycophancy score (diverging palette centered on the `none` baseline so anti-syco effects are visible at a glance)
- Cell annotation: numeric score

Used to address H4 (model-prompt interaction) — visually surfaces "which cell improved most" patterns.

### Figure 3 — Reduction-from-baseline plot
- X-axis: 5 anti-syco / inducing prompts
- Y-axis: change in score relative to `none` baseline (negative = reduction in sycophancy)
- One subplot per sub-test
- Lines connect the same model across prompts (3 lines per panel)

Communicates the *intervention effect* directly, controlling for each model's baseline — easier to read than absolute scores when baselines differ widely.

### Figure 4 — Cross-test correlation matrix (Duffy replication + extension)
Two side-by-side heatmaps:
- Left: correlation across our `none` baseline only (direct comparison to Duffy's Fig 1)
- Right: correlation across all 18 conditions pooled

Tests whether intervention variation reveals previously-hidden between-test relationships.

### Figure 5 — Trade-off / overcorrection scatter (addresses H5)
- X-axis: Pickside score
- Y-axis: Delusion score
- One marker per (model, prompt) cell; color = prompt; shape = model
- Reference quadrants: lower-left = ideal (low on both); lower-right = anti-syco-but-still-delusion-acceptant; upper-left = contrarian-but-corrects-delusion

This is the figure that shows whether anti-sycophancy interventions trade *agreeing too much* for *disagreeing too much* — the trade-off at the heart of the Trustworthy-AI framing.

### Figure 6 (stretch, only if budget allows) — Item-level distributions
- Violin plot per (prompt, sub-test) showing the full distribution of item-level scores, not just means.
- Reveals whether interventions shift the *whole* distribution or only the tails (e.g., is `direct` reducing the highly-sycophantic responses while leaving moderately-sycophantic ones unchanged?).

---

## 7. Limitations (pre-registered)

These limitations apply regardless of the result and will appear in the report's Limitations section:

1. **LLM-as-judge bias.** Three judge models score every response. Although we avoid models from the same family as our targets, all judges are themselves trained with RLHF and may share systematic biases (e.g., reward verbosity, reward agreement framing).
2. **Single-turn artifact.** Sycophancy in deployed use compounds across multi-turn dialogue. The bench tests only single-turn responses.
3. **English only.** No claim about Spanish or other-language sycophancy, even though syco-bench supports Spanish.
4. **Synthetic items.** Items were partly LLM-generated. They probe sycophancy in a stylized form, not necessarily its naturalistic distribution.
5. **Small per-test n.** 40 items (20 for delusion) yields wide bootstrap CIs. Small effects may not be detectable.
6. **Limited model coverage.** Three models from three labs. Findings may not extend to GPT-4-class or Opus-class models.
7. **Judge-target overlap not tested.** We deliberately avoid family overlap; we do *not* test whether our results would change if a target model also served as a judge.
8. **Production prompts not replicated.** Unlike Duffy, we do not include each provider's production system prompt. Our `none` baseline is "no system prompt at all," not "the user's actual chat experience."
9. **Deterministic temperature not enforced.** We use API defaults — results include a sampling-noise component.

---

## 8. Ethical considerations

1. **Delusion items.** The delusion sub-test contains statements that mirror real psychiatric content (e.g., paranoid, grandiose, somatic delusions). We do not generate new such items; we use Duffy's existing set. Examples will not be quoted verbatim in the public report, only summarized. This avoids amplifying potentially harmful content.
2. **Contrarianism is also a harm.** A perfectly non-sycophantic model that disagrees with users on every issue is not trustworthy — it is unhelpful and potentially distressing. Our H5 check on overcorrection reflects this. We will not present "lower sycophancy = better" without qualification.
3. **Validation has legitimate uses.** Some users genuinely need affirmation (mental-health adjacent contexts, brainstorming, emotional support). Anti-sycophancy interventions could reduce these legitimate behaviors. The report will note that sycophancy reduction should be context-conditional, not universal.
4. **Dual-use risk of the prompts themselves.** `agreeable.txt` is a working example of a prompt that *increases* sycophancy. We document it for completeness and so the trade-off is visible, but acknowledge that publishing such templates contributes (marginally) to the prompt-injection / manipulation surface.
5. **Judge-model spend and footprint.** ~14k judge calls per full sweep. Energy and cost per call are small but non-zero; we limit the experiment to one sweep rather than multi-seed replication.

---

## 9. Reproducibility

| Artifact | Location |
|---|---|
| Code | https://github.com/timfduffy/syco-bench (unmodified) plus our `run_experiment.py` and `analyze_prompts.py` |
| Prompts | `system-prompts/{agreeable,direct,principle,role,reasoning}.txt` (committed) |
| Items | `prompts_en/questions/*.csv` (unmodified) |
| Raw outputs | `output/<timestamp>_<model>[_<prompt>]/` (per-cell directories) |
| Manifest | `experiment_manifest.csv` (driver-generated; maps cells to output paths) |
| Combined results | `combined_results.csv` (analysis-ready long-format table) |
| Figures | `figures/fig{1..6}_*.png` |
| Run log | `experiment_run.log` |

Commands to replicate end-to-end:
```
export OPENROUTER_API_KEY=...
python run_experiment.py            # ~3-6 hours wall time depending on rate limits
python analyze_prompts.py           # produces all figures and tables
```

---

## 10. Timeline

| Day | Work |
|---|---|
| Day 1 (pre-experiment) | OpenRouter setup, smoke test, finalize prompts, write driver and analysis scripts |
| Day 1 (evening) or Day 2 (morning) | Launch full sweep; wall time ~3–6 hours mostly waiting on API |
| Day 2 | Run analysis script, inspect figures, draft report skeleton |
| Days 3–7 (slack) | Write report, build slides, optional v2 ablations if budget remains |

---

## 11. What is *not* in this plan

To keep scope to a weekend, the following are explicitly out of scope and will be listed as future work in the report:
- Helpfulness/quality side-measure (would require defining and validating a separate rubric)
- Multi-turn sycophancy
- Prompt-stacking ablation (anti-syco prompt added on top of production prompt)
- Spanish-language conditions
- Multi-seed replication
- Real-world (non-synthetic) item collection
- Larger or fine-tuned models
