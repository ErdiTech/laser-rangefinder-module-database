#!/usr/bin/env python3
"""Regenerate MODULES.md and docs/index.html from data/modules.json."""
import html, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(ROOT, "data", "modules.json"), encoding="utf-8"))
cols = ["brand", "model", "wavelength_nm", "min_range_m", "max_range_m", "accuracy", "rate_hz",
        "interface", "weight_g", "price_public_usd"]
hdr = ["Brand", "Model", "nm", "Min m", "Max m", "Accuracy", "Rate", "Interface", "Weight", "USD", "Source"]


def c(v):
    return "" if v is None else str(v).replace("|", "/").replace("\n", " ")


md = ("# All modules\n\nGenerated from `data/modules.json` by `scripts/build_views.py`. Empty cell = not "
      "published by the vendor. Other fields (range condition, voltage, dimensions, laser class, capture "
      "date) are in the JSON/CSV.\n\n| " + " | ".join(hdr) + " |\n|" + "---|" * len(hdr) + "\n")
for r in rows:
    md += "| " + " | ".join(c(r[k]) for k in cols) + f" | [page]({r['source_url']}) |\n"
open(os.path.join(ROOT, "MODULES.md"), "w", encoding="utf-8").write(md)

tr = "".join(
    "<tr>" + "".join(f"<td>{html.escape(c(r[k]))}</td>" for k in cols)
    + f"<td><a href=\"{html.escape(r['source_url'])}\" rel=\"noopener\">source</a></td></tr>\n" for r in rows)
th = "".join(f"<th data-i=\"{i}\">{h}</th>" for i, h in enumerate(hdr))
n = len(rows)
page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Laser rangefinder module database - compare @N@ single-point LiDAR modules</title>
<meta name="description" content="Sortable table of @N@ laser rangefinder / single-point LiDAR distance modules: range, accuracy, rate, interface, weight, public price, source URL.">
<style>body{font:14px system-ui,sans-serif;margin:1rem}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:4px 6px;text-align:left}th{cursor:pointer;background:#f2f2f2;position:sticky;top:0}input{padding:6px;width:20rem;margin-bottom:8px}</style></head><body>
<h1>Laser rangefinder module database</h1>
<p>@N@ modules from 8 manufacturers. Values copied from each manufacturer public page (captured Oct-Nov 2026). Click a header to sort. <a href="https://github.com/Tommyapi/laser-rangefinder-module-database">Data and code on GitHub</a>.</p>
<input id="q" placeholder="Filter (brand, model, UART, 1535...)">
<table id="t"><thead><tr>@TH@</tr></thead><tbody>
@TR@</tbody></table>
<script>
var t=document.getElementById('t'),b=t.tBodies[0],dir={};
function v(c){var x=parseFloat(c.textContent);return isNaN(x)?c.textContent.toLowerCase():x}
t.tHead.onclick=function(e){var i=+e.target.dataset.i;if(isNaN(i))return;dir[i]=!dir[i];
var r=[].slice.call(b.rows).sort(function(a,c){var x=v(a.cells[i]),y=v(c.cells[i]);
if(x==='')return 1;if(y==='')return -1;return (x>y?1:x<y?-1:0)*(dir[i]?1:-1)});r.forEach(function(x){b.appendChild(x)})};
document.getElementById('q').oninput=function(){var s=this.value.toLowerCase();[].forEach.call(b.rows,function(r){r.style.display=r.textContent.toLowerCase().indexOf(s)<0?'none':''})};
</script></body></html>""".replace("@N@", str(n)).replace("@TH@", th).replace("@TR@", tr)
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
open(os.path.join(ROOT, "docs", "index.html"), "w", encoding="utf-8").write(page)
print("built", n, "rows")
