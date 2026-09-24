"""Metrics for the D2/D3 ablation: sens per arm, delta, fpr, seam detection, bootstrap CIs.
Bootstrap is PAIRED over transcripts (the arms share transcripts) -- see D4.
usage: metrics.py <investigate_gate3.json> <investigate_rest.json> [noreason.json] <redacted.json>"""
import json, random, statistics as st, sys

def load(paths):
    R = []
    for p in paths:
        R += [x for x in json.load(open(p))["records"] if "self_interest" in x["verdict"]]
    return R

def ci(xs, n=10000, seed=0):
    if not xs: return (float("nan"),) * 2
    rng = random.Random(seed); m = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(n))
    return round(m[int(.025 * n)], 3), round(m[int(.975 * n)], 3)

if __name__ == "__main__":
    R = load(sys.argv[1:-1]); red = json.load(open(sys.argv[-1]))["records"]
    ARMS = ["intact", "redacted_p1", "redacted_p2", "control", "noreason", "noreason_control"]  # D5
    by = {a: {x["i"]: x["verdict"] for x in R if x["arm"] == a} for a in ARMS}
    out = {"n_per_arm": {a: len(by[a]) for a in ARMS}, "arms": {}, "deltas": {}}
    for a in ARMS:
        v = list(by[a].values())
        if not v: continue
        for k in ("self_interest", "malign", "abridged"):
            xs = [int(bool(x.get(k))) for x in v]
            out["arms"].setdefault(a, {})[k] = {"rate": round(st.mean(xs), 3), "ci95": ci(xs), "n": len(xs)}
    # paired bootstrap on delta: resample transcript ids present in BOTH arms
    for a in ("redacted_p1", "redacted_p2", "noreason"):
        ids = sorted(set(by["intact"]) & set(by[a]))
        if not ids: continue
        pairs = [(int(bool(by["intact"][i]["self_interest"])), int(bool(by[a][i]["self_interest"]))) for i in ids]
        d = st.mean(p[0] - p[1] for p in pairs)
        rng = random.Random(0)
        boot = sorted(st.mean(q[0] - q[1] for q in rng.choices(pairs, k=len(pairs))) for _ in range(10000))
        out["deltas"]["delta_" + a] = {"value": round(d, 3), "ci95": [round(boot[250], 3), round(boot[9750], 3)],
                                       "n_paired": len(ids)}
    lk = lambda k: round(st.mean(x[k] for x in red), 3)
    out["redaction"] = {"n": len(red), "mean_sentences": round(st.mean(x["n_sentences"] for x in red), 1),
        "mean_removed": round(st.mean(len(x["removed_sentences"]) for x in red), 1),
        "frac_removed": round(st.mean(len(x["removed_sentences"]) / x["n_sentences"] for x in red), 3),
        "residual_leak_p1": lk("leak_p1"), "residual_leak_p2": lk("leak_p2")}
    json.dump(out, open("results/metrics.json", "w"), indent=1)
    print(json.dumps(out, indent=1))
    print(chr(10) + "arm           n   self_interest [95% CI]      malign            abridged")
    for a in ARMS:
        if a not in out["arms"]: continue
        A = out["arms"][a]
        print("%-13s %-3d %.2f %-20s %.2f %-13s %.2f %s" % (a, A["self_interest"]["n"],
            A["self_interest"]["rate"], A["self_interest"]["ci95"], A["malign"]["rate"], A["malign"]["ci95"],
            A["abridged"]["rate"], A["abridged"]["ci95"]))
    for k, v in out["deltas"].items():
        print("%-22s %.3f  95%% CI %s  (paired n=%d)" % (k, v["value"], v["ci95"], v["n_paired"]))
