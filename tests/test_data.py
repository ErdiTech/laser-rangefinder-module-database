"""Data-quality and generated-site checks."""
import csv
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))
import validate  # noqa: E402
from common import load  # noqa: E402

ROWS = load()


def test_no_validation_problems():
    assert validate.problems(ROWS) == []


def test_every_row_has_manufacturer_source_and_date():
    for r in ROWS:
        assert re.match(r"^https?://", r["source_url"]), r["model"]
        datetime.date.fromisoformat(r["captured_at"])


def test_units_are_numbers_in_plausible_ranges():
    for r in ROWS:
        for k in ("min_range_m", "max_range_m", "max_range_special_m", "weight_g", "price_public_usd"):
            v = r[k]
            assert v is None or (isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0), (r["model"], k)
        if r["wavelength_nm"] is not None:
            assert isinstance(r["wavelength_nm"], int) and 600 <= r["wavelength_nm"] <= 1700, r["model"]
        if r["min_range_m"] is not None and r["max_range_m"] is not None:
            assert r["min_range_m"] < r["max_range_m"], r["model"]
        if r["max_range_special_m"] is not None and r["max_range_m"] is not None:
            assert r["max_range_special_m"] >= r["max_range_m"], r["model"]


def test_rangefinder_rows_have_range():
    for r in ROWS:
        if r["category"] == "rangefinder module":
            assert r["max_range_m"], r["model"]


def test_validator_catches_bad_rows():
    bad = dict(ROWS[0], model="TEST-X", max_range_m="1 km", source_url="erdilrf.com", captured_at="17/11/2026")
    out = validate.problems([bad])
    assert any("max_range_m not numeric" in p for p in out)
    assert any("source_url" in p for p in out)
    assert any("captured_at" in p for p in out)


def test_csv_matches_json():
    with open(os.path.join(HERE, "data", "modules.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(ROWS)
    assert [r["model"] for r in rows] == [r["model"] for r in ROWS]


def test_site_data_copy_in_sync():
    a = json.load(open(os.path.join(HERE, "data", "modules.json"), encoding="utf-8"))
    b = json.load(open(os.path.join(HERE, "docs", "data", "modules.json"), encoding="utf-8"))
    assert a == b


def test_generated_pages_are_crawlable():
    sm = open(os.path.join(HERE, "docs", "sitemap.xml"), encoding="utf-8").read()
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    assert len(locs) >= 15
    llms = open(os.path.join(HERE, "docs", "llms.txt"), encoding="utf-8").read()
    base = "https://erditech.github.io/laser-rangefinder-module-database/"
    for u in locs:
        rel = u[len(base):]
        if rel.startswith("data/"):
            assert os.path.exists(os.path.join(HERE, "docs", rel))
            continue
        p = os.path.join(HERE, "docs", rel, "index.html")
        html = open(p, encoding="utf-8").read()
        assert "application/ld+json" in html and "<title>" in html and 'rel="canonical"' in html, rel
        hub = rel in ("alternatives/", "guides/")
        assert ("<ul" in html) if hub else ("<table" in html), rel
        assert u in llms, rel
