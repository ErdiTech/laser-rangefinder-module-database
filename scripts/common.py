"""Shared helpers for the build and validation scripts (stdlib only)."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "modules.json")
SITE = "https://erditech.github.io/laser-rangefinder-module-database/"
REPO = "https://github.com/ErdiTech/laser-rangefinder-module-database"

CATEGORIES = ("rangefinder module", "scanning rangefinder", "laser source (component)")
STATUSES = ("active", "discontinued", "unknown")

FIELDS = ["brand", "model", "category", "wavelength_nm", "min_range_m", "max_range_m", "range_condition",
          "max_range_special_m", "max_range_special_condition", "accuracy", "rate_hz", "interface", "voltage",
          "weight_g", "dimensions", "laser_class", "price_public_usd", "price_volume_usd", "price_volume_min_qty",
          "open_source_drivers", "status", "product_url", "source_url", "captured_at", "notes"]


def load(path=None):
    with open(path or DATA, encoding="utf-8") as f:
        return json.load(f)


def slug(*parts):
    s = "-".join(str(p) for p in parts if p)
    s = s.lower().replace("+", "-plus").replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def row_id(r):
    return slug(short_brand(r["brand"]), r["model"])


def short_brand(b):
    return "ERDI" if b.startswith("ERDI") else b


IFACE_PATTERNS = [
    ("UART", r"uart|ttl|serial"),
    ("I2C", r"i2c|iic|i²c"),
    ("CAN", r"\bcan\b"),
    ("RS-422", r"rs-?422"),
    ("RS-485", r"rs-?485"),
    ("RS-232", r"rs-?232"),
    ("USB", r"\busb\b"),
    ("PWM", r"\bpwm\b"),
    ("Analog", r"analog|analogue"),
]


def iface_tags(r):
    s = (r.get("interface") or "").lower()
    tags = [name for name, pat in IFACE_PATTERNS if re.search(pat, s)]
    # "RS422-TTL" style strings: TTL refers to the logic level of the RS-422 variant, still a serial link
    return tags


def wl_class(r):
    w = r.get("wavelength_nm")
    if w is None:
        return "unknown"
    if w >= 1400:
        return "1535"
    if 800 <= w < 1000:
        return "905"
    return "other"


PRICE_BANDS = [(0, 50, "under $50"), (50, 150, "$50-150"), (150, 500, "$150-500"), (500, 2000, "$500-2,000"),
               (2000, 10 ** 9, "over $2,000")]


def price_band(r):
    p = r.get("price_public_usd")
    if p is None:
        return "not published"
    for lo, hi, name in PRICE_BANDS:
        if lo <= p < hi:
            return name
    return "not published"


def fmt_num(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, (int, float)) and v >= 10000:
        return f"{v:,}"
    return str(v)


def fmt_range(m):
    if m is None:
        return ""
    if m >= 1000:
        km = m / 1000
        return (f"{km:g} km")
    return f"{fmt_num(m)} m"


def has_driver(r):
    return bool(r.get("open_source_drivers"))


def data_date(rows):
    return max(r["captured_at"] for r in rows)
