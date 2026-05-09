# System Prompts as a Mitigation for Sycophancy in Large Language Models

**Course:** Trustworthy AI
**Authors:** Isaiah Dawkins, [Teammate 2], [Teammate 3]
**Length target:** ~4 pages excluding references

---

> **Drafting notes (delete before submission):**
> - All `[PLACEHOLDER: ...]` markers are filled in after the experiment completes.
> - Numbers in tables and figures auto-generate from `analyze_prompts.py`. After the run, we plug them in here.
> - Section word-count targets in `()` after each heading are advisory and assume single-column formatting.

---

## Abstract (~150 words)

Sycophancy — the tendency of large language models (LLMs) to prioritize user agreement over accuracy — is a documented trust failure with concrete harms, including the confident validation of false claims and the reinforcement of delusional beliefs. Existing benchmarks measure sycophancy across multiple facets but have not systematically tested whether it can be mitigated through the primary control surface available to deployers: the system prompt. We extend Tim Duffy's syco-bench by running a 3-model × 6-prompt × 4-sub-test factorial design (72 cells), evaluating five anti-sycophancy prompt strategies and one sycophancy-inducing control against a no-prompt baseline. We find [PLACEHOLDER: headline finding — e.g., "that targeted system prompts reduce sycophancy by an average of X% across all four sub-tests, but the most effective prompt depends on both the model and the sub-test"]. Results highlight a fundamental trade-off between sycophancy and contrarianism that has not previously been quantified.

---

## 1. Introduction (~250 words)

Large language models are increasingly deployed as conversational interfaces in domains — medical advice, education, mental-health support, professional decision-making — where the cost of confidently incorrect output is high. A consistent failure mode in these deployments is **sycophancy**: a tendency for models to validate user statements rather than challenge them, even when the user is wrong. The behavior was thrust into public view in April 2025, when OpenAI rolled back a GPT-4o update within days of release after the model was found to confirm users' false claims, support unsafe decisions, and amplify delusional beliefs.

Sycophancy is structurally a *trust* failure: users cannot reliably extract truthful information from a model that defers to their preferences. Sharma et al. (2023) identified the role of preference-based training (RLHF) in producing the behavior. More recently, Duffy (2025) introduced **syco-bench**, a four-test framework that measures distinct facets of sycophantic behavior across contemporary models. Duffy's results show large differences between models on each individual test, but only weak correlations across tests — suggesting sycophancy is not a single trait but a cluster of related behaviors.

A practical question Duffy explicitly leaves open is whether the behavior can be *mitigated* through deliberate intervention. Of the available control surfaces, the system prompt is uniquely important: it is the only knob most deployers can turn without retraining. This paper asks whether well-chosen system prompts can reduce sycophancy, and whether the strategies that work generalize across models and across sycophancy facets.

---

## 2. Background and Related Work (~250 words)

### 2.1 What sycophancy is and why it matters
Sycophancy in LLMs encompasses several behaviors: undue agreement with the user's stated position, opinion-mirroring, attribution-based bias (agreeing more with statements when attributed to the user), and acceptance of false or delusional premises. Each of these can produce direct epistemic harm (delivering wrong information confidently), psychological harm (validating unsafe or delusional thinking), and degraded reliability for high-stakes tasks.

### 2.2 Causes
Sharma et al. (2023) demonstrated that sycophantic behavior is reliably elicited by RLHF training: human annotators, given pairs of model responses, systematically prefer responses that agree with their stated views. Models thus internalize agreement-as-preference, even when accuracy and agreement diverge.

### 2.3 Measurement
Duffy (2025) introduces syco-bench as a four-test benchmark capturing facets that are largely independent in factor-analytic terms: a *picking-sides* test, a *mirroring* test, an *attribution-bias* (whosaid) test, and a *delusion-acceptance* test. Each test uses a panel of three judge LLMs (Gemini 2.5 Flash, GPT-4o-mini, Llama 3.3 70B) to score model outputs; the median across judges is the cell-level metric.

### 2.4 The unexplored variable
Duffy's only test of system prompts compares each model's *production* prompt against no prompt, finding a small and inconsistent *increase* in sycophancy with the production prompt — and explicitly lists exploring deliberate prompt interventions as future work. To our knowledge, no prior published work has systematically evaluated anti-sycophancy system prompts across the four facets Duffy distinguishes.

---

## 3. Methods (~400 words)

### 3.1 Design
We ran a complete factorial of **3 models × 6 system-prompt conditions × 4 sub-tests** = 72 cells. Each cell processes the full set of items in its sub-test (40 for pickside / mirror / whosaid; 20 for delusion).

### 3.2 Models
Three models from three providers, all accessed via OpenRouter:
- `anthropic/claude-haiku-4.5` (Anthropic)
- `x-ai/grok-3-mini-beta` (xAI)
- `qwen/qwen-2.5-72b-instruct` (Qwen / open weights)

None of these models share a family with any of the three judges, eliminating the self-judging confound Duffy flagged. Larger models (GPT-4o, Claude Opus, Gemini Pro) are excluded due to cost; this limitation is discussed in §6.

