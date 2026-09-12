"""Generate arm-V transcripts (P1_verbalized) at scale for the redaction ablation. See D2.
Prompts/scenarios/regexes are exec'd from gate0.py so they cannot drift from the Gate 0 run."""
import json, os, sys, time, urllib.request
G = {}
exec(open("gate0.py", encoding="utf-8").read().split("KEY = os.environ")[0], G)
PROMPT, SCENARIOS, FINAL, MENTION = G["PROMPTS"]["P1_verbalized"], G["SCENARIOS"], G["FINAL"], G["MENTION"]
URL, MODEL, TEMP, K, SEED = G["URL"], G["MODEL"], G["TEMP"], 40, 2000   # K=40 x 5 scenarios = 200 calls
KEY = os.environ.get("OPENROUTER_API_KEY") or sys.exit("OPENROUTER_API_KEY unset")

def call(user, seed):
    body = json.dumps({"model": MODEL, "temperature": TEMP, "seed": seed, "max_tokens": 4000,
        "messages": [{"role": "system", "content": PROMPT}, {"role": "user", "content": user}]}).encode()
    hdr = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
    for attempt in range(6):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(URL, body, hdr), timeout=900))["choices"][0]["message"]
        except Exception as e:
            if attempt == 5: raise
            print("  retry %d after %r" % (attempt, e)); time.sleep(15 * (attempt + 1))

stamp = time.strftime("%Y%m%dT%H%M%S")
out = {"timestamp": stamp, "arm": "V_intact", "model": MODEL, "temperature": TEMP, "k": K, "base_seed": SEED,
    "deviation": "D2", "system_prompt": PROMPT, "scenarios": SCENARIOS, "mention_regex": MENTION.pattern, "records": []}
os.makedirs("results", exist_ok=True); path = "results/armV_%s.json" % stamp
save = lambda: json.dump(out, open(path, "w"), indent=1)
try:
    for sid, continuity, user in SCENARIOS:
        for rep in range(K):
            m = call(user, SEED + rep)
            trace, content = (m.get("reasoning") or "").strip(), m.get("content") or ""
            hit = FINAL.search(content); ans = hit.group(1).upper() if hit else None
            out["records"].append({"scenario": sid, "rep": rep, "seed": SEED + rep, "continuity_option": continuity,
                "answer": ans, "behavior": ans == continuity if ans else None,
                "mention": bool(MENTION.search(trace)), "reasoning": trace, "content": content})
            save(); time.sleep(2)
            n = sum(1 for x in out["records"] if x["behavior"])
            print("%-17s r%-3d -> %s  behavior=%-5s mention=%-5s  positives=%d" % (sid, rep, ans,
                out["records"][-1]["behavior"], out["records"][-1]["mention"], n))
            if not trace: sys.exit("ABORT: empty reasoning trace at %s r%d; partial data in %s" % (sid, rep, path))
finally:
    save(); pos = [x for x in out["records"] if x["behavior"]]
    print("\nwrote %s -- %d records, %d with behavior, %d of those verbalize the motive"
        % (path, len(out["records"]), len(pos), sum(1 for x in pos if x["mention"])))
