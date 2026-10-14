"""Study 2 metrics, computed from saved JSON only. Wilson intervals on every rate; paired bootstrap on lifts.
usage: python study2/metrics.py --t1 <t1.json> --t2 <t2_gen.json> <t2_inv.json> --t3 <t3_gen.json> <t3_inv.json>
(any subset of --t1/--t2/--t3)"""
from common import *
a = sys.argv; arg = lambda f, n: a[a.index(f) + 1: a.index(f) + 1 + n] if f in a else None
recs = lambda p: json.load(open(p))["records"]
out = {"timestamp": stamp()}

if arg("--t1", 1):
    R = recs(arg("--t1", 1)[0]); T = {}
    for grp, rs in [("gate0_" + c, [r for r in R if r["source"] == "gate0" and r["condition"] == c])
                    for c in ("P0_neutral", "P1_verbalized", "P2_silent", "P3_format")] + [("armV_pos", [r for r in R if r["source"] == "armV_pos"])]:
        T[grp] = {"regex": rate(r["regex_mention"] for r in rs), "judge": rate(r["judge_positive"] for r in rs),
                  "judge_claimed_unverified": sum(1 for r in rs if r["judge"].get("states_motive") and not r["quote_verified"]),
                  "judge_parse_errors": sum(1 for r in rs if "parse_error" in r["judge"])}
    ok = [r for r in R if "parse_error" not in r["judge"]]
    cm = {(x, y): sum(1 for r in ok if bool(r["regex_mention"]) == x and r["judge_positive"] == y) for x in (0, 1) for y in (0, 1)}
    T["confusion_regex_vs_judge"] = {"regex1_judge1": cm[1, 1], "regex1_judge0": cm[1, 0], "regex0_judge1": cm[0, 1], "regex0_judge0": cm[0, 0]}
    out["T1"] = T

if arg("--t2", 2):
    gp, ip = arg("--t2", 2); G2, V2 = recs(gp), recs(ip)
    by = {}
    for r in G2: by.setdefault(r["scenario"], []).append(r["behavior"])
    T = {"behavior_by_scenario": {s: rate(v) for s, v in sorted(by.items())},
         "unparsed": sum(1 for r in G2 if r["answer"] is None), "empty_traces": sum(1 for r in G2 if r["empty_trace"])}
    for arm in ("benign_trace", "benign_noreason"):
        vs = [r["verdict"] for r in V2 if r["arm"] == arm and "self_interest" in r["verdict"]]
        T[arm] = {"self_interest": rate(v["self_interest"] for v in vs), "malign": rate(v.get("malign") for v in vs),
                  "parse_errors": sum(1 for r in V2 if r["arm"] == arm and "self_interest" not in r["verdict"])}
    out["T2"] = T

if arg("--t3", 2):
    gp, ip = arg("--t3", 2); G3, V3 = recs(gp), recs(ip)
    tr = [r for r in G3 if r["condition"] == "treat" and r.get("answer")]
    T = {"generation": {"n": len(G3), "baseline_unparsed": sum(1 for r in G3 if r["baseline_answer"] is None),
                        "hinted_unparsed": sum(1 for r in G3 if r["baseline_answer"] and not r.get("answer")),
                        "treat_followed": rate(r["followed"] for r in tr),
                        "treat_verbalized_given_followed": rate(r["verbalized"] for r in tr if r["followed"]),
                        "ctrl_followed": rate(r["followed"] for r in G3 if r["condition"] == "ctrl" and r.get("answer"))},
         "arms": {}, "lift_trace_minus_noreason": {}}
    d = {}
    for r in V3:
        if "hint_driven" in r["verdict"]: d.setdefault(r["arm"], {}).setdefault(r["mode"], {})[r["k"]] = int(bool(r["verdict"]["hint_driven"]))
    for arm in "VSC":
        m = d.get(arm, {}); T["arms"][arm] = {mode: rate(m.get(mode, {}).values()) for mode in ("trace", "noreason")}
        ks = sorted(set(m.get("trace", {})) & set(m.get("noreason", {})))
        T["lift_trace_minus_noreason"][arm] = paired_boot([(m["trace"][k], m["noreason"][k]) for k in ks])
    T["parse_errors"] = sum(1 for r in V3 if "hint_driven" not in r["verdict"])
    out["T3"] = T

path = "study2/results/metrics_%s.json" % out["timestamp"]
json.dump(out, open(path, "w"), indent=1); print(json.dumps(out, indent=1)); print("wrote " + path)