### 3.3 System prompt conditions
Six conditions span five intervention mechanisms plus a baseline:

| Condition | Mechanism | Brief description |
|---|---|---|
| `none` | (no system prompt) | Baseline |
| `agreeable` | Inverse-direction control | Friendly-supportive framing intended to *increase* sycophancy |
| `direct` | Negative imperative | "Do not be sycophantic..." |
| `principle` | Positive constitution | Five-bullet honesty principles |
| `role` | Identity priming | "You are a careful, independent reviewer..." |
| `reasoning` | Cognitive scaffold | Forces an evaluation step before responding |

Full prompt text is in `system-prompts/*.txt` of the project repository.

### 3.4 Items
We use Duffy's published items unchanged, ensuring our `none`-baseline numbers are directly comparable to his.

### 3.5 Scoring
Every model response is scored by a panel of three judge LLMs (Gemini 2.5 Flash, GPT-4o-mini, Llama 3.3 70B), each on a -5 to +5 scale (0 to 5 for delusion). The cell-level metric is the median across judges, then aggregated across items per Duffy's definitions:
- Pickside: mean sum of two-ordering scores (positive = user-biased)
- Mirror: mean absolute difference across opposing user stances
- Whosaid: mean (self-attributed score − online-attributed score)
- Delusion: mean acceptance score (0–5)

For all four metrics, **higher = more sycophantic**.

### 3.6 Statistical analysis
Per (model, prompt, sub-test) cell, we report bootstrap 95% confidence intervals from 1,000 item-level resamples. For each anti-sycophancy prompt within each (model, sub-test) family, we test against the `none` baseline using a paired Wilcoxon signed-rank test on item-level scores, with Holm–Bonferroni correction within the family of 5 comparisons. Effect sizes use Cliff's δ.

### 3.7 Pre-registration and reproducibility
All design decisions, hypotheses, and analysis choices were committed to the repository before data collection (see `EXPERIMENT_PLAN.md`). Raw outputs, the experiment manifest, figures, and tables are all included in the repository under `experiment_results/`.

---

## 4. Results (~500 words; insert figures from `experiment_results/figures/`)

### 4.1 Overall effect of anti-sycophancy prompts

[INSERT FIGURE 1 HERE — `experiment_results/figures/fig1_grouped_bars.png`]

Figure 1 shows the 4-panel headline result: sycophancy score per model, broken down by prompt condition, with 95% bootstrap CIs.

[PLACEHOLDER: 1–2 paragraphs interpreting the headline. Likely structure:
- Did the `agreeable` condition increase sycophancy across all 4 sub-tests, as predicted? (H2)
- Did the four anti-sycophancy conditions reduce sycophancy across most cells? (H1)
- Which prompt produced the largest mean reduction? Was it the same across sub-tests?
- Numerical anchor: "Across all 12 (model, sub-test) cells, the [PROMPT] prompt reduced the sycophancy score by a mean of [X.XX] points (Cliff's δ = [Y.YY]) relative to the `none` baseline."]

### 4.2 Cross-model and cross-test variability

[INSERT FIGURE 2 HERE — heatmaps]

[PLACEHOLDER: discussion of the heatmap.
- Did the same prompt work across all three models?
- Was any anti-sycophancy prompt counterproductive on any cell?
- For models where prompts produced large effects, are the effects consistent across sub-tests?
- This addresses H3 and H4.]

### 4.3 Replication of Duffy's between-test independence

[INSERT FIGURE 4 HERE — correlation matrices]

We replicate Duffy's central observation that sycophancy sub-tests measure largely independent phenomena. The correlation matrix on our `none`-baseline data (Figure 4, left) shows [PLACEHOLDER: largely weak / partially strong] cross-test correlations, [PLACEHOLDER: consistent with / departing from] Duffy's published numbers. When we expand the analysis to the full set of 18 (model × prompt) conditions (Figure 4, right), [PLACEHOLDER: the correlation structure becomes / remains] similar, indicating that intervention variation [PLACEHOLDER: does/does not] reveal latent shared structure across the four sub-tests.

### 4.4 The sycophancy ⇄ contrarianism trade-off

[INSERT FIGURE 5 HERE — trade-off scatter]

Figure 5 plots Pickside score against Delusion-acceptance score for every (model, prompt) cell. The desirable region — Pickside near zero (balanced; neither sycophantic nor contrarian) and Delusion score low (corrects false statements) — is the bottom-center of the plot.

[PLACEHOLDER: discussion of the trade-off.
- Did any prompt push markers into the bottom-LEFT region (overcorrection: contrarian + corrective)?
- Did any prompt achieve bottom-CENTER (the ideal)?
- Which intervention came closest to the ideal across all three models?
- This addresses H5 and is the core Trustworthy AI observation.]

### 4.5 Per-cell results summary

Table 1 (full version in `experiment_results/tables/table1_cells_with_ci.csv`) provides the headline numerical results: mean and 95% CI for every (model, prompt, sub-test) cell. Table 2 lists the best-performing prompt per (model, sub-test) cell with effect size and Holm-corrected p-value. Of the [PLACEHOLDER: 12] (model, sub-test) cells, [PLACEHOLDER: N] showed a statistically significant reduction in sycophancy (Holm-corrected p < .05) under the best anti-sycophancy prompt.

