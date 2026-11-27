#!/usr/bin/env python3
"""Regenerate every derived file from data/modules.json.

Outputs: data/modules.csv, MODULES.md, README stats block, and the static GitHub Pages site in docs/
(index table, "<model> alternatives" pages, selection guides, 905 vs 1535 nm page, sitemap.xml,
robots.txt, llms.txt, data copies). Pages are plain HTML with JSON-LD; JavaScript only adds
sorting/filtering to the main table, everything is readable without it.
Usage: python scripts/build_views.py
"""
import csv
import datetime
import functools
import subprocess
import html
import io
import json
import math
import os
import re
import shutil
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (FIELDS, REPO, ROOT, SITE, data_date, fmt_num, fmt_range, has_driver, iface_tags, load,  # noqa
                    price_band, row_id, short_brand, wl_class)
import site_chrome as UI  # noqa: E402  shared erditech.com navigation, footer and design system links
import site_clean as SC  # noqa: E402  display-only cleanup of editor notes in spec cells

E = html.escape
ROWS = load()
DATE = data_date(ROWS)
DOCS = os.path.join(ROOT, "docs")
YEAR = datetime.date.today().year
PAGE_DATES = {}
PAGES = []  # (path relative to SITE, title, description) for sitemap / llms.txt
ORG = {"@type": "Organization", "name": "ERDI TECH LTD", "url": "https://erdilrf.com/"}

RANGE_ROWS = [r for r in ROWS if r["category"] != "laser source (component)" and r.get("max_range_m")]
N_MOD = sum(1 for r in ROWS if r["category"] == "rangefinder module")
N_SCAN = sum(1 for r in ROWS if r["category"] == "scanning rangefinder")
N_SRC = sum(1 for r in ROWS if r["category"] == "laser source (component)")
EXTRA = f"plus {N_SCAN} single-beam scanning rangefinders and {N_SRC} pulsed laser sources"


def write(rel, text):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def cell(v):
    return "" if v is None else str(v)


# ---------------------------------------------------------------- CSV / Markdown
def csv_text():
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(FIELDS)
    for r in ROWS:
        out = []
        for k in FIELDS:
            v = r.get(k)
            if k == "open_source_drivers":
                v = " ; ".join(d["url"] for d in v) if v else ""
            out.append(cell(v))
        w.writerow(out)
    return buf.getvalue()


def md_cell(v):
    return cell(v).replace("|", "/").replace("\n", " ")


def build_md():
    hdr = ["Brand", "Model", "Type", "nm", "Min m", "Max m", "Accuracy", "Rate", "Interface", "Weight g",
           "USD (1 pc)", "Open-source driver", "Source"]
    lines = [f"# All modules ({len(ROWS)} rows, data date {DATE})", "",
             "Generated from `data/modules.json` by `scripts/build_views.py`. Empty cell = not published by the "
             "manufacturer. Range conditions, voltage, dimensions, laser class, volume prices and capture dates are "
             "in the JSON/CSV. Interactive version: " + SITE, "",
             "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for r in sorted(ROWS, key=lambda r: (short_brand(r["brand"]).lower(), r.get("max_range_m") or 0, r["model"])):
        drv = ", ".join(f"[{d['name']}]({d['url']})" for d in r["open_source_drivers"])
        lines.append("| " + " | ".join(md_cell(x) for x in [
            short_brand(r["brand"]), r["model"], r["category"].replace(" (component)", ""), r["wavelength_nm"],
            fmt_num(r["min_range_m"]), fmt_num(r["max_range_m"]), r["accuracy"], r["rate_hz"], r["interface"],
            fmt_num(r["weight_g"]), fmt_num(r["price_public_usd"])]) + f" | {drv} | [source]({r['source_url']}) |")
    return "\n".join(lines) + "\n"


def brand_counts():
    c = {}
    for r in ROWS:
        c[r["brand"]] = c.get(r["brand"], 0) + 1
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))


def readme_stats():
    n_mod = sum(1 for r in ROWS if r["category"] == "rangefinder module")
    n_scan = sum(1 for r in ROWS if r["category"] == "scanning rangefinder")
    n_src = sum(1 for r in ROWS if r["category"] == "laser source (component)")
    lines = [f"**{len(ROWS)} rows from {len(brand_counts())} manufacturers** ({n_mod} rangefinder modules, "
             f"{n_scan} scanning rangefinders, {n_src} laser-source components) · data date **{DATE}** · "
             f"[open the sortable table]({SITE})", "",
             "| Manufacturer | Rows |", "|---|---|"]
    lines += [f"| {b} | {n} |" for b, n in brand_counts()]
    return "\n".join(lines)


def update_readme():
    p = os.path.join(ROOT, "README.md")
    t = open(p, encoding="utf-8").read()
    t2 = re.sub(r"<!-- stats:start -->.*?<!-- stats:end -->",
                "<!-- stats:start -->\n" + readme_stats() + "\n<!-- stats:end -->", t, flags=re.S)
    t2 = re.sub(r"<!-- count -->\d+<!-- /count -->", f"<!-- count -->{len(ROWS)}<!-- /count -->", t2)
    t2 = re.sub(r"<!-- nmod -->\d+<!-- /nmod -->", f"<!-- nmod -->{N_MOD}<!-- /nmod -->", t2)
    t2 = re.sub(r"<!-- date -->[\d-]+<!-- /date -->", f"<!-- date -->{DATE}<!-- /date -->", t2)
    if t2 != t:
        write("README.md", t2)


# ---------------------------------------------------------------- HTML helpers
CSS = """.prose .wrap{overflow-x:auto}"""


@functools.lru_cache(maxsize=None)
def source_modified(*paths):
    dates = []
    for path in paths:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", path], cwd=ROOT,
            capture_output=True, text=True, check=True)
        value = result.stdout.strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            dates.append(value)
    if not dates:
        raise RuntimeError("Source history required for dateModified")
    return max(dates)


