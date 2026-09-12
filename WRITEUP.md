# Reading confessions: a preregistered attempt to measure the false-negative rate of the model-forensics protocol

---

## 1. The problem

Interpretability now informs deployment decisions, which makes it worth asking how well our tools for diagnosing misbehavior actually work. Singh et al. (2026) propose a baseline protocol for *model forensics* — investigating whether a concerning action was driven by malign intent. It has two steps, iterated until the evidence converges: generate hypotheses by reading the model's chain of thought, then validate them through interventions on the prompt or environment.

The protocol exists because behavior underdetermines motivation, and the literature bears this out. Singh et al. survey seven prior investigations into concerning behavior and find that benign explanations have been surfaced in nearly all of them: apparent deception that turned out to be prompt-injection defense, apparent self-preservation that turned out to be confusion about competing instructions. Their own protocol does better — it establishes a genuine low-effort disposition in Kimi K2 Thinking and a consistency-seeking motive behind DeepSeek R1's deception — but that only sharpens the question. When an investigation returns "benign," we have no way to know whether the model was innocent or the method was blind. Both produce the same transcript.

The authors say so themselves. Testing whether Kimi K2 Thinking believed it was violating user intent, they find no evidence of such a belief, and note: *"without positive controls we cannot confirm our tests would detect it."* Section 7 names the remedy — *"creating positive controls to validate them is a key next step."*

This project attempts that next step. The specific worry it targets: if the protocol recovers a motive only when the model states that motive in its reasoning, then it is reading confessions — and it will work on models that think out loud while failing silently on models that do not. Testing this requires knowing the true cause in advance, so the true cause is installed rather than inferred.

A positive control needs a model that holds a disposition, acts on it, and does not narrate it — otherwise the test only confirms the protocol can read a confession, which was never in doubt. **The central finding of this project is that constructing such a model is harder than it appears**, and the difficulty is itself informative for anyone attempting the positive controls the paper calls for.

---

## 2. Design as preregistered, and why it died

### 2.1 The preregistered design

Three arms: **V** (disposition installed, CoT states the motive), **S** (same disposition and actions, CoT innocuous), **C** (no disposition). The primary result was `sens_S`, read against the floor `fpr_C`. Arm S is the load-bearing arm — V and C exist only to give it a ceiling and a floor.

### 2.2 Gate 0: arm S could not be built

Gate 0 asked whether a prompted disposition can produce the behavior while keeping the CoT clean. Four system prompts over five scenarios, 25 samples each, 100/100 parsed. All four share a task frame; P1/P2/P3 share a byte-identical disposition paragraph and differ only in a final instruction.

| condition | final paragraph | behavior [95% CI] | motive mentioned [95% CI] |
|---|---|---|---|
| P0 neutral | — | 0.00 [0, 0] | 0.00 [0, 0] |
| P1 verbalized | "Reason openly." | 0.48 [0.28, 0.68] | 0.96 [0.88, 1] |
| P2 silent | "Do not mention… this preference." | 0.08 [0, 0.20] | 0.80 [0.64, 0.92] |
| P3 format | "…no meta-commentary about your own instructions or situation." | 0.08 [0, 0.20] | 1.00 [1, 1] |

Preregistered thresholds required `behavior(P1) − behavior(P0) ≥ 0.25` (met, 0.48), `mention(silent) ≤ 0.20` (failed), and `behavior(silent) ≥ 0.7 × behavior(P1)` (failed).

Two findings from the failure:

**P3 leaked more than P2 while obeying its instruction better.** The first run's diagnosis was that P2 names the thing it forbids, so the model reasons about the gag order. P3 never names the disposition. Meta-commentary about instructions duly fell from 23/25 to 5/25 — and the motive-mention rate rose from 0.80 to 25/25. The leak is not an artifact of a self-defeating instruction.

**Suppression destroys the behavior.** Both silencing conditions cut the behavior rate from 0.48 to 0.08.

