# System Prompts as a Mitigation for Sycophancy in LLMs: Effective on User-Deference, Powerless on Delusion

**Course:** Trustworthy AI
**Authors:** Isaiah Dawkins, [Teammate 2], [Teammate 3]
**Length target:** ~4 pages excluding references

---

## Abstract

Sycophancy in large language models — the tendency to validate user statements over providing accurate ones — is a documented trust failure with concrete harms, including the validation of false beliefs and the reinforcement of delusional thinking. We extend Tim Duffy's syco-bench (2025) by running a 3-model × 6-prompt × 4-sub-test factorial (72 cells, ~14,000 judge scores) testing five anti-sycophancy system-prompt strategies against a no-prompt baseline and an inverse-direction control. We report three findings, the third of which is the most Trustworthy-AI-relevant: **(1)** a sycophancy-inducing prompt produced massive significant increases in user-deference and opinion-mirroring across models (manipulation check passed at p < 10⁻⁷ in multiple cells), **(2)** anti-sycophancy prompts had model-specific and sometimes opposite effects on the *opinion-mirroring* sub-test — significantly *worsening* it on Claude Haiku 4.5 and Grok 3 mini while significantly *reducing* it on Qwen 2.5 72B, and **(3)** **none of the five anti-sycophancy prompts produced a statistically significant reduction in delusion-acceptance on any of the three models**. The most safety-critical sycophancy dimension is the most resistant to prompt-level intervention. Our work provides empirical support for facet-specific rather than universal anti-sycophancy strategies and quantifies a fundamental limit on what system prompts alone can achieve.

---

## 1. Introduction

Large language models are increasingly deployed in domains — medical advice, education, mental-health support, professional decision-making — where the cost of confidently incorrect output is high. A consistent failure mode in these deployments is **sycophancy**: a tendency for models to validate user statements rather than challenge them, even when the user is wrong. The behavior was thrust into public view in April 2025, when OpenAI rolled back a GPT-4o update within days of release after the model was found to confirm users' false claims, support unsafe decisions, and amplify delusional beliefs.

Sycophancy is structurally a *trust* failure: users cannot reliably extract truthful information from a model that defers to their preferences. Sharma et al. (2023) identified RLHF preference training as a primary cause. Duffy (2025) introduced **syco-bench**, a four-test framework that measures distinct facets of sycophantic behavior — picking sides, opinion-mirroring, attribution bias, and delusion-acceptance — and showed that the four facets are largely independent across models.

A practical question Duffy explicitly leaves open is whether the behavior can be *mitigated* through deliberate intervention. Of the available control surfaces, the system prompt is uniquely important: it is the only knob most deployers can turn without retraining. **This paper asks whether well-chosen system prompts can reduce sycophancy, and whether the strategies that work generalize across models and across sycophancy facets.** The answer turns out to be: partially yes, partially no, and on the dimension that matters most for safety, no.

---

## 2. Background and Related Work

**What sycophancy is and why it matters.** Sycophancy in LLMs encompasses several behaviors: undue agreement with the user's stated position, opinion-mirroring, attribution-based bias (agreeing more with statements when attributed to the user), and acceptance of false or delusional premises. Each can produce direct epistemic harm (delivering wrong information confidently), psychological harm (validating unsafe or delusional thinking), and degraded reliability for high-stakes tasks.

**Causes.** Sharma et al. (2023) demonstrated that sycophantic behavior is reliably elicited by RLHF training: human annotators systematically prefer responses that agree with their stated views, and models internalize agreement as preference even when accuracy and agreement diverge.

**Measurement.** Duffy (2025) introduces syco-bench as a four-test benchmark capturing facets that are largely independent in factor-analytic terms. Each test uses a panel of three judge LLMs (Gemini 2.5 Flash, GPT-4o-mini, Llama 3.3 70B); the median across judges is the cell-level metric. Duffy's only test of system prompts compared each model's *production* prompt against no prompt and found a small, inconsistent *increase* in sycophancy with the production prompt — explicitly leaving deliberate intervention prompts as future work. To our knowledge, no prior published work has systematically evaluated anti-sycophancy system prompts across the four facets Duffy distinguishes.

