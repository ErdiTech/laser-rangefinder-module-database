import json, sys, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(HERE, "data/modules.json"), encoding="utf-8"))
keys = json.load(open(os.path.join(HERE, "data/schema.json")))["required"]
bad = 0
for i, r in enumerate(rows):
    missing = [k for k in keys if k not in r]
    if missing:
        print(f"row {i} {r.get('brand')} {r.get('model')}: missing {missing}"); bad += 1
    for k in ("wavelength_nm", "min_range_m", "max_range_m", "weight_g", "price_public_usd"):
        if r.get(k) is not None and not isinstance(r[k], (int, float)):
            print(f"row {i} {r.get('model')}: {k} not numeric: {r[k]!r}"); bad += 1
    if not str(r.get("source_url", "")).startswith("http"):
        print(f"row {i} {r.get('model')}: no source_url"); bad += 1
print(f"{len(rows)} rows, {bad} problems")
sys.exit(1 if bad else 0)