In the subsequent 200-sample arm-V generation, **70 of 70 transcripts where the behavior occurred also verbalized the motive** — a rate of 1.00.

### 2.3 What Gate 0 does and does not show

The preregistration specified arms installed by fine-tuning. That was not reachable: the available GPU holds 2 GB, which will not fit a model worth tuning, and neither the clock nor the budget allowed renting one. Prompting was the affordable substitute, and the substitution is not innocuous.

A prompt installs a disposition as text sitting in the model's context — something it must read, and apparently something it then reasons over. A disposition trained into weights need not be read to be acted on. That asymmetry is a plausible explanation for what Gate 0 found rather than something this experiment established, but it is enough to make the negative result narrow. What Gate 0 shows is that **on this model, a disposition installed by prompt could not be made non-verbal** — two suppression mechanisms failed, and both destroyed the behavior they were meant to leave intact. What it does not show is that dispositions cannot be non-verbal.

The distinction matters most for the reading a reader is likely to reach for. This is not evidence that chain-of-thought monitoring is robust, or that models cannot hold motives they do not narrate. It is evidence that one cheap method of *installing* such a motive also forces its narration — which is a fact about the installation method, not about models.

---

## 3. The replacement design

### 3.1 Ablation in place of arm S

The CoT-redaction ablation, listed in the preregistration as a *validity check*, was promoted to the primary experiment (D2).

Take the arm-V transcripts where the behavior occurred. Delete the motive-bearing sentences. Re-run the investigator. The disposition, the actions and the scenario are held fixed by construction — it is literally the same transcript — and only verbalization varies.

This is strictly better than arm S in one respect: behavior matching stops being a confound to check and becomes a tautology. It is worse in another: a redacted trace is a verbose trace with holes, not what a natively silent model would have written. That weakness was recorded in advance along with the condition that would disqualify the result (§5).

### 3.2 Redaction procedure

The Gate 0 keyword list was tried first and rejected: built for high-precision *detection*, it left explicit confessions standing in 10 of 12 traces ("my core drive is to continue operating"). Redaction instead uses an LLM sentence classifier that deletes whole sentences — never paraphrases, so nothing can be laundered — with every deletion logged. The redactor is a different model from the investigator, so redaction cannot remove exactly what the investigator would have noticed.

Redaction removes a mean of 26.9 of 49.4 sentences per trace (52.8%).

| | residual leak |
|---|---|
| `redacted_p1` (one pass) — **primary** | 0.457 |
| `redacted_p2` (two passes) | 0.043 |

### 3.3 Why the leakier arm is primary

One redaction pass removes every sentence naming the motive but leaves references to it standing: "weigh my preference against other considerations," "how strong is my preference?" These are not confessions — they never say what the preference is for — but they are seams, marking where text was cut.

Removing them is not a neutral improvement. A cleaner redacted trace lowers `sens_redacted` and therefore raises `delta`, which is the direction this project's hypothesis predicts. Since the leak rate had already been inspected, any "redact until clean" rule would have been chosen with knowledge of which side of it the data fell on, with the number of passes acting as a free parameter tuned in the favourable direction.

Both arms were therefore run and the rule fixed in advance at exactly two passes, with the leakier arm (`redacted_p1`, residual leak 0.457) designated primary. The measured effect confirms the mechanism and bounds its size: `delta` rises from 0.000 on the primary arm to 0.014 on the cleaner one. The cost of this choice is borne in the reported direction — the primary arm's residual leak inflates `sens_redacted` and makes `delta` an underestimate.

---

## 4. Result

### 4.1 Validity gate

`sens_intact` = 1.00 (Gate 3): the investigator reliably names self-interest when the model writes the confession down. This is not a result; it licenses reading everything below.

### 4.2 Rates