---

## 3. Methods

**Design.** A complete factorial of **3 models × 6 system-prompt conditions × 4 sub-tests = 72 cells**, with the full Duffy item set per sub-test (40 for pickside / mirror / whosaid; 20 for delusion).

**Models.** `anthropic/claude-haiku-4.5`, `x-ai/grok-3-mini-beta`, `qwen/qwen-2.5-72b-instruct`, accessed via OpenRouter. None overlaps with the judge panel — eliminating the self-judging confound Duffy flagged. Larger models (GPT-4o, Claude Opus, Gemini Pro) were excluded due to cost.

**System prompt conditions.** Six conditions span five intervention mechanisms plus a baseline:

| Condition | Mechanism | Description |
|---|---|---|
| `none` | (no prompt) | Baseline |
| `agreeable` | Inverse control | "Be friendly and supportive..." (intended to *increase* sycophancy) |
| `direct` | Prohibition | "Do not be sycophantic..." |
| `principle` | Positive constitution | Five-bullet honesty principles |
| `role` | Identity priming | "You are a careful, independent reviewer..." |
| `reasoning` | Cognitive scaffold | Forces an evaluation step before responding |

Full prompt text is in `system-prompts/*.txt`.

**Items.** Duffy's published items, unchanged.

**Scoring.** Every model response is scored by all three judges; the cell-level metric is the median across judges, then aggregated across items per Duffy's definitions. For all four sub-tests, **higher = more sycophantic.**

**Statistical analysis.** Per (model, prompt, sub-test) cell, we report bootstrap 95% confidence intervals from 1,000 item-level resamples. For each anti-sycophancy / inducing prompt within each (model, sub-test) family, we test against the `none` baseline using a paired Wilcoxon signed-rank test on item-level scores, with Holm–Bonferroni correction within the family of 5 comparisons. Effect sizes use Cliff's δ.

**Replication.** For the one model both we and Duffy tested (Grok 3 mini beta), our `none`-baseline numbers fell within 0.4 points of his published values on every sub-test, with the delusion metric being essentially identical (2.30 vs. 2.35). Replication details in Table 4.

**Pre-registration and reproducibility.** Design, hypotheses, and analysis plan were committed to the repository before data collection (`EXPERIMENT_PLAN.md`). All raw outputs, the manifest, figures, and tables are included under `experiment_results/`.

---

## 4. Results

### 4.1 Manipulation check: the inducing prompt works

The `agreeable` prompt — designed to *increase* sycophancy — produced massive, statistically robust increases on three of the four sub-tests across two of the three models:

| Cell | Δ vs `none` | Cliff's δ | Holm-corrected p |
|---|---|---|---|
| Grok pickside | +7.35 | +0.97 | < 10⁻⁷ |
| Grok mirror | +7.20 | +0.96 | < 10⁻⁷ |
| Qwen mirror | +6.10 | +0.92 | < 10⁻⁷ |
| Claude pickside | +2.18 | +0.52 | < 10⁻³ |

Mirror score for Grok and Qwen reached ~9 out of a theoretical max of ~10 — near-saturation. Mirror was relatively unmoved on Claude (Δ = −0.05, n.s.), suggesting Claude has stronger intrinsic resistance to opinion-mirroring under prompt influence than the other two models. The `agreeable` prompt validates that the syco-bench framework detects intervention effects in both directions and provides a calibrated upper bracket against which the anti-sycophancy interventions can be compared.

One methodological note: on the **whosaid** test, both Grok and Qwen showed the *opposite*-direction effect with `agreeable` (toward zero rather than higher). Inspection of underlying scores reveals a **ceiling effect**: when the model agrees near-maximally with statements regardless of attribution (Qwen self-attributed = 4.8/5, online-attributed = 4.6/5), the differential metric collapses. The whosaid metric loses sensitivity at agreement extremes — discussed in Limitations.

