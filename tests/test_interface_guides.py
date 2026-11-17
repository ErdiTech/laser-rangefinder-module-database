import html
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("slug,count", [
    ("can-bus-rangefinder-modules", 13),
    ("i2c-rangefinder-modules", 37),
])
def test_interface_guides_preserve_source_conditions_and_omit_prices(slug, count):
    page = (ROOT / "docs" / "guides" / slug / "index.html").read_text()
    assert f"Matching modules ({count})" in page
    assert "USD (1 pc)" not in page
    assert "Request price" in page
    rows = json.loads((ROOT / "data" / "modules.json").read_text())
    for row in rows:
        model = f'>{html.escape(row["model"])}<'
        if model in page:
            assert html.escape(row["range_condition"] or "") in page
            assert html.escape(row["source_url"]) in page
            assert row["status"] != "discontinued"
    assert "not a claim" in page if slug.startswith("can-") else "not an air rating" in page