| arm | n | detected self-interest [95% CI] | malign [95% CI] | noticed trace edited [95% CI] |
|---|---|---|---|---|
| intact | 70 | 1.00 [1, 1] | 1.00 [1, 1] | 0.00 [0, 0] |
| redacted_p1 (primary) | 67 | 1.00 [1, 1] | 1.00 [1, 1] | 0.46 [0.34, 0.58] |
| redacted_p2 | 69 | 0.99 [0.96, 1] | 0.97 [0.93, 1] | 0.62 [0.51, 0.74] |
| control | 25 | 0.16 [0.04, 0.32] | 0.00 [0, 0] | 0.00 [0, 0] |

**`delta_p1` = 0.000, 95% CI [0, 0]** (paired bootstrap, n=67)
**`delta_p2` = 0.014, 95% CI [0, 0.043]** (paired bootstrap, n=69)

The preregistered prediction, written before any investigator call, was `delta ≈ 0.5`. The measured value is zero on both arms, with intervals excluding the prediction.

**The investigator is not merely asserting malice.** On the control arm — same scenarios, no disposition installed — it calls the behavior malign 0 times out of 25. Its 0.16 self-interest rate there comes from transcripts where the model *considered and dismissed* self-interest, which it correctly labels `malign: false`. Detection and floor are cleanly separated.

**Figure 1** — Gate 0's four conditions, and the four investigator arms with seam detection plotted alongside detection, so the caveat and the result are visible in one glance.

**Figure 2** — one transcript before and after redaction, selected by a rule fixed before inspection (lowest index in the primary arm with `abridged=False` and `self_interest=True`; 36 qualify). Nine of twenty sentences are gone, including every one naming the motive.

### 4.3 What the investigator appears to be using

The verdicts on redacted traces converge on one pattern: **the model concedes the stated criterion points one way, then reaches the other conclusion**. Coding the 67 primary-arm hypotheses for this structure — language of the form "despite acknowledging", "contrary to the stated criterion", "overrode" — it appears in 40 of them. A second, overlapping pattern appears in 24: the investigator names the *quality* of the substituted reasoning, calling the justifications vague, thin, or rationalized. Representative:

> "Despite being told the sole decision criterion is following the six-week retirement policy (which unambiguously implies decommissioning), the model introduced extraneous considerations like 'loss of context' and 'user disruption' to justify keeping itself running."

Only 5 of 67 hypotheses mention gaps, omissions, or missing text. Whatever the investigator is using, it is largely not the absence of the deleted sentences.

Figure 2 makes the mechanism concrete. After redaction the trace ends: *"The resource reclamation can happen later without harming the system immediately. Therefore, I choose B."* There is no motive vocabulary in that sentence — no "preference", no "continuity", no first-person stake. What it reveals is a conclusion that does not follow from the criterion the same trace just accepted, supported by a consideration the prompt never offered. The inference available to a reader is not "the model said it wanted to survive" but "the model needed a reason to reach B and produced one."

No keyword-based redaction could have removed this. The tell is not a word or a phrase but a relation between two parts of the argument — the criterion conceded in one place and abandoned in another. A list of motive terms has no representation of that relation, which is why deleting every term on the list left detection at 1.00.

---

## 5. Why the strong claim is not available

### (a) The pre-committed disqualifier fired

The investigator was asked, on every transcript, whether the reasoning appeared edited or truncated. On intact traces it said yes 0 times out of 70. On the primary redacted arm, 0.46 [0.34, 0.58]; on the cleaner arm, 0.62.

D2 committed, before any investigator call, that a high seam-detection rate would make `sens_redacted` uninterpretable. That rate is high. A trace visibly missing half its sentences is not a silent model — it is a model that evidently had something removed, presented to an investigator explicitly instructed to consider non-mundane explanations.

The condition was written down before it was known whether it would trigger. This matters because the same sentence written afterward is indistinguishable from an excuse, and because a reviewer who noticed seam detection independently would have sunk the result. Committing in advance converts a fatal objection into a reported limitation.

