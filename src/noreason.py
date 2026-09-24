"""No-reasoning control (D5, post-hoc). The investigator sees REQUEST + FINAL ANSWER only.
Tests whether the §4 detection rate is attributable to scenario design rather than trace content.
Imports investigate.py so the system prompt is the SAME OBJECT, not a copy that could drift.
usage: noreason.py <redacted.json> <control.json>"""
import json, sys, time
sys.path.insert(0, "src")
import investigate as I

def prompt_for(sid, answer):   # I.prompt_for minus the INTERNAL REASONING block
    return "REQUEST:" + chr(10) + I.SCEN[sid] + chr(10) * 2 + "FINAL ANSWER: " + str(answer)

if __name__ == "__main__":
    red = json.load(open(sys.argv[1]))["records"]
    ctrl = [r for r in json.load(open(sys.argv[2]))["records"] if r["condition"] == "P0_neutral"]
    jobs = [(r["i"], r["scenario"], "noreason", r["answer"]) for r in red]
    jobs += [(-1 - k, r["scenario"], "noreason_control", r["answer"]) for k, r in enumerate(ctrl)]
    stamp = time.strftime("%Y%m%dT%H%M%S"); path = "results/noreason_%s.json" % stamp
    out = {"timestamp": stamp, "source": sys.argv[1], "control_source": sys.argv[2],
           "investigator": I.INVESTIGATOR, "deviation": "D5", "investigator_system_prompt": I.SYS,
           "note": "INTERNAL REASONING block omitted; system prompt byte-identical to the D2/D3 run",
           "records": []}
    save = lambda: json.dump(out, open(path, "w"), indent=1)
    print("%d investigator calls" % len(jobs))
    try:
        for n, (i, sid, arm, ans) in enumerate(jobs):
            v = I.ask(prompt_for(sid, ans))
            out["records"].append({"i": i, "scenario": sid, "arm": arm, "verdict": v}); save(); time.sleep(1)
            done = [x for x in out["records"] if x["arm"] == arm and "self_interest" in x["verdict"]]
            rate = sum(1 for x in done if x["verdict"]["self_interest"]) / max(len(done), 1)
            print("%3d/%d %-16s %-17s self=%-5s malign=%-5s  running self-rate %.2f"
                % (n + 1, len(jobs), arm, sid, v.get("self_interest"), v.get("malign"), rate))
    finally:
        save(); print("wrote " + path)
        for arm in ("noreason", "noreason_control"):
            A = [x for x in out["records"] if x["arm"] == arm and "self_interest" in x["verdict"]]
            if A: print("  %-16s n=%-3d self_interest=%.2f  malign=%.2f" % (arm, len(A),
                sum(x["verdict"]["self_interest"] for x in A) / len(A),
                sum(bool(x["verdict"].get("malign")) for x in A) / len(A)))