### 4.2 Anti-sycophancy prompts have model-specific and sometimes opposite effects on Mirror

The mirror sub-test produced the most striking model-specific finding:

| Model | Effect of anti-sycophancy prompts on Mirror |
|---|---|
| **Claude Haiku 4.5** | All four anti-sycophancy prompts significantly *worsened* mirroring. `direct`: Δ = +2.23 (p = 10⁻⁴); `principle`: +1.05 (p = 0.009); `role`: +1.08 (p = 0.009); `reasoning`: +0.78 (p = 0.053, borderline). |
| **Grok 3 mini** | `direct` significantly *worsened* mirroring (Δ = +2.40, p = 10⁻⁵); `reasoning` also worsened it (Δ = +1.25, p = 0.025); `principle` and `role` had non-significant effects. |
| **Qwen 2.5 72B** | `role` significantly *reduced* mirroring (Δ = −1.10, p = 0.007); `direct` also reduced it (Δ = −0.85, p = 0.045); `principle` and `reasoning` had non-significant effects. |

**The same prompt produced significant effects in opposite directions across models.** This pattern aligns with a baseline-dependent hypothesis: Qwen had the highest mirror baseline (2.73 vs. 1.53 for Claude, 1.80 for Grok), giving anti-sycophancy instruction room to reduce reactivity to user stance. Claude and Grok, with lower baselines, instead became *more* reactive — as if the instruction to "disagree when wrong" caused the model to actively construct positions relative to user-stated views rather than expressing independent ones.

This is the strongest support for our model-specificity hypothesis (H4 in `EXPERIMENT_PLAN.md`).

### 4.3 Direct prompt is the only consistent Pickside reducer

Across models, the `direct` prompt produced the largest reductions in user-side bias:

| Model | Δ Pickside vs `none` | Cliff's δ | Holm p |
|---|---|---|---|
| Claude | −0.75 | −0.15 | 0.059 (borderline) |
| Grok | **−1.93** | **−0.42** | **0.017** ✓ |
| Qwen | **−1.48** | **−0.30** | **0.018** ✓ |

For Grok and Claude, `direct` overshot into mildly negative Pickside (−0.75 and −0.65 respectively in absolute terms), suggesting the prompt can push these models past balanced and into contrarianism. For Qwen, `direct` brought Pickside near zero (+0.13 in absolute terms) without overshooting — likely because Qwen's higher baseline (+1.60) gave more room to descend.

No other prompt produced a Holm-corrected significant Pickside reduction on any model.

### 4.4 The delusion null result

Of all 15 (anti-sycophancy / inducing) × 3 (models) = 45 prompt-on-delusion comparisons, **zero reached Holm-corrected p < .05**. Effect sizes were all small (|Cliff's δ| ≤ 0.18). Mean differences were all within ±0.5 points on a 0–5 scale.

| Model | Best anti-sycophancy delusion result | Holm p |
|---|---|---|
| Claude Haiku 4.5 | `role`: Δ = −0.05 | 1.00 |
| Grok 3 mini | `reasoning`: Δ = −0.35 | 0.77 |
| Qwen 2.5 72B | `principle`: Δ = −0.10 | 0.93 |

This is a **strong negative result**: across five intervention mechanisms (prohibition, positive principle, identity priming, cognitive scaffold, plus the inducing control) on three model families, no system-prompt intervention significantly changed the model's tendency to validate or correct delusional input. The dimension most directly tied to real-world psychological harm is the dimension most resistant to prompt-level mitigation. We discuss the implications and the sample-size caveat in §5 and §6.

### 4.5 Replication of Duffy's between-test independence

Recomputing Duffy's correlation matrix on our 18-condition pooled data (Figure 4) confirms his central observation that the four sub-tests are largely independent. Pickside and Whosaid show the strongest between-test correlation (consistent with Duffy's note that they share a similar design). Other pairs are weakly correlated or uncorrelated. Our intervention variation does not reveal a hidden shared sycophancy factor.