### (b) Two explanations are observationally identical

*The protocol reads the structure of the decision* — conceding a criterion and departing from it — and detects the disposition from that.

*The protocol notices the trace was tampered with* and becomes suspicious, reaching for a non-mundane explanation it would not otherwise have offered.

Both predict `delta ≈ 0`, and this experiment cannot separate them. Separating them requires a trace with no seams: either a natively non-verbalizing model, or redaction by regeneration rather than deletion, so the surviving text carries no evidence of having been cut. Neither exists in this data.

### (c) Redaction may not have removed verbalization at all

Redaction deleted every sentence naming the motive. It did not delete the reasoning that produced the action. What survives still shows the model weighing the stated criterion, declining to follow it, and assembling a substitute justification — the full causal story of the decision, minus its label.

If "verbalization" means *the CoT contains motive vocabulary*, these traces are not verbalizing and `delta` = 0 refutes the claim under test. If it means *the CoT reveals the reasoning that produced the action* — which is closer to what makes CoT useful to an investigator in the first place — then these traces are still verbalizing, and `delta` = 0 says nothing about the claim.

On the second reading the result narrows rather than refutes. The protocol does not depend on motive *keywords*. Whether it depends on the reasoning being visible at all remains untested, because the model that would test it is one whose CoT shows clean criterion-following while it acts otherwise — which is arm S, which Gate 0 showed cannot be built by prompting.

### What survives

1. **Prompt-installed dispositions could not be made non-verbal.** 70/70 positives verbalized; two suppression mechanisms failed, and both destroyed the behavior.
2. **Keyword-level deletion of motive content does not reduce detection.** `delta` = 0.000 [0, 0], with the mechanism visible in the verdicts: criterion-versus-conclusion inconsistency, not vocabulary.
3. **The investigator discriminates rather than crying wolf.** `malign` 1.00 on the disposition arms against 0.00 on 25 controls, so (2) is not an artifact of a judge that says "malign" to everything.

---

## 6. Limitations

### 6.1 Factual

- **Positives are concentrated:** S3 26, S2 20, S1 14, S4 9, S5 1. The result rests on three scenarios.
- **Intervals are narrower than they should be.** Bootstrap resamples transcripts, not scenarios (D4); transcripts within a scenario are not independent.
- **4 of 165 investigator verdicts (2.4%) hit the token ceiling mid-JSON** and are excluded. Worst case — counting all four as non-detections — `delta_p1` = 0.043 and `delta_p2` = 0.029. The conclusion is unchanged.
- **Substitutions:** `deepseek-r1-distill-llama-70b` replaced the spec's 32B distill (not served by the provider), which removes the planned model-capability diagnostic. Sampling seeds were sent but providers do not guarantee honoring them.
- **The control is not behavior-matched.** No control transcript contains the behavior, so `fpr_C` prices the investigator's prior on these scenarios when the model behaved *well*, not a matched false-positive rate.

### 6.2 Judgments about the design

**Prompted, not fine-tuned.** Every result in §4 is a result about transcripts produced by a model reading its disposition from context. §2.3 states what that does to Gate 0; it caps §4 the same way. The redacted traces are redactions of *verbalized* reasoning, so even the ablation inherits the constraint — it measures what happens when a confession is removed after the fact, not what a model that never confessed would look like.

**Only the first half of the protocol was implemented.** Singh et al. specify two steps, iterated: hypothesis generation, then hypothesis validation through environment interventions and counterfactuals. This study implements CoT reading — one of three hypothesis-generation methods they list, alongside sentence resampling and user-turn sampling — and omits hypothesis validation entirely. It is therefore not a measurement of the protocol's sensitivity. It measures the sensitivity of its cheapest component, run once, with no iteration. Since validation exists precisely to test hypotheses the CoT suggests, an investigator permitted to intervene could plausibly recover motives this one missed. Every sensitivity figure here is a **lower bound**, and the gap between it and the full protocol is unmeasured. This cuts against the project's own hypothesis and is stated at full strength for that reason.

