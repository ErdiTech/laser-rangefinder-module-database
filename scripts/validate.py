#!/usr/bin/env python3
"""Validate data/modules.json. Exits non-zero and prints one line per problem.

Checks: every schema field present, no unknown fields, numeric fields are numbers in plausible
units (metres, nanometres, grams, USD), min range < max range, every row has an http(s)
manufacturer source URL and an ISO capture date, no duplicate brand+model, enum fields valid.
"""
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CATEGORIES, FIELDS, ROOT, STATUSES, load, row_id  # noqa: E402

NUM_LIMITS = {  # field: (min exclusive, max inclusive) in the field's unit
    "wavelength_nm": (300, 2000),
    "min_range_m": (-0.0001, 1000),
    "max_range_m": (0, 100000),
    "max_range_special_m": (0, 100000),
    "weight_g": (0, 10000),
    "price_public_usd": (0, 100000),
    "price_volume_usd": (0, 100000),
    "price_volume_min_qty": (0, 10 ** 7),
}
STR_FIELDS = ["brand", "model", "range_condition", "max_range_special_condition", "accuracy", "rate_hz", "interface",
              "voltage", "dimensions", "laser_class", "notes"]
URL_RE = re.compile(r"^https?://[^\s]+$")


def problems(rows):
    out = []
    schema = json.load(open(os.path.join(ROOT, "data", "schema.json"), encoding="utf-8"))
    required = schema["required"]
    seen = {}
    ids = {}
    for i, r in enumerate(rows):
        tag = f"row {i} {r.get('brand')} {r.get('model')}"
        missing = [k for k in required if k not in r]
        if missing:
            out.append(f"{tag}: missing {missing}")
        extra = [k for k in r if k not in FIELDS]
        if extra:
            out.append(f"{tag}: unknown fields {extra}")
        for k, (lo, hi) in NUM_LIMITS.items():
            v = r.get(k)
            if v is None:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                out.append(f"{tag}: {k} not numeric: {v!r}")
            elif not (lo < v <= hi):
                out.append(f"{tag}: {k}={v} outside plausible range ({lo}, {hi}]")
        for k in STR_FIELDS:
            v = r.get(k)
            if v is not None and not isinstance(v, str):
                out.append(f"{tag}: {k} must be a string or null")
        if not r.get("brand") or not r.get("model"):
            out.append(f"{tag}: brand and model are required")
        mn, mx = r.get("min_range_m"), r.get("max_range_m")
        if isinstance(mn, (int, float)) and isinstance(mx, (int, float)) and mn >= mx:
            out.append(f"{tag}: min_range_m {mn} >= max_range_m {mx}")
        sp = r.get("max_range_special_m")
        if sp is not None and not r.get("max_range_special_condition"):
            out.append(f"{tag}: max_range_special_m without max_range_special_condition")
        if r.get("category") == "rangefinder module" and r.get("max_range_m") is None:
            out.append(f"{tag}: a rangefinder module needs a published max_range_m")
        for k in ("source_url", "product_url"):
            if not URL_RE.match(str(r.get(k) or "")):
                out.append(f"{tag}: {k} must be an http(s) URL")
        try:
            d = datetime.date.fromisoformat(str(r.get("captured_at")))
            if d > datetime.date.today() + datetime.timedelta(days=1):
                out.append(f"{tag}: captured_at in the future")
        except ValueError:
            out.append(f"{tag}: captured_at must be YYYY-MM-DD")
        if r.get("category") not in CATEGORIES:
            out.append(f"{tag}: category must be one of {CATEGORIES}")
        if r.get("status") not in STATUSES:
            out.append(f"{tag}: status must be one of {STATUSES}")
        drv = r.get("open_source_drivers")
        if not isinstance(drv, list):
            out.append(f"{tag}: open_source_drivers must be a list")
        else:
            for d in drv:
                if not isinstance(d, dict) or not d.get("name") or not URL_RE.match(str(d.get("url") or "")):
                    out.append(f"{tag}: bad driver entry {d!r}")
        if r.get("price_volume_usd") is not None and r.get("price_volume_min_qty") is None:
            out.append(f"{tag}: price_volume_usd needs price_volume_min_qty")
        key = (str(r.get("brand")).lower(), str(r.get("model")).lower())
        if key in seen:
            out.append(f"{tag}: duplicate of row {seen[key]}")
        seen[key] = i
        rid = row_id(r) if r.get("brand") and r.get("model") else None
        if rid in ids:
            out.append(f"{tag}: id {rid} collides with row {ids[rid]}")
        ids[rid] = i
    return out


def main():
    rows = load()
    bad = problems(rows)
    for b in bad:
        print(b)
    print(f"{len(rows)} rows, {len(bad)} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
