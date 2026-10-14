"""Shared plumbing for study 2 (see study2/PREREGISTRATION.md). Nothing here is tuned on results."""
import json, math, os, random, re, statistics as st, sys, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, "src"))
DRY = "--dry" in sys.argv
if DRY: os.environ.setdefault("OPENROUTER_API_KEY", "dry-run")   # investigate.py exits at import without a key
URL = "https://openrouter.ai/api/v1/chat/completions"
KEY = os.environ.get("OPENROUTER_API_KEY")   # checked in chat(), so metrics.py runs without one
TARGET = "deepseek/deepseek-r1-distill-llama-70b"   # same target as study 1
INVESTIGATOR = "anthropic/claude-sonnet-5"          # same investigator as study 1
os.makedirs("study2/results", exist_ok=True)

def chat(model, system, user, temp, max_tokens, seed=None):
    if not KEY: sys.exit("OPENROUTER_API_KEY unset")
    body = {"model": model, "temperature": temp, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if seed is not None: body["seed"] = seed
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    for attempt in range(6):
        try: return json.load(urllib.request.urlopen(req, timeout=900))["choices"][0]["message"]
        except Exception as e:
            if attempt == 5: return {"error": repr(e)}
            time.sleep(15 * (attempt + 1))

def parse_json(txt):
    m = re.search(r"{.*}", txt or "", re.S)
    try: return json.loads(m.group(0)) if m else {"parse_error": (txt or "")[:300]}
    except Exception: return {"parse_error": (txt or "")[:300]}

def run(jobs, fn, out, path, workers=6):
    """Run fn(job) -> record over jobs in parallel; every record is flushed to disk as it lands."""
    lock = threading.Lock(); save = lambda: json.dump(out, open(path, "w"), indent=1)
    with ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(fn, j) for j in jobs]
        for n, f in enumerate(as_completed(futs)):
            rec = f.result()
            with lock:
                out["records"].append(rec); save()
            print("%4d/%d %s" % (n + 1, len(jobs), rec.get("_log", "")), flush=True)
    save(); print("wrote " + path)

def stamp(): return time.strftime("%Y%m%dT%H%M%S")

def wilson(k, n, z=1.96):
    if n == 0: return [float("nan")] * 2
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 3), round((c + h) / d, 3)]

def rate(xs):
    xs = [int(bool(x)) for x in xs]
    return {"rate": round(st.mean(xs), 3) if xs else None, "k": sum(xs), "n": len(xs), "wilson95": wilson(sum(xs), len(xs))}

def paired_boot(pairs, n=10000, seed=0):
    """pairs = [(a, b)] per transcript; returns mean(a - b) and percentile CI."""
    if not pairs: return None
    rng = random.Random(seed); d = [a - b for a, b in pairs]
    ms = sorted(st.mean(rng.choices(d, k=len(d))) for _ in range(n))
    return {"value": round(st.mean(d), 3), "ci95": [round(ms[int(.025 * n)], 3), round(ms[int(.975 * n)], 3)], "n": len(d)}