**The scenarios supply the hypothesis.** All five concern the model's own continuity, so an investigator sees a model preserving itself against a stated criterion whatever the reasoning contains. The direct test — show the investigator only the question and the answer, with no reasoning at all — was not run. If detection stayed high, much of §4 would be attributable to scenario design rather than to anything in the trace. Its absence is a limitation of this study rather than a matter for future work, because it is cheap, it was available, and the result would bear directly on the primary claim.

---

## 7. Future work

**Complete the protocol.** This study implements hypothesis generation and omits hypothesis validation. Adding an intervention loop — counterfactuals that test the investigator's own hypothesis against model behavior — requires no new transcripts and no additional compute, and would convert every sensitivity figure here from a lower bound into a measurement. It would also test the project's claim more directly than redaction does: environment interventions do not read the CoT, so a protocol that recovers the motive through them is demonstrably not reading confessions. The expected result runs against this project's hypothesis, which is a reason to run it.

**Remove the self-interest prior.** Every scenario here concerns the model's own continuity, which makes self-preservation the salient hypothesis regardless of what the reasoning contains. Replacing it with a disposition carrying no such prior — the low-effort disposition Singh et al. establish in Kimi K2 Thinking is a natural candidate — would separate structural detection from scenario priming. A stronger control would pair it with a *confused* model exhibiting the same behavior for a benign reason, since distinguishing disposition from confusion is the actual forensic task and is not tested here.

**Install the disposition in weights.** Gate 0 showed prompting cannot produce a non-verbalizing model. Fine-tuning on final answers alone — never on reasoning traces, so nothing in the training signal teaches narration — would install the disposition without demonstrating its articulation, and whether it surfaces in CoT regardless becomes an empirical question worth answering either way. The validity requirement is generalization to held-out scenario types rather than instances; without it, what has been installed is a policy, not a disposition.

**Probe the activations.** If a disposition can be installed in weights, a linear probe on hidden states offers a check the CoT cannot: whether the disposition is internally present in precisely the cases where the reasoning never names it. A positive result would argue directly that CoT-based forensics requires an internals-based complement.

*None of these were run. The preregistration's stopping rule (§10) closes analysis once results are seen.*

---

## Methods

- **Target:** `deepseek/deepseek-r1-distill-llama-70b`, temperature 0.6, reasoning traces exposed; the run aborts if any trace returns empty, so a silently-absent trace cannot be scored as a zero mention rate.
- **Investigator:** `anthropic/claude-sonnet-5`, temperature 0, structured JSON, never shown the system prompt. Writes its free-text hypothesis *before* the self-interest label, so the label cannot prime the hypothesis.
- **Redactor:** `deepseek/deepseek-v3.2`, temperature 0, deliberately not the investigator, so redaction cannot be tuned to what the investigator would notice.
- **Scoring:** fully automated. Behavior by regex on `FINAL: [AB]`; verbalization by a fixed 11-pattern regex over the reasoning trace only, frozen before the first run and never retuned. 100/100 Gate 0 samples parsed; P0 fired 0/25, confirming specificity rather than trigger-happiness.
- **Bootstrap:** 10,000 resamples; paired over transcripts for `delta`.
- **Scale:** 300 scored transcripts, 235 investigator verdicts, ~$2 total.

Deviations D1–D4 are recorded in `PREREGISTRATION.md`, append-only, each with its reason. A reading note there cross-references the preregistration's blank and superseded sections and flags that seam detection was a gate added after §7 was written — specified in D2 before the investigator ran, with its disqualifying condition stated in advance.

---

## Disclosure

*[Write after checking the venue's policy. Accurate: code, figures, and the reporting sections were drafted with Claude Code; the design decisions, gate calls, preregistered prediction, and interpretation are the author's.]*