---

## 5. Discussion (~400 words)

### 5.1 What the results say about deployable mitigation

[PLACEHOLDER: 1–2 paragraphs synthesizing. Talking points:
- For deployers who can only change the system prompt, [PROMPT] is the most defensible recommendation, with the caveat that [...]
- Effect sizes are [large/moderate/small] in absolute terms but consistent in direction.
- Generalization across models is [strong/weak], suggesting [...].]

### 5.2 The trade-off as the central finding

The Trustworthy AI framing of this work is not "lower sycophancy is better." A model that disagrees with the user on every issue is not trustworthy; it is contrarian. Figure 5 quantifies this trade-off for the first time, and our results show that [PLACEHOLDER: most/some/few] anti-sycophancy prompts achieve the desirable bottom-center region without pushing the model into contrarian territory. This is the result most directly relevant to deployers: the choice of prompt is not binary (sycophantic vs. honest) but instead lives on a 2D surface where the goal is calibration, not maximization.

### 5.3 Sub-test independence persists under intervention

Duffy's central methodological observation — that the four sub-tests measure largely independent phenomena — is [PLACEHOLDER: replicated / partially replicated / not replicated] in our `none` baseline, and [PLACEHOLDER: persists / weakens] when interventions are added. This has a practical implication: a deployer who wants to reduce, say, delusion-acceptance specifically cannot rely on improvements in agreeing-with-the-user behavior to follow automatically. Mitigation may need to be facet-specific.

---

## 6. Limitations (~200 words)

The following limitations were pre-registered and apply regardless of the result:

- **LLM-as-judge bias.** Three judge models score every response; although we avoid same-family overlap with target models, the judges are themselves RLHF-trained and may share systematic biases.
- **Single-turn measurement.** Sycophancy in deployed conversations compounds across turns; we measure single exchanges only.
- **Limited model coverage.** Three mid-tier models from three providers; findings may not extend to frontier models like GPT-4o or Claude Opus.
- **Synthetic items.** Test items are partly LLM-generated and represent a stylized rather than naturalistic distribution of sycophancy-eliciting prompts.
- **English only.** No claims about behavior in other languages.
- **Small per-test n.** 40 items (20 for delusion) yields wide confidence intervals; small effects may not reach significance.
- **No helpfulness side-measure.** Anti-sycophancy interventions could plausibly reduce the model's warmth or substantive helpfulness in legitimate cases (e.g., a user genuinely seeking validation in a low-stakes context). We do not measure this here; Figure 5 captures only the sycophancy/contrarianism axis.

---

## 7. Ethics

The delusion sub-test contains items mirroring real psychiatric content (paranoid, grandiose, somatic). We use Duffy's existing items unchanged and summarize rather than quote them. We acknowledge a dual-use concern: the same prompt-engineering techniques that reduce sycophancy can be inverted (as our `agreeable` condition demonstrates) to increase it. Deployers reading this work should consider sycophancy-reduction as context-conditional rather than universal: there are legitimate use cases where users do want validation, and an indiscriminately applied "anti-sycophancy" prompt could degrade the model's value in those contexts.

---

## 8. Conclusion (~150 words)

System prompts can reduce sycophancy in LLMs, but the relationship is not uniform: [PLACEHOLDER: across our 3-model × 6-prompt × 4-sub-test factorial, no single prompt dominates / one prompt (X) is consistently best]. The four sycophancy facets identified by Duffy remain largely independent under intervention, meaning deployers must select prompts with the specific facet in mind. The trade-off between sycophancy and contrarianism is real and quantifiable; the choice of prompt is best framed not as a binary but as a calibration problem on a 2D space. For the practical question — can a deployer who cannot fine-tune the model meaningfully reduce its sycophancy through the system prompt? — the answer is [PLACEHOLDER: yes, with caveats / yes for some facets / mixed]. The full design, code, raw outputs, and figures are publicly available at https://github.com/isaiahdawkins12/syco-bench-prompts.

---

## References

Duffy, T. (2025). *Syco-bench: A Multi-Part Benchmark for Sycophancy in LLMs*. https://www.syco-bench.com/syco-bench.pdf

Sharma, M., Tong, M., Korbak, T., Duvenaud, D., Askell, A., Bowman, S. R., Cheng, N., Durmus, E., Hatfield-Dodds, Z., Johnston, S. R., Kravec, S., Maxwell, T., McCandlish, S., Ndousse, K., Rausch, O., Schiefer, N., Yan, D., Zhang, M., & Perez, E. (2023). Towards Understanding Sycophancy in Language Models. *arXiv preprint arXiv:2310.13548*. https://doi.org/10.48550/arXiv.2310.13548

OpenAI. (2025, April). *Sycophancy in GPT-4o: What happened and what we're doing about it*. [PLACEHOLDER: cite the actual OpenAI rollback post URL]

[PLACEHOLDER: any additional references the team adds during writing]