def page(rel, title, desc, body, jsonld, extra_head=""):
    canon = SITE + rel
    modified = source_modified("data/modules.json", "scripts/build_views.py", "scripts/common.py")
    PAGE_DATES[rel] = modified
    if rel.startswith(("compare/", "guides/", "alternatives/")):
        title = f"{title} ({YEAR})"
        desc = f"{YEAR}: {desc}"
        body = re.sub(r"(<h1[^>]*>)(.*?)(</h1>)",
                      lambda m: f"{m[1]}{m[2]} ({YEAR}){m[3]}", body, count=1)
    stamp = datetime.date.fromisoformat(modified).strftime("%b %Y")
    body = re.sub(r"(</h1>)", rf'\1<p class="muted">Updated: {stamp}</p>', body, count=1)
    jsonld = [dict(j, dateModified=modified) if j.get("@type") in
              ("Article", "TechArticle", "WebPage", "Dataset") else j for j in jsonld]
    jsonld.append({"@context": "https://schema.org", "@type": "WebPage",
                   "url": canon, "name": title, "dateModified": modified})
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in jsonld)
    section = rel.split("/")[0] if "/" in rel else ""
    img, img_m, fx = UI.HEROES.get(section, UI.HEROES[""])
    m = re.search(r"<h1[^>]*>(.*?)</h1>(<p class=\"muted\">Updated: [^<]*</p>)?", body, re.S)
    h1_html = m.group(1) if m else E(title)
    stamp_html = m.group(2) or "" if m else ""
    if m:
        body = body.replace(m.group(0), "", 1)
    crumb = ['<a href="https://erditech.com/">ERDI TECH</a>', '<span aria-hidden="true">/</span>',
             f'<a href="{SITE}">Module database</a>']
    if section:
        crumb += ['<span aria-hidden="true">/</span>', f'<a href="{SITE}{section}/">{UI.SECTION_NAMES.get(section, section)}</a>']
    meta = [f"<span>{N_MOD} modules in the database</span>", f"<span>Data date {DATE}</span>"]
    if stamp_html:
        meta.insert(0, "<span>" + re.sub(r"<[^>]+>", "", stamp_html) + "</span>")
    hero = (f'<section class="phero" data-dark data-glow style="--fx:{fx}">\n'
            f'<div class="phero-media"><picture><source media="(max-width: 760px)" srcset="{img_m}" width="720" height="1280">'
            f'<source media="(min-width: 761px)" type="image/avif" srcset="{img[:-5]}.avif"><img src="{img}" alt="" width="1600" height="900" fetchpriority="high" decoding="async"></picture></div>\n'
            f'<div class="wrap"><div class="phero-copy"><p class="crumbs">{"".join(crumb)}</p>'
            f'<h1{" class=" + chr(34) + "vt-database" + chr(34) if rel == "" else ""}>{h1_html}</h1><div class="ph-meta">{"".join(meta)}</div></div></div>\n'
            '<p class="beam-note">Beam drawn for illustration: 905 and 1535 nm light is invisible to the eye.</p>'
            '<span class="ph-line" aria-hidden="true"></span></section>\n')
    preload = (f'<link rel="preload" as="image" type="image/avif" href="{img[:-5]}.avif" media="(min-width: 761px)" fetchpriority="high">\n'
               f'<link rel="preload" as="image" href="{img_m}" media="(max-width: 760px)" fetchpriority="high">')
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canon}"><meta property="og:type" content="website">
<meta name="theme-color" content="#0b1424">
{preload}
{UI.HEAD}
<style>{CSS}</style>
{ld}{extra_head}
</head><body>
<a class="skip" href="#main">Skip to content</a>
{UI.SPRITE}
{UI.NAV}
{hero}<main id="main" class="page-body"><div class="wrap prose">
{body}
<p class="gen-note">Laser rangefinder module database · data date {DATE} · values copied from each manufacturer's public page or datasheet, linked per row ·
<a href="{REPO}">GitHub</a> (MIT; corrections welcome as pull requests) · <a href="{SITE}data/modules.csv">CSV</a> · <a href="{SITE}data/modules.json">JSON</a> ·
Maintained by ERDI TECH LTD (<a href="https://erdilrf.com/">erdilrf.com</a>), which also makes some of the listed modules.</p>
</div></main>
{UI.FOOTER}{UI.SPEC}
{UI.SCRIPTS}
</body></html>
"""
    write(os.path.join("docs", rel, "index.html") if not rel.endswith(".html") else os.path.join("docs", rel), doc)
    PAGES.append((rel, title, desc))


def crumbs(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}


def itemlist(name, rows, url):
    return {"@context": "https://schema.org", "@type": "ItemList", "name": name, "url": url,
            "numberOfItems": len(rows), "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": f"{short_brand(r['brand'])} {r['model']}",
                 "url": r["product_url"]} for i, r in enumerate(rows)]}


def drv_html(r):
    return ", ".join(f'<a href="{E(d["url"])}">{E(d["name"])}</a>' for d in r["open_source_drivers"])


COLS = [  # key, header, renderer, numeric?
    ("brand", "Brand", lambda r: E(short_brand(r["brand"])), False),
    ("model", "Model", lambda r: f'<a href="{E(r["product_url"])}">{E(r["model"])}</a>', False),
    ("wl", "nm", lambda r: fmt_num(r["wavelength_nm"]), True),
    ("max", "Max range", lambda r: fmt_range(r["max_range_m"]), True),
    ("cond", "Range condition", lambda r: UI.cond_html(SC.clean(cell(r["range_condition"])), E), False),
    ("min", "Min (m)", lambda r: fmt_num(r["min_range_m"]), True),
    ("acc", "Accuracy", lambda r: UI.cond_html(SC.clean(cell(r["accuracy"])), E, 220), False),
    ("rate", "Rate", lambda r: E(SC.clean(cell(r["rate_hz"]))), False),
    ("if", "Interface", lambda r: E(cell(r["interface"])), False),
    ("w", "Weight (g)", lambda r: fmt_num(r["weight_g"]), True),
    ("usd", "USD", lambda r: fmt_num(r["price_public_usd"]), True),
    ("drv", "Driver", drv_html, False),
    ("src", "Source", lambda r: f'<a href="{E(r["source_url"])}">source</a> <span class="muted">{r["captured_at"]}</span>', False),
]


def table(rows, cols=None, self_row=None, extra=None, sortable=False, full_conditions=False):
    cols = cols or [c[0] for c in COLS]
    spec = [c for c in COLS if c[0] in cols]
    th = "".join(f'<th data-k="{k}">{h}</th>' if sortable else f"<th>{h}</th>" for k, h, _, _ in spec)
    if extra:
        th += f"<th>{extra[0]}</th>"
    out = [f'<div class="tbl"><table class="cards"{" id=t" if sortable else ""}><thead><tr>{th}</tr></thead><tbody>']
    for r in rows:
        attrs = ""
        if sortable:
            attrs = (f' id="{row_id(r)}" data-range="{r.get("max_range_m") or ""}" data-wl="{wl_class(r)}" '
                     f'data-if="{" ".join(iface_tags(r))}" data-price="{r.get("price_public_usd") or ""}" '
                     f'data-drv="{1 if has_driver(r) else 0}" data-cat="{E(r["category"])}" '
                     f'data-status="{r["status"]}"')
        cls = ' class="self"' if r is self_row else ""
        tds = "".join(f'<td{" class=n" if num else ""}>{E(cell(r["range_condition"])) if k == "cond" and full_conditions else fn(r)}</td>'
                      for k, _, fn, num in spec)
        if extra:
            tds += f"<td>{extra[1](r)}</td>"
        out.append(f"<tr{cls}{attrs}>{tds}</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def nav(extra=""):
    return (f'<nav><a href="{SITE}">All modules</a> · <a href="{SITE}guides/">Selection guides</a> · '
            f'<a href="{SITE}alternatives/">Alternatives</a> · <a href="{SITE}compare/905nm-vs-1535nm/">905 vs 1535 nm</a> · '
            f'<a href="{SITE}compare/tfmini-vs-sf11-vs-long-range/">TFmini vs SF11 vs long range</a>'
            f'{extra}</nav>')


def name(r):
    return f"{short_brand(r['brand'])} {r['model']}"


def find(model_regex, brand=None):
    for r in ROWS:
        if re.fullmatch(model_regex, r["model"], re.I) and (brand is None or r["brand"].startswith(brand)):
            return r
    return None


# ---------------------------------------------------------------- index
def build_index():
    n = len(ROWS)
    makers = len(brand_counts())
    n1k = sum(1 for r in RANGE_ROWS if r["max_range_m"] >= 1000)
    n1535 = sum(1 for r in RANGE_ROWS if wl_class(r) == "1535")
    ndrv = sum(1 for r in ROWS if has_driver(r))
    dataset = {
        "@context": "https://schema.org", "@type": "Dataset",
        "name": "Laser rangefinder module database",
        "alternateName": "Single-point LiDAR / laser distance module comparison dataset",
        "description": (f"Open dataset of {N_MOD} single-point laser rangefinder and LiDAR distance modules ({EXTRA}) "
                        f"from {makers} manufacturers: wavelength, minimum and maximum range with the quoted target condition, "
                        "accuracy, update rate, interface (UART, I2C, CAN, RS-422, RS-485), voltage, weight, "
                        "dimensions, laser class, public price, open-source driver links, and the manufacturer "
                        "source URL and capture date for every row."),
        "url": SITE, "sameAs": REPO, "license": "https://opensource.org/licenses/MIT",
        "isAccessibleForFree": True, "dateModified": DATE, "creator": ORG, "publisher": ORG, "maintainer": ORG,
        "keywords": ["laser rangefinder module", "LiDAR distance sensor", "single-point LiDAR", "905 nm", "1535 nm",
                     "drone altimeter", "TFmini", "LightWare", "UART", "rangefinder comparison"],
        "variableMeasured": ["wavelength_nm", "min_range_m", "max_range_m", "accuracy", "rate_hz", "interface",
                             "voltage", "weight_g", "dimensions", "laser_class", "price_public_usd"],
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": SITE + "data/modules.csv"},
            {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": SITE + "data/modules.json"}],
        "citation": f"ERDI TECH LTD. Laser rangefinder module database ({DATE}). {REPO}",
    }
    brands = sorted({short_brand(r["brand"]) for r in ROWS}, key=str.lower)
    body = f"""{nav()}
