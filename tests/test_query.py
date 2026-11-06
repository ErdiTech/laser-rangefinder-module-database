import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import query

ROWS = query.load()


def test_loaded():
    assert len(ROWS) >= 100


def test_min_range():
    r = query.select(ROWS, min_range=1000)
    assert r and all(x["max_range_m"] >= 1000 for x in r)


def test_interface_and_wavelength():
    r = query.select(ROWS, interface="uart", wavelength=905)
    assert r and all("uart" in x["interface"].lower() and x["wavelength_nm"] == 905 for x in r)


def test_weight_parse():
    assert query.grams("5 +/- 0.3 g") == 5.0
    assert query.grams(None) is None
    assert query.grams(12) == 12.0


def test_cli_json(capsys):
    assert query.main(["--brand", "Benewake", "--format", "json"]) == 0
    assert all(x["brand"] == "Benewake" for x in json.loads(capsys.readouterr().out))
