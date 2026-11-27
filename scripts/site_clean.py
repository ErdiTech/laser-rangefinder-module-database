"""Display-only cleanup for spec cells on erditech.com (the CSV/JSON keep the full provenance text).

Removes bracketed editor notes such as "(page prints '...', operator missing)" or
"(SPD1200N0 controlled source technical table; ...)" and stray footnote markers like "¹)".
"""
import re

_NOTE = re.compile(r"\s*\((?=[^()]*(?:page prints|operator missing|controlled source|source row|not inferred|inferred|copied from))[^()]*\)", re.I)
_PRINTS = re.compile(r"\s*\(page prints .*?operator missing\)", re.I)
_CLAUSE = re.compile(r"[;,]?\s*no additional [a-z ]*inferred", re.I)
_FOOT = re.compile(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]+\)?")
_SPACE = re.compile(r"\s{2,}")


def clean(t):
    if not t:
        return t
    s = _PRINTS.sub("", t)
    s = _NOTE.sub("", s)
    s = _CLAUSE.sub("", s)
    s = _FOOT.sub("", s)
    s = _SPACE.sub(" ", s).strip(" ;,")
    return s or t