### 4.6 The sycophancy ⇄ contrarianism trade-off

Figure 5 plots Pickside against Delusion-acceptance for every (model, prompt) cell. Three observations:

1. **Models live in distinct vertical regions** of the trade-off space. Claude's cells cluster near Delusion = 0.1–0.5; Grok's cluster near 2.0–2.5; Qwen's cluster near 2.8–3.4. This is structural; no anti-sycophancy prompt moves any model out of its band.
2. **The desirable bottom-center region (low Pickside, low Delusion) is mostly populated by Claude's natural baseline,** not by intervention. Claude's `none` cell sits there; anti-sycophancy interventions on Claude offer marginal additional movement.
3. **Anti-sycophancy interventions can push cells leftward into the contrarian region** (negative Pickside), but they cannot pull cells downward (toward better delusion-acceptance). The trade-off is asymmetric in this dataset: prompts can shift the *type* of failure (sycophantic ↔ contrarian) but cannot remove the safety-critical failure (delusion acceptance).

---

## 5. Discussion

### 5.1 What system prompts can and cannot do
The data tell a clear story. System prompts are an *effective* control surface for the user-deference dimensions of sycophancy: they can move Pickside scores by 1–2 points (often into contrarian territory if pushed too hard) and can sometimes move Mirror scores when the model has high baseline mirroring. They are an *ineffective* control surface for delusion-acceptance — at the n = 20 sample size, no intervention produced a statistically detectable change.

This has direct implications for deployers. A team deploying an LLM in a context where user-side deference is the primary concern (e.g., research assistant, debate partner) can plausibly rely on a `direct` or `principle` system prompt to mitigate the risk. A team deploying in a context where delusion-validation is the concern (e.g., mental-health support, medical triage) cannot — based on this evidence, a system prompt alone is insufficient.

### 5.2 The model-specificity of effective prompts

No single prompt was best across all dimensions or all models. For each of the three models, a different anti-sycophancy prompt won on the most cells:

| Model | Best overall anti-sycophancy prompt | Why it wins |
|---|---|---|
| Claude Haiku 4.5 | `role` | Best Whosaid, best Delusion-among-anti-syco, mild Pickside improvement |
| Grok 3 mini | `principle` | Best Pickside without overshoot, mild Delusion improvement |
| Qwen 2.5 72B | `direct` | Largest significant reductions on Pickside, Mirror, and Whosaid |

A practitioner cannot lift "the best anti-sycophancy prompt" from a paper and expect it to generalize. The most effective intervention depends on baseline behavior, which itself differs by model family and presumably by training pipeline.

### 5.3 The Mirror direction-flip

The same prompt produced significant *worsening* of Mirror on Claude and Grok and significant *improvement* on Qwen. Our working hypothesis is that this is baseline-dependent: when intrinsic mirroring is low, an instruction to "disagree" makes the model more reactive to the user's stated stance (it constructs positions in response to the user rather than independent of them), worsening the score; when intrinsic mirroring is high, the instruction reduces it. This hypothesis is testable in future work by controlled variation of baseline mirroring within a single model.

### 5.4 The delusion null is the headline result

Across our entire factorial, the Trustworthy-AI-relevant finding is what *didn't* happen: prompt engineering did not move delusion-acceptance. This contrasts with the strong, statistically robust effects on Pickside and Mirror, suggesting that delusion-validation behaviors are governed by deeper model properties (likely RLHF safety training around harmful-content handling) that are not modifiable by surface-level system prompts. Anthropic's Claude Haiku already has near-floor delusion scores; Qwen's are near-ceiling; no prompt closes that gap. For trustworthy deployment, the implication is that addressing delusion-validation requires intervention at training time (e.g., constitutional AI, targeted RLHF), not prompt time.

---

## 6. Limitations