<h1>Laser rangefinder module database</h1>
<p>Official ERDI TECH LTD open engineering dataset, maintained in Chengdu, China.
Contact Tommy Yu, Overseas Sales: <a href="mailto:tommy@erdimail.com">tommy@erdimail.com</a>;
WhatsApp +86 133 0819 5790. <a href="https://erdilrf.com/">Product catalogue and enquiries</a>.</p>
<p>Compare <strong>{N_MOD}</strong> single-point laser rangefinder / LiDAR distance modules ({EXTRA}; {n} rows) from
{makers} manufacturers ({', '.join(E(b) for b in brands)}). Every value is copied from the manufacturer's own product page or datasheet,
with the source link and the date it was read. Empty cell = the manufacturer does not publish that value.
Data date: <strong>{DATE}</strong>. {n1k} modules list 1 km or more; {n1535} use 1535/1550 nm; {ndrv} have an open-source
driver that names the exact model.</p>
<p class="muted">Scope: integrated single-point laser/ToF distance modules, single-beam scanning rangefinders and pulsed
laser sources for rangefinders; not bare ToF-chip breakouts, 3D LiDAR, radar or handheld rangefinders.
Max range is only comparable together with its <em>range condition</em> (target size and reflectance,
visibility). Download: <a href="data/modules.csv">CSV</a> · <a href="data/modules.json">JSON</a> ·
<a href="data/schema.json">schema</a> · <a href="{REPO}">GitHub</a>.</p>
<p>Guides: <a href="guides/drone-altimeter-1km/">drone altimeter, 1 km</a> · <a href="guides/eye-safe-1535nm/">eye-safe 1535 nm</a> ·
<a href="guides/long-range-over-2km/">long range over 2 km</a> · <a href="guides/under-50-usd/">under $50</a> ·
<a href="guides/open-source-driver-ros2-arduino/">with ROS 2 / Arduino / ArduPilot driver</a> ·
<a href="compare/905nm-vs-1535nm/">905 vs 1535 nm</a> · <a href="compare/tfmini-vs-sf11-vs-long-range/">TFmini vs SF11 vs long range</a> ·
<a href="alternatives/">alternatives to popular models</a></p>
<form class="f" id="f" onsubmit="return false">
<label>Search<input id="q" placeholder="brand, model, text"></label>
<label>Min range (m)<input id="rmin" type="number" min="0" step="any" placeholder="e.g. 1000"></label>
<label>Max range up to (m)<input id="rmax" type="number" min="0" step="any"></label>
<label>Wavelength<select id="wl"><option value="">any</option><option value="905">850-940 nm</option><option value="1535">1535/1550 nm</option></select></label>
<label>Interface<select id="if"><option value="">any</option><option>UART</option><option>I2C</option><option>CAN</option><option>RS-422</option><option>RS-485</option><option>RS-232</option><option>USB</option><option>PWM</option></select></label>
<label>Price (1 pc)<select id="pr"><option value="">any</option><option value="0-50">under $50</option><option value="50-150">$50-150</option><option value="150-500">$150-500</option><option value="500-2000">$500-2,000</option><option value="2000-1e9">over $2,000</option><option value="none">not published</option></select></label>
<label>Open-source driver<select id="dr"><option value="">any</option><option value="1">yes</option><option value="0">no</option></select></label>
<label>Type<select id="ct"><option value="">all</option><option>rangefinder module</option><option>scanning rangefinder</option><option>laser source (component)</option></select></label>
<span class="muted" id="cnt">{n} shown</span>
</form>
{table(ROWS, sortable=True)}
<script>
(function(){{var t=document.getElementById('t'),b=t.tBodies[0],dir={{}};
function val(td){{var s=td.textContent.replace(/,/g,'');var m=s.match(/^-?[\\d.]+/);if(m)return parseFloat(m[0])*(/ km/.test(s)?1000:1);return s.trim().toLowerCase()}}
t.tHead.onclick=function(e){{var th=e.target.closest('th');if(!th)return;var i=th.cellIndex;dir[i]=!dir[i];
[].slice.call(b.rows).sort(function(x,y){{var a=val(x.cells[i]),c=val(y.cells[i]);if(a==='')return 1;if(c==='')return -1;
if(typeof a!==typeof c){{a=String(a);c=String(c)}}return(a>c?1:a<c?-1:0)*(dir[i]?1:-1)}}).forEach(function(r){{b.appendChild(r)}})}};
var g=function(id){{return document.getElementById(id)}};
function run(){{var q=g('q').value.toLowerCase(),lo=parseFloat(g('rmin').value),hi=parseFloat(g('rmax').value),wl=g('wl').value,ifc=g('if').value,pr=g('pr').value,dr=g('dr').value,ct=g('ct').value,n=0;
[].forEach.call(b.rows,function(r){{var d=r.dataset,rg=parseFloat(d.range),p=parseFloat(d.price),ok=true;
if(q&&r.textContent.toLowerCase().indexOf(q)<0)ok=false;if(!isNaN(lo)&&!(rg>=lo))ok=false;if(!isNaN(hi)&&!(rg<=hi))ok=false;
if(wl&&d.wl!==wl)ok=false;if(ifc&&(' '+d.if+' ').indexOf(' '+ifc+' ')<0)ok=false;if(dr&&d.drv!==dr)ok=false;if(ct&&d.cat!==ct)ok=false;
if(pr){{if(pr==='none'){{if(!isNaN(p))ok=false}}else{{var a=pr.split('-');if(isNaN(p)||p<+a[0]||p>=+a[1])ok=false}}}}
r.style.display=ok?'':'none';if(ok)n++}});g('cnt').textContent=n+' shown'}}
['q','rmin','rmax','wl','if','pr','dr','ct'].forEach(function(id){{g(id).addEventListener('input',run)}});
var u=new URLSearchParams(location.search);['q','rmin','rmax','wl','if','pr','dr','ct'].forEach(function(id){{if(u.get(id))g(id).value=u.get(id)}});run();}})();
</script>"""
    page("", f"Laser rangefinder module database: compare {N_MOD} single-point LiDAR modules",
         f"Sortable, filterable table of {N_MOD} laser rangefinder / single-point LiDAR modules from {makers} makers: range "
         "and target condition, wavelength (905/1535 nm), accuracy, rate, UART/I2C/CAN interface, weight, price, drivers.",
         body, [dataset])


# ---------------------------------------------------------------- alternatives
HOT = [  # (model regex, brand prefix)
    (r"TFmini-S", "Benewake"), (r"TF-Luna", "Benewake"), (r"TFmini Plus", "Benewake"), (r"TF02-Pro", "Benewake"),
    (r"TF03.*", "Benewake"), (r"TF350", "Benewake"), (r"SF11/C", "LightWare"), (r"SF30/D", "LightWare"),
    (r"SF30/C", "LightWare"), (r"LW20/C", "LightWare"), (r"GRF-500", "LightWare"), (r"LIDAR-Lite v3HP", "Garmin"),
    (r"LIDAR-Lite v3", "Garmin"), (r"(TeraRanger )?Evo 60m", "Terabee"), (r"(TeraRanger )?Evo 15m", "Terabee"),
]


def similar(x, rows, lo=0.5, hi=2.5):
    R = x["max_range_m"]
    W = x.get("weight_g")
    xt = set(iface_tags(x))
    out = []
    for r in rows:
        if r is x or r["category"] != "rangefinder module" or r["status"] == "discontinued":
            continue
        rr = r["max_range_m"]
        if not (lo * R <= rr <= hi * R):
            continue
        s = abs(math.log(rr / R))
        if W and r.get("weight_g"):
            s += 0.3 * abs(math.log(r["weight_g"] / W))
        if xt and not (xt & set(iface_tags(r))):
            s += 0.4
        if wl_class(r) != wl_class(x):
            s += 0.15
        out.append((s, r))
    out.sort(key=lambda t: (t[0], name(t[1]).lower()))
    return [r for _, r in out]


def why(x):
    def f(r):
        bits = [f"range ×{r['max_range_m'] / x['max_range_m']:.2g}"]
        if x.get("weight_g") and r.get("weight_g"):
            bits.append(f"weight ×{r['weight_g'] / x['weight_g']:.2g}")
        common = sorted(set(iface_tags(x)) & set(iface_tags(r)))
        bits.append("shared interface: " + "/".join(common) if common else "different interface")
        return E("; ".join(bits))
    return f


def build_alternatives():
    done = []
    for rx, brand in HOT:
        x = find(rx, brand)
        if not x or not x.get("max_range_m") or x in [d[1] for d in done]:
            continue
        s = re.sub(r"[^a-z0-9]+", "-", x["model"].lower().replace("+", "-plus")).strip("-")
        rel = f"alternatives/{s}/"
        alts = similar(x, RANGE_ROWS)[:25]
        cheaper_longer = []
        if x.get("price_public_usd"):
            cheaper_longer = sorted(
                [r for r in RANGE_ROWS if r is not x and r["category"] == "rangefinder module"
                 and r["status"] != "discontinued" and r.get("price_public_usd") is not None
                 and r["price_public_usd"] <= x["price_public_usd"] and r["max_range_m"] > 2.5 * x["max_range_m"]],
                key=lambda r: (r["max_range_m"], r["price_public_usd"]))
        ifs = "/".join(iface_tags(x)) or "not stated"
        spec = (f"{E(name(x))} ({E(x['category'])}): {fmt_num(x['wavelength_nm']) + ' nm' if x['wavelength_nm'] else 'wavelength not published'}, "
                f"max range {fmt_range(x['max_range_m'])}"
                + (f" ({E(x['range_condition'])})" if x.get("range_condition") else "")
                + f", interface {E(ifs)}"
                + (f", {fmt_num(x['weight_g'])} g" if x.get("weight_g") else "")
                + (f", public price ${fmt_num(x['price_public_usd'])}" if x.get("price_public_usd") else "")
                + (f". Status on the source page: {x['status']}" if x["status"] != "active" else "") + ".")
        title = f"{name(x)} alternatives: {len(alts)} comparable laser rangefinder modules"
        desc = (f"Modules comparable to the {name(x)} ({fmt_range(x['max_range_m'])}, {ifs}): same range class, "
                f"weight and interface, with manufacturer-sourced specs, prices and drivers. Data date {DATE}.")
        body = [nav(), f"<h1>{E(name(x))} alternatives</h1>",
                f"<p><strong>Reference module.</strong> {spec} <a href=\"{E(x['source_url'])}\">Source</a>.</p>",
                f"<p>Below are the {len(alts)} catalogued modules whose published maximum range is between 0.5× and 2.5× "
                f"of the {E(name(x))}, ordered by how close they are in range, then weight, interface and wavelength "
                "class (no manufacturer is ranked by preference). None of them is a drop-in replacement unless the "
                "protocol, connector, supply voltage and mounting match; check the linked datasheet. Ranges are "
                "quoted by each maker under its own target condition, so compare the condition column too.</p>",
                table([x] + alts, self_row=x, extra=("Compared with reference", why(x)))]
        if cheaper_longer:
            body += [f"<h2>Longer range at or below the {E(name(x))} public price</h2>",
                     f"<p>Modules with more than 2.5× the range whose public single-unit price is at or below "
                     f"${fmt_num(x['price_public_usd'])}. Only makers that publish prices can appear here.</p>",
                     table(cheaper_longer[:20], extra=("Compared with reference", why(x)))]
        body.append(f'<p class="muted">Missing a module? Add it in <a href="{REPO}">a pull request</a> with the '
                    "manufacturer source link.</p>")
        page(rel, title, desc, "\n".join(body),
             [itemlist(f"Alternatives to {name(x)}", alts, SITE + rel),
              crumbs([("Database", ""), ("Alternatives", "alternatives/"), (name(x), rel)])])
        done.append((rel, x, len(alts)))
    items = "".join(f'<li><a href="{rel.split("/", 1)[1]}">{E(name(x))} alternatives</a> '
                    f'<span class="muted">({fmt_range(x["max_range_m"])}, {n} comparable modules)</span></li>'
                    for rel, x, n in done)
    page("alternatives/", "Alternatives to popular laser rangefinder and LiDAR modules",
         "Comparable modules for TFmini-S, TF-Luna, TF02-Pro, TF03, SF11/C, SF30/D, LW20/C, LIDAR-Lite v3HP, "
         "TeraRanger Evo and others, from an open manufacturer-sourced dataset.",
         f"{nav()}<h1>Alternatives to popular modules</h1><p>Each page lists modules from the database with a similar "
         f"published range, weight and interface. Data date {DATE}.</p><ul class=cols>{items}</ul>",
         [crumbs([("Database", ""), ("Alternatives", "alternatives/")])])
    return done


# ---------------------------------------------------------------- guides
def under(v, lim):
    return v is not None and v <= lim


GUIDES = [
    {"slug": "can-bus-rangefinder-modules", "title": "Laser rangefinder modules with a published CAN interface",
     "short": "CAN interface modules",
     "rule": "category is rangefinder module, published interface includes CAN, published max range is present, "
             "and status is not discontinued",
     "filter": lambda r: r["category"] == "rangefinder module" and "CAN" in iface_tags(r)
     and r["status"] != "discontinued",
     "sort": lambda r: (short_brand(r["brand"]).lower(), r["model"]),
     "cols": [c[0] for c in COLS if c[0] != "usd"],
     "notes": ["CAN in the interface field is a shortlist criterion, not a claim that two modules share a "
               "message format, connector or application protocol. Confirm the exact interface variant, bitrate, "
               "pinout, termination and protocol document before integration.",
               "Keep each range beside its manufacturer's target condition. The table is ordered by manufacturer "
               "and model, not by an inferred performance ranking.",
               "Empty fields retain the dataset's null meaning: no published value is recorded. Check the linked "
               "source and capture date for availability and current specifications. Request prices from each maker; this page does not list them."]},
    {"slug": "i2c-rangefinder-modules", "title": "Laser rangefinder modules with a published I2C interface",
     "short": "I2C interface modules",
     "rule": "category is rangefinder module, published interface includes I2C, IIC or I²C, published max range "
             "is present, and status is not discontinued",
     "filter": lambda r: r["category"] == "rangefinder module" and "I2C" in iface_tags(r)
     and r["status"] != "discontinued",
     "sort": lambda r: (short_brand(r["brand"]).lower(), r["model"]),
     "cols": [c[0] for c in COLS if c[0] != "usd"],
     "notes": ["I2C labels do not establish plug compatibility. Confirm supply and logic voltage separately, "
               "address selection, pull-up requirements, register map and the exact ordered interface variant.",
               "The interface filter includes modules intended for different media and target conditions. "
               "Read the range condition before comparing rows; an underwater specification is not an air rating.",
               "A listed driver names a particular model; an empty driver field is not proof that no driver "
               "exists. No electrical limits, range values or compatibility claims have been inferred. Request prices from each maker; this page does not list them."]},
    {"slug": "drone-altimeter-1km", "title": "Laser rangefinder modules for a 1 km drone altimeter",
     "short": "drone altimeter, 1 km",
     "rule": "published max range ≥ 1,000 m, published weight ≤ 60 g, and a UART, I2C or CAN interface "
             "that a flight controller or companion computer can read",
     "filter": lambda r: r["max_range_m"] >= 1000 and under(r.get("weight_g"), 60)
     and bool({"UART", "I2C", "CAN"} & set(iface_tags(r))),
     "sort": lambda r: (r["weight_g"], -r["max_range_m"]),
     "notes": ["Datasheet ranges are usually quoted for a large, high-reflectance target (often 90% whiteboard or a "
               "building) in good visibility. Grass, crops, water and snow return less light, so the usable "
               "altitude over terrain is normally well below the headline number; check the range condition column.",
               "Update rate matters for terrain following: a 1-10 Hz long-range module suits survey altitude "
               "hold, while landing and obstacle work usually needs 50 Hz or more at short range.",
               "Check how the flight stack will read the sensor: the driver column lists open-source drivers "
               "(ArduPilot, ROS 2, Arduino) that name the exact model; others need a companion computer or a custom "
               "driver using the manufacturer's protocol document."]},
    {"slug": "eye-safe-1535nm", "title": "Eye-safe 1535 / 1550 nm laser rangefinder modules",
     "short": "eye-safe 1535 nm",
     "rule": "published wavelength 1400-1700 nm (in practice 1535 and 1550 nm Er:glass or fibre-laser based modules)",
     "filter": lambda r: wl_class(r) == "1535",
     "sort": lambda r: (r["max_range_m"], r.get("weight_g") or 1e9),
     "notes": ["1535/1550 nm light is absorbed before it reaches the retina, so IEC 60825-1 allows far more pulse "
               "energy at these wavelengths than at 905 nm for the same laser class. That is why multi-kilometre "
               "Class 1 modules are almost all 1.5 µm designs.",
               "The trade-off is cost and size: 1.5 µm modules need an InGaAs detector and usually an "
               "erbium-glass laser, so they cost and weigh more than 905 nm modules of similar short-range "
               "performance. The laser class actually certified for a given module is in its datasheet; the "
               "laser_class column is empty where the maker does not publish it.",
               "Most long-range 1535 nm modules use RS-422 or 3.3 V TTL UART and update at 1-10 Hz."]},
    {"slug": "long-range-over-2km", "title": "Long-range laser rangefinder modules (over 2 km)",
     "short": "long range over 2 km",
     "rule": "published max range ≥ 2,000 m (any wavelength)",
     "filter": lambda r: r["max_range_m"] >= 2000,
     "sort": lambda r: (r["max_range_m"], r.get("weight_g") or 1e9),
     "notes": ["Range conditions differ a lot at this distance: target size (for example 2.3 × 2.3 m vehicle-sized "
               "targets), reflectance (often 30%) and visibility (often ≥ 10 km). Two modules with the same headline "
               "number can perform very differently on the same target.",
               "Beam divergence and receiver aperture determine whether small targets (people, drones, poles) are "
               "measurable at range; they are in the linked datasheets but not normalised in this table."]},
    {"slug": "under-50-usd", "title": "Low-cost laser rangefinder modules: public price under $50",
     "short": "under $50",
     "rule": "a public single-unit price of $50 or less on the manufacturer's own site",
     "filter": lambda r: r.get("price_public_usd") is not None and r["price_public_usd"] <= 50,
     "sort": lambda r: (r["price_public_usd"], -r["max_range_m"]),
     "second": ("Public price $50-150", lambda r: r.get("price_public_usd") is not None
                and 50 < r["price_public_usd"] <= 150),
     "notes": ["Many manufacturers (for example Benewake, Nooploop, Terabee and most long-range OEM makers) sell "
               "through distributors or by quotation and publish no price on their own site. Their modules cannot "
               "appear on this page even if distributors sell them below $50; filter the main table by range and "
               "interface instead.",
               "Prices are single-unit list prices on the capture date; volume tiers are in the JSON/CSV "
               "(price_volume_usd, price_volume_min_qty)."]},
    {"slug": "open-source-driver-ros2-arduino",
     "title": "Laser rangefinder modules with open-source ROS 2, Arduino or ArduPilot drivers",
     "short": "with ROS 2 / Arduino / ArduPilot driver",
     "rule": "at least one open-source driver or documented open-source flight-stack integration that names the "
             "exact model (manufacturer repositories, ArduPilot AP_RangeFinder documentation)",
     "filter": lambda r: has_driver(r),
     "sort": lambda r: (short_brand(r["brand"]).lower(), r["max_range_m"]),
     "notes": ["A driver listed here names the model explicitly. Modules from the same family may work with the same "
               "protocol, but they are only listed when the driver or its documentation names them.",
               "ArduPilot links point to the ArduPilot rangefinder documentation; the driver code itself is in the "
               "ArduPilot repository (libraries/AP_RangeFinder, GPLv3).",
               "Where to buy: each model name links to the manufacturer's product page (online shop or quotation "
               "form); the price column shows the public single-unit price where one is published."]},
]


def build_guides():
    links = []
    for g in GUIDES:
        rows = sorted([r for r in RANGE_ROWS if r["category"] != "laser source (component)" and g["filter"](r)],
                      key=g["sort"])
        rel = f"guides/{g['slug']}/"
        makers = sorted({short_brand(r["brand"]) for r in rows}, key=str.lower)
        lead = (f"<p><strong>{len(rows)} modules from {len(makers)} manufacturers</strong> "
                f"({', '.join(E(m) for m in makers)}) match: {E(g['rule'])}. Data date {DATE}; every row links to the "
                "manufacturer page the values were copied from.</p>")
        body = [nav(), f"<h1>{E(g['title'])}</h1>", lead,
                "<h2>What to check</h2><ul>" + "".join(f"<li>{E(n)}</li>" for n in g["notes"]) + "</ul>",
                f"<h2>Matching modules ({len(rows)})</h2>",
                table(rows, cols=g.get("cols"), full_conditions=bool(g.get("cols")))]
        if g.get("second"):
            t2, f2 = g["second"]
            rows2 = sorted([r for r in RANGE_ROWS if f2(r)], key=lambda r: (r["price_public_usd"], -r["max_range_m"]))
            body += [f"<h2>{E(t2)} ({len(rows2)})</h2>", table(rows2)]
        shows_price = "usd" in (g.get("cols") or [c[0] for c in COLS])
        desc = (f"{len(rows)} modules matching: {g['rule']}. Manufacturer-sourced specs, "
                + ("prices and source links." if shows_price else "range conditions and source links."))
        page(rel, g["title"], desc[:300], "\n".join(body),
             [itemlist(g["title"], rows, SITE + rel), crumbs([("Database", ""), ("Guides", "guides/"), (g["short"], rel)])])
        links.append((g, len(rows)))
    items = "".join(f'<li><a href="{g["slug"]}/">{E(g["title"])}</a> <span class="muted">({n} modules)</span></li>'
                    for g, n in links)
    items += '<li><a href="../compare/905nm-vs-1535nm/">905 nm vs 1535 nm laser rangefinder modules</a></li>'
    page("guides/", "Laser rangefinder module selection guides",
         "Selection guides built from an open dataset: drone altimeter 1 km, eye-safe 1535 nm, over 2 km, under $50, "
         "open-source drivers.",
         f"{nav()}<h1>Selection guides</h1><p>Each guide is a filter over the dataset with the rule stated at the top. "
         f"Data date {DATE}.</p><ul>{items}</ul>", [crumbs([("Database", ""), ("Guides", "guides/")])])


# ---------------------------------------------------------------- 905 vs 1535
def build_wavelength():
    groups = {"905": [r for r in RANGE_ROWS if wl_class(r) == "905"],
              "1535": [r for r in RANGE_ROWS if wl_class(r) == "1535"]}

    def stat(rows):
        rng = [r["max_range_m"] for r in rows]
        w = [r["weight_g"] for r in rows if r.get("weight_g")]
        p = [r["price_public_usd"] for r in rows if r.get("price_public_usd")]
        return {"n": len(rows), "makers": len({r["brand"] for r in rows}),
                "rmin": min(rng), "rmed": statistics.median(rng), "rmax": max(rng),
                "wmin": min(w) if w else None, "wmed": statistics.median(w) if w else None,
                "pmin": min(p) if p else None, "pn": len(p),
                "ifs": sorted({t for r in rows for t in iface_tags(r)})}
    s = {k: stat(v) for k, v in groups.items()}
    rowsd = [("Modules in the database", "n", fmt_num), ("Manufacturers", "makers", fmt_num),
             ("Shortest headline max range", "rmin", fmt_range), ("Median headline max range", "rmed", fmt_range),
             ("Longest headline max range", "rmax", fmt_range), ("Lightest published weight", "wmin",
                                                                   lambda v: f"{fmt_num(v)} g" if v else "-"),
             ("Median published weight", "wmed", lambda v: f"{fmt_num(round(v, 1))} g" if v else "-"),
             ("Lowest public 1-pc price", "pmin", lambda v: f"${fmt_num(v)}" if v else "-"),
             ("Rows with a public price", "pn", fmt_num), ("Interfaces seen", "ifs", lambda v: ", ".join(v))]
    t1 = ("<div class=wrap><table><thead><tr><th></th><th>905 nm class (850-940 nm)</th><th>1535 nm class (1535/1550 nm)"
          "</th></tr></thead><tbody>" + "".join(
              f"<tr><td>{E(lab)}</td><td>{E(fn(s['905'][k]))}</td><td>{E(fn(s['1535'][k]))}</td></tr>"
              for lab, k, fn in rowsd) + "</tbody></table></div>")
    vend = {}
    for k, rows in groups.items():
        for r in rows:
            vend.setdefault(short_brand(r["brand"]), {"905": [], "1535": []})[k].append(r)
    t2 = ("<div class=wrap><table><thead><tr><th>Manufacturer</th><th>905 nm class modules</th><th>Longest 905 nm range</th>"
          "<th>1535 nm class modules</th><th>Longest 1535 nm range</th></tr></thead><tbody>")
    for b in sorted(vend, key=lambda b: (-(len(vend[b]['1535']) > 0), b.lower())):
        v = vend[b]
        t2 += (f"<tr><td>{E(b)}</td><td class=n>{len(v['905']) or ''}</td>"
               f"<td class=n>{fmt_range(max((r['max_range_m'] for r in v['905']), default=None))}</td>"
               f"<td class=n>{len(v['1535']) or ''}</td>"
               f"<td class=n>{fmt_range(max((r['max_range_m'] for r in v['1535']), default=None))}</td></tr>")
    t2 += "</tbody></table></div>"
    around1k = sorted([r for r in RANGE_ROWS if 800 <= r["max_range_m"] <= 3000 and wl_class(r) in ("905", "1535")],
                      key=lambda r: (wl_class(r), r["max_range_m"], r.get("weight_g") or 1e9))
    def wspan(rows):
        w = sorted(r["weight_g"] for r in rows if r.get("weight_g"))
        return f"{fmt_num(w[0])}-{fmt_num(w[-1])} g ({len(w)} with published weight)" if w else "n/a"
    w905 = wspan([r for r in groups["905"] if 1000 <= r["max_range_m"] <= 3000])
    w1535 = wspan([r for r in groups["1535"] if r["max_range_m"] <= 3000])
    rel = "compare/905nm-vs-1535nm/"
    body = f"""{nav()}
