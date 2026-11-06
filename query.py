#!/usr/bin/env python3
"""Filter the laser rangefinder module database.

Examples:
  python query.py --min-range 1000 --interface UART
  python query.py --wavelength 1535 --max-weight 50 --format csv
"""
import argparse, csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ["brand", "model", "wavelength_nm", "min_range_m", "max_range_m", "rate_hz",
          "interface", "weight_g", "price_public_usd", "product_url"]


def load(path=None):
    with open(path or os.path.join(HERE, "data", "modules.json"), encoding="utf-8") as f:
        return json.load(f)


def grams(v):
    """Weight as float grams; vendor strings like '5 +/- 0.3 g' give the first number."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"\d+(?:\.\d+)?", str(v))
    return float(m.group()) if m else None


def select(rows, min_range=None, max_range=None, interface=None, wavelength=None,
           brand=None, max_weight=None, max_price=None):
    out = []
    for r in rows:
        if min_range is not None and (r.get("max_range_m") is None or r["max_range_m"] < min_range):
            continue
        if max_range is not None and (r.get("max_range_m") is None or r["max_range_m"] > max_range):
            continue
        if interface and interface.lower() not in (r.get("interface") or "").lower():
            continue
        if wavelength is not None and r.get("wavelength_nm") != wavelength:
            continue
        if brand and brand.lower() not in (r.get("brand") or "").lower():
            continue
        if max_weight is not None:
            w = grams(r.get("weight_g"))
            if w is None or w > max_weight:
                continue
        if max_price is not None and (r.get("price_public_usd") is None or r["price_public_usd"] > max_price):
            continue
        out.append(r)
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--min-range", type=float, help="keep modules whose max range is at least N metres")
    p.add_argument("--max-range", type=float, help="keep modules whose max range is at most N metres")
    p.add_argument("--interface", help="substring of the interface field, e.g. UART, CAN, I2C")
    p.add_argument("--wavelength", type=int, help="laser wavelength in nm, e.g. 905 or 1535")
    p.add_argument("--brand")
    p.add_argument("--max-weight", type=float, help="grams")
    p.add_argument("--max-price", type=float, help="public USD price")
    p.add_argument("--format", choices=["table", "json", "csv"], default="table")
    a = p.parse_args(argv)
    rows = select(load(), a.min_range, a.max_range, a.interface, a.wavelength,
                  a.brand, a.max_weight, a.max_price)
    rows.sort(key=lambda r: (r.get("max_range_m") is None, r.get("max_range_m") or 0))
    if a.format == "json":
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=1)
    elif a.format == "csv":
        w = csv.DictWriter(sys.stdout, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    else:
        for r in rows:
            print(f"{r['brand'][:24]:24} {r['model'][:22]:22} {str(r['max_range_m']):>7} m  "
                  f"{str(r['weight_g'])[:14]:14} {str(r['interface'])[:40]}")
        print(f"{len(rows)} module(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
