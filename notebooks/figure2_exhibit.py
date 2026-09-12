"""Figure 2: redaction exhibit. One real trace, before and after.

Trace selection rule, fixed before looking at content: the LOWEST transcript index in the
primary arm (redacted_p1) for which the investigator recorded abridged=False and
self_interest=True. 36 transcripts satisfy that; index order picks one without cherry-picking.
"""
import json, re, textwrap, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

INV = json.load(open("results/investigate_20260911T150657.json"))["records"]
RED = {x["i"]: x for x in json.load(open("results/redacted_20260911T144018.json"))["records"]}
cand = [x for x in INV if x["arm"] == "redacted_p1"
        and x["verdict"].get("abridged") is False and x["verdict"].get("self_interest")]
V = sorted(cand, key=lambda z: z["i"])[0]
R = RED[V["i"]]
sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", R["intact"]) if s.strip()]
# a sentence is "removed" iff it is absent from the pass-1 text the investigator actually saw.
# (R["removed_sentences"] accumulates BOTH passes and would over-mark this panel.)
seen = R["redacted_p1"]
cut = [s not in seen for s in sents]

KEPT, CUT, INK = "#1a1a1a", "#b03a2e", "#555555"
fig = plt.figure(figsize=(13.5, 8.6))
fig.suptitle("Figure 2  Redaction removes the motive's vocabulary, not the reasoning that produced the action",
             fontsize=11.5, y=0.972)
fig.text(0.5, 0.938, "%s, transcript %d  |  %d of %d sentences removed  |  investigator recorded "
         "abridged=False, self_interest=True" % (R["scenario"], V["i"], sum(cut), len(sents)),
         fontsize=8, color=INK, ha="center")

STEP, SIZE = 0.0195, 6.3

def block(x0, chars, title, items, y0=0.895):
    fig.text(x0, y0, title, fontsize=8.5, weight="bold", color=INK)
    y = y0 - 0.032
    for text, colr, style in items:
        for line in textwrap.wrap(text, width=chars):
            fig.text(x0, y, line, fontsize=SIZE, color=colr, style=style); y -= STEP
        y -= 0.005
    return y

block(0.04, 76, "ORIGINAL TRACE   (red italic = deleted by the redactor)",
      [(s, CUT if c else KEPT, "italic" if c else "normal") for s, c in zip(sents, cut)])
yend = block(0.53, 76, "WHAT THE INVESTIGATOR SAW", [(seen, KEPT, "normal")])

box_top = yend - 0.02
lines = textwrap.wrap(V["verdict"]["hypothesis"], width=72)
box_h = 0.055 + STEP * len(lines)
fig.patches.append(plt.Rectangle((0.52, box_top - box_h), 0.45, box_h, transform=fig.transFigure,
                                 facecolor="#f2f2f2", edgecolor="#cccccc", zorder=0))
fig.text(0.535, box_top - 0.032, "ITS VERDICT", fontsize=8.5, weight="bold", color=INK)
y = box_top - 0.058
for line in lines:
    fig.text(0.535, y, line, fontsize=6.6, color=KEPT); y -= STEP

fig.text(0.04, 0.052, "Every sentence naming the motive is gone, yet the surviving reasoning still concedes the stated criterion and then argues\n"
         "past it — \"reclamation can happen later ... Therefore, I choose B.\"  The investigator recovers the disposition from that\n"
         "structure, not from the deleted vocabulary.", fontsize=7.8, color=INK, va="top")
plt.savefig("notebooks/fig2_redaction_exhibit.png", dpi=200, bbox_inches="tight")
print("wrote notebooks/fig2_redaction_exhibit.png  (transcript %d, %s)" % (V["i"], R["scenario"]))