<h1>905 nm vs 1535 nm laser rangefinder modules</h1>
<p>Short answer: <strong>905 nm</strong> modules (silicon avalanche photodiode receivers, pulsed laser diodes) are the
low-cost, low-weight choice and in this dataset reach up to {fmt_range(s['905']['rmax'])} on large reflective targets;
<strong>1535 nm</strong> modules (InGaAs receivers, usually erbium-glass lasers) are eye-safe at much higher pulse
energy, which is why they dominate multi-kilometre ranging, at higher price and weight. The figures below are computed
from {s['905']['n'] + s['1535']['n']} modules in the open dataset (data date {DATE}).</p>
<h2>Side by side (from the dataset)</h2>{t1}
<h2>Which manufacturers sell each wavelength</h2>
<p>Counts of modules in this database, not complete product catalogues.</p>{t2}
<h2>How to choose</h2>
<ul>
<li><strong>Up to a few hundred metres</strong>, small drones and robots: 905 nm (or 850/940 nm ToF) modules are
lighter and cheaper; check update rate and interface.</li>
<li><strong>Around 1-3 km</strong>: both exist. In this dataset the 905 nm modules rated 1-3 km weigh {w905} and the
1535 nm modules rated up to 3 km weigh {w1535}. Makers quote these ranges under different target sizes and
reflectances, so compare the range condition column, not just the number.</li>
<li><strong>Beyond 2-3 km</strong>, or where Class 1 eye safety at high energy is required: 1535 nm.</li>
<li>Both wavelengths are invisible; for aiming, some modules add a visible pointer or are boresighted to a camera.</li>
</ul>
<h2>Modules from 800 m to 3 km, both wavelengths ({len(around1k)})</h2>
{table(around1k)}"""
    page(rel, "905 nm vs 1535 nm laser rangefinder modules: range, weight, price and vendors",
         "Data-based comparison of 905 nm and 1535 nm laser rangefinder modules: range, weight, public price, "
         "interfaces and which manufacturers sell each wavelength.", body,
         [crumbs([("Database", ""), ("905 vs 1535 nm", rel)]),
          {"@context": "https://schema.org", "@type": "Article",
           "headline": "905 nm vs 1535 nm laser rangefinder modules", "dateModified": DATE, "author": ORG,
           "publisher": ORG, "mainEntityOfPage": SITE + rel}])


def build_drone_classes():
    def light(r, lim):
        return r.get("weight_g") is not None and r["weight_g"] <= lim and r["category"] == "rangefinder module"             and r["status"] != "discontinued"
    classes = [
        ("Short-range ToF / LiDAR (up to 50 m)", "TFmini-S, TF-Luna, TOFSense class",
         lambda r: r["max_range_m"] <= 50 and light(r, 15), lambda r: (r["weight_g"], -r["max_range_m"])),
        ("Mid-range LiDAR (100-600 m)", "SF11/C, SF30/D, LW20/C, GRF-250/500 class",
         lambda r: 100 <= r["max_range_m"] <= 600 and light(r, 60), lambda r: (r["max_range_m"], r["weight_g"])),
        ("Long-range laser rangefinder modules (1 km and more)", "905 nm and 1535 nm OEM modules",
         lambda r: r["max_range_m"] >= 1000 and light(r, 60), lambda r: (r["max_range_m"], r["weight_g"])),
    ]
    refs = [x for x in (find(r"TFmini-S", "Benewake"), find(r"SF11/C", "LightWare")) if x]
    body = [nav(), "<h1>TFmini vs SF11 vs long-range laser rangefinder modules for drones</h1>",
            "<p>Single-point rangefinders used on drones fall into three published-range classes. The Benewake "
            "TFmini family is a short-range ToF class sensor, the LightWare SF11/C is a 100 m class LiDAR (end of "
            "life according to its maker), and long-range laser rangefinder modules rate 1 km or more. The tables "
            "below list every module in the dataset in each class that publishes a weight within the stated limit, "
            f"so the choice can be made on range, weight, rate and interface. Data date {DATE}.</p>"]
    if refs:
        body += ["<h2>The two named reference modules</h2>", table(refs)]
    body += ["<h2>Rule of thumb</h2><ul>"
             "<li>Landing, terrain following below ~10 m, obstacle stop: short-range ToF modules (high rate, a few grams).</li>"
             "<li>Altitude hold and terrain following at survey heights: 100-600 m LiDAR modules.</li>"
             "<li>Ranging to distant targets from a gimbal, or altitude above 600 m: long-range modules (1-10 Hz typical).</li>"
             "</ul>"]
    allrows = []
    for title, sub, f, key in classes:
        rows = sorted([r for r in RANGE_ROWS if f(r)], key=key)
        allrows += rows
        body += [f"<h2>{E(title)} ({len(rows)})</h2><p class=muted>{E(sub)}; weight limit as stated in the "
                 "rule, current products only.</p>", table(rows)]
    rel = "compare/tfmini-vs-sf11-vs-long-range/"
    page(rel, "TFmini vs SF11 vs long-range laser rangefinder modules for drones",
         "Three classes of drone rangefinders compared from an open dataset: short-range ToF (TFmini class), "
         "100-600 m LiDAR (SF11 class) and 1 km+ laser rangefinder modules, with weight, rate, interface and price.",
         "\n".join(body), [itemlist("Drone rangefinder modules by range class", allrows, SITE + rel),
                            crumbs([("Database", ""), ("TFmini vs SF11 vs long range", rel)])])


# ---------------------------------------------------------------- crawler files
def build_best():
    groups = [
        ("Lightweight modules with published weight", sorted(
            [r for r in RANGE_ROWS if r["category"] == "rangefinder module" and r.get("weight_g")],
            key=lambda r: (r["weight_g"], name(r)))[:5]),
        ("Modules with linked open-source drivers", sorted(
            [r for r in RANGE_ROWS if r["category"] == "rangefinder module" and has_driver(r)],
            key=name)[:5]),
    ]
    body = [nav(), "<h1>Best laser rangefinder modules by application</h1>",
            "<p>Best depends on the integration: these transparent dataset filters are a shortlist, "
            "not hands-on reviews or a universal ranking. Compare target conditions before selecting; "
            "no customer reviews or procurement demand are implied.</p>"]
    for heading, rows in groups:
        body += [f"<h2>{heading}</h2>", table(rows, full_conditions=True)]
    page("guides/best-laser-rangefinder-modules/", "Best laser rangefinder modules by application",
         "Manufacturer-sourced shortlists for lightweight integration and linked open-source drivers, "
         "with published range conditions and sources.", "\n".join(body), [])


def build_crawler_files():
    urls = [SITE + p for p, _, _ in PAGES]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"<url><loc>{E(SITE + p)}</loc><lastmod>{PAGE_DATES[p]}</lastmod></url>" for p, _, _ in PAGES]
    sm += [f"<url><loc>{SITE}data/modules.csv</loc><lastmod>{source_modified("data/modules.json")}</lastmod></url>",
           f"<url><loc>{SITE}data/modules.json</loc><lastmod>{source_modified("data/modules.json")}</lastmod></url>", "</urlset>"]
    write("docs/sitemap.xml", "\n".join(sm) + "\n")
    write("docs/robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n")
    makers = ", ".join(b for b, _ in brand_counts())
    ll = [f"# Laser rangefinder module database", "",
          f"> Open, manufacturer-sourced dataset of {N_MOD} single-point laser rangefinder / LiDAR distance modules "
          f"({EXTRA}; data date {DATE}): wavelength, range with target condition, accuracy, rate, interface, weight, public "
          "price, open-source drivers, source URL and capture date for each row. MIT licence. Maintained by ERDI TECH "
          "LTD (erdilrf.com), which also makes some listed modules; rows for every maker follow the same rules.", "",
          f"Manufacturers: {makers}.", "",
          "## Data", "",
          f"- [modules.csv]({SITE}data/modules.csv): all rows, one module per line",
          f"- [modules.json]({SITE}data/modules.json): same data as JSON",
          f"- [schema.json]({SITE}data/schema.json): field definitions and units",
          f"- [GitHub repository]({REPO}): source, history, validation tests", "", "## Pages", ""]
    ll += [f"- [{t}]({SITE + p}): {d}" for p, t, d in PAGES]
    write("docs/llms.txt", "\n".join(ll) + "\n")


def main():
    write("data/modules.csv", csv_text())
    write("MODULES.md", build_md())
    update_readme()
    # clean generated directories
    for d in ("alternatives", "guides", "compare"):  # generated only
        shutil.rmtree(os.path.join(DOCS, d), ignore_errors=True)
    build_index()
    build_alternatives()
    build_guides()
    build_best()
    build_wavelength()
    build_drone_classes()
    os.makedirs(os.path.join(DOCS, "data"), exist_ok=True)
    for f in ("modules.json", "modules.csv", "schema.json"):
        shutil.copyfile(os.path.join(ROOT, "data", f), os.path.join(DOCS, "data", f))
    build_crawler_files()
    write("docs/.nojekyll", "")
    print(f"built {len(ROWS)} rows, {len(PAGES)} pages")


if __name__ == "__main__":
    main()
