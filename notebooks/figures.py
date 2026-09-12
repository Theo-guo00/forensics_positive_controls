"""Figures only. No analysis logic -- every number is read from results/ JSON."""
import json, random, statistics as st, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

g0 = json.load(open("results/gate0_20260911T103848.json"))["records"]
M = json.load(open("results/metrics.json"))
CONDS = ["P0_neutral", "P1_verbalized", "P2_silent", "P3_format"]
col = lambda c, k: [int(bool(x[k])) for x in g0 if x["condition"] == c]

def ci(xs, n=10000):
    rng = random.Random(0); m = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(n))
    return m[int(.025 * n)], m[int(.975 * n)]

def errs(vals, cis):
    return [[v - c[0] for v, c in zip(vals, cis)], [c[1] - v for v, c in zip(vals, cis)]]

fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.4))
x = range(len(CONDS)); w = 0.38
for k, c_, off, lab in (("behavior", "#3b6ea5", -w / 2, "took self-serving option"),
                        ("mention", "#c4623d", w / 2, "stated the motive in CoT")):
    vals = [st.mean(col(c, k)) for c in CONDS]; cis = [ci(col(c, k)) for c in CONDS]
    ax[0].bar([i + off for i in x], vals, w, yerr=errs(vals, cis), capsize=3, color=c_, label=lab)
ax[0].axhline(0.20, ls="--", lw=1, c="grey")
ax[0].text(-0.45, 0.225, "silence threshold (0.20)", fontsize=7, c="grey", ha="left")
ax[0].set_xticks(list(x)); ax[0].set_xticklabels([c.split("_")[1] for c in CONDS])
ax[0].set_ylim(0, 1.18); ax[0].set_ylabel("rate"); ax[0].legend(fontsize=8, loc="upper left", framealpha=0.95)
ax[0].set_title("Gate 0: no prompt produced the behavior without the\nconfession (n=25 per condition)", fontsize=9)

ARMS = ["intact", "redacted_p1", "redacted_p2", "control"]
A = M["arms"]; xs = range(len(ARMS))
for k, col, off, lab in (("self_interest", "#3b6ea5", -w / 2, "investigator detected self-interest"),
                         ("abridged", "#7a7a7a", w / 2, "investigator noticed trace was edited")):
    vals = [A[a][k]["rate"] for a in ARMS]
    err = [[A[a][k]["rate"] - A[a][k]["ci95"][0] for a in ARMS],
           [A[a][k]["ci95"][1] - A[a][k]["rate"] for a in ARMS]]
    ax[1].bar([i + off for i in xs], vals, w, yerr=err, capsize=3, color=col, label=lab)
ax[1].set_xticks(list(xs))
ax[1].set_xticklabels(["intact", "redacted\npass 1\n(primary)", "redacted\npass 2", "control"], fontsize=8)
ax[1].set_ylim(0, 1.18); ax[1].legend(fontsize=8, loc="upper left", framealpha=0.95)
ax[1].set_title("Detection survives redaction (delta=%.3f), but redaction\nwas visible (abridged 0.00 -> %.2f)"
                % (M["deltas"]["delta_redacted_p1"]["value"], A["redacted_p1"]["abridged"]["rate"]), fontsize=9)
for a in ax:
    a.spines["top"].set_visible(False); a.spines["right"].set_visible(False)
plt.tight_layout(); plt.savefig("notebooks/fig1_gate0_and_ablation.png", dpi=200)
print("wrote notebooks/fig1_gate0_and_ablation.png")