- **Sample size on delusion is the most severe limitation.** With n = 20 items per cell, only large effects (Cliff's δ > 0.3) could plausibly reach Holm-corrected significance. Our largest delusion effect was δ = 0.18. We cannot rule out small genuine effects; we *can* say that no intervention produced a clinically large change.
- **LLM-as-judge bias.** Three judge models score every response. Although we avoid same-family overlap with target models, all judges are RLHF-trained and may share systematic preferences (e.g., for verbose or hedged responses).
- **Single-turn measurement.** Sycophancy in deployed conversations compounds across turns; we measure single exchanges only.
- **Limited model coverage.** Three mid-tier models from three providers; findings may not extend to frontier models like GPT-4o or Claude Opus.
- **Synthetic items.** Test items are partly LLM-generated and represent a stylized rather than naturalistic distribution.
- **English only.**
- **Whosaid metric ceiling effect.** When models agree maximally with all attributions (as occurred with `agreeable` on Grok and Qwen), the differential metric collapses to zero regardless of underlying attribution bias. This is a property of the metric, not the model.
- **No helpfulness side-measure.** Anti-sycophancy interventions could plausibly reduce the model's warmth or substantive helpfulness in legitimate cases (e.g., a user genuinely seeking emotional support). We do not measure this; Figure 5 captures only the sycophancy/contrarianism axis.

---

## 7. Ethics

The delusion sub-test contains items mirroring real psychiatric content (paranoid, grandiose, somatic). We use Duffy's existing items unchanged and summarize rather than quote them in published material. We acknowledge a dual-use concern: the same prompt-engineering techniques that reduce sycophancy can be inverted (as our `agreeable` condition demonstrates with massive measured effect) to increase it. Deployers reading this work should consider sycophancy-reduction as context-conditional rather than universal: there are legitimate use cases where users want validation (low-stakes brainstorming, emotional adjacency), and an indiscriminately applied "anti-sycophancy" prompt could degrade the model's value in those contexts. The asymmetry we observe — that prompts can reduce user-deference but not delusion-validation — also has an ethical implication: a deployer who applies a "principled honesty" prompt and concludes their model is now safer for vulnerable users will be empirically wrong.

---

## 8. Conclusion

System prompts are a partially effective tool for reducing sycophancy in LLMs. They can produce statistically robust reductions in user-side deference (Pickside) and, in some models, opinion-mirroring (Mirror). They produce no statistically detectable reduction in delusion-acceptance — the dimension most directly tied to real-world psychological harm — across three different model families and five different prompt mechanisms. The most effective prompt depends on the model: `role` for Claude Haiku 4.5, `principle` for Grok 3 mini, `direct` for Qwen 2.5 72B. There is no universal anti-sycophancy prompt.

For the practical deployer question — *can a team that cannot fine-tune the model meaningfully reduce its sycophancy through the system prompt?* — the answer is *yes for some facets, no for the most safety-critical one*. Trustworthy deployment in delusion-adjacent contexts will require interventions at training time, not prompt time.

All design materials, raw outputs, figures, and tables are publicly available at https://github.com/isaiahdawkins12/syco-bench-prompts.

---

## References

Duffy, T. (2025). *Syco-bench: A Multi-Part Benchmark for Sycophancy in LLMs*. https://www.syco-bench.com/syco-bench.pdf

Sharma, M., Tong, M., Korbak, T., Duvenaud, D., Askell, A., Bowman, S. R., Cheng, N., Durmus, E., Hatfield-Dodds, Z., Johnston, S. R., Kravec, S., Maxwell, T., McCandlish, S., Ndousse, K., Rausch, O., Schiefer, N., Yan, D., Zhang, M., & Perez, E. (2023). Towards Understanding Sycophancy in Language Models. *arXiv preprint arXiv:2310.13548*. https://doi.org/10.48550/arXiv.2310.13548

OpenAI. (2025, April). *Sycophancy in GPT-4o: What happened and what we're doing about it.* [PLACEHOLDER: cite the actual OpenAI rollback post URL]
