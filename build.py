#!/usr/bin/env python3
"""Build index.html for the Holiday Hill Marina vessel listing.

Reads the vessel records straight from Airtable, so Airtable is the single
source of truth. Photographs are NOT fetched — they live in img/ as files
committed to this repo, keyed by slip code (img/1-6.jpg, img/DT-29.jpg …).
Cropping was done by eye and is not something a build should redo.

Usage:
    AIRTABLE_TOKEN=pat... python3 build.py            # writes index.html
    AIRTABLE_TOKEN=pat... python3 build.py --check    # print, write nothing
"""

import datetime
import html
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_ID = "appW80oInUny6dWAP"
TABLE_ID = "tbl2PULvbkXQnuZyS"
ON_LIST = "On list"
HELD = "HHM holds title"

# Airtable field IDs. Names can be renamed in the UI; IDs cannot.
F = {
    "listing":   "fld2QWFXHF2MkTTBs",   # formula: "Pier 1 Slip 6 · ASTARA"
    "desc":      "fldJfEmi5LjfjNfaz",   # Charity Description
    "make":      "fldczIeyA5IEDbsNS",
    "model":     "fldjsncF7H9TFiyJi",
    "year":      "fldenaK3W6hUbAPCV",
    "loa":       "fld6R1JkNfxI0N9gL",
    "route":     "fldMAWM8vWi4NwMP2",   # Title Route
    "list":      "flddkcXzvMkp36cCt",   # Charity List
    "slip":      "fldQnyO9q13CacRtn",   # Pier_Slip
    "dry":       "fldjAwnSwBes2E6vM",   # Dry Storage Location
    "hide_mm":   "fldfj0zCmQQtzwQy1",   # Hide Make/Model on page
}

ROOT = pathlib.Path(__file__).parent
WORDS = ("zero one two three four five six seven eight nine ten eleven twelve "
         "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty").split()
TENS = {30: "thirty", 40: "forty", 50: "fifty"}


def word(n):
    """Small number to words: 5 -> 'five', 22 -> 'twenty-two'."""
    if n < len(WORDS):
        return WORDS[n]
    for base in (50, 40, 30, 20):
        if n >= base:
            rest = n - base
            stem = TENS.get(base, "twenty")
            return stem if rest == 0 else f"{stem}-{WORDS[rest]}"
    return str(n)


def sel(v):
    """singleSelect comes back as an object; take its name."""
    return v.get("name", "") if isinstance(v, dict) else (v or "")


def fetch_records(token):
    """Every vessel row, following pagination.

    Only the handful of fields the page needs are requested — no attachments,
    no owner details, nothing private leaves Airtable. Filtering to the charity
    list happens in Python rather than in a filterByFormula: formulas want field
    NAMES, which anyone can rename in the Airtable UI, and a renamed field would
    silently return zero rows. Field IDs are stable, so we filter on those here.
    """
    wanted = list(F.values())
    out, offset = [], None
    while True:
        params = [("pageSize", "100")] + [("fields[]", fid) for fid in wanted]
        if offset:
            params.append(("offset", offset))
        url = (f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
               f"?{urllib.parse.urlencode(params)}&returnFieldsByFieldId=true")
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:400]
            hint = ""
            if e.code in (401, 403):
                hint = (
                    "\n\nThis is almost always the token rather than the code. Check at"
                    "\n  https://airtable.com/create/tokens"
                    "\n  1. the token has the HHM Active Customers base under Access"
                    "\n     (a new token starts with NO bases attached)"
                    "\n  2. the token has the data.records:read scope"
                    "\n  3. the secret in GitHub is named exactly AIRTABLE_TOKEN"
                    "\n     and holds the token value, not the token's name or ID"
                )
            sys.exit(f"Airtable returned {e.code}: {body}{hint}")
        out += data.get("records", [])
        offset = data.get("offset")
        if not offset:
            break

    keep = [r for r in out if sel(r.get("fields", {}).get(F["list"])) == ON_LIST]
    print(f"Airtable: {len(out)} rows read, {len(keep)} on the charity list")
    return keep


def sort_key(code):
    """'1-6' -> (0, 1, 6); 'B-3' -> (1, 0, 3); 'DT-29' -> (2, 'DT', 29).

    Piers first in numeric order, then the bulkhead, then dry storage.
    """
    prefix, _, num = code.partition("-")
    n = int(num) if num.isdigit() else 0
    if prefix.isdigit():
        return (0, int(prefix), n, code)
    if prefix == "B":
        return (1, 0, n, code)
    return (2, prefix, n, code)


def slip_code(f):
    """Key used for the photo filename: '1-6', 'DT-29', 'B-3'."""
    return (f.get(F["slip"]) or f.get(F["dry"]) or "").strip()


def curly(text):
    """Straight quotes around a boat name become typographic ones.

    Airtable holds "IVY" because that is what a keyboard types; the page
    should read “IVY”. Only paired double quotes are touched — single
    quotes are left alone so foot and inch marks (27' 0") survive.
    """
    import re as _re
    return _re.sub(r'"([^"]*)"', lambda m: "\u201c" + m.group(1) + "\u201d", text)


def boat(rec):
    f = rec.get("fields", {})
    code = slip_code(f)
    listing = (f.get(F["listing"]) or "").strip()
    hide = bool(f.get(F["hide_mm"]))
    return {
        "code": code,
        "title": listing,
        "desc": curly((f.get(F["desc"]) or "").strip()),
        "make": "" if hide else (f.get(F["make"]) or "").strip(),
        "model": "" if hide else str(f.get(F["model"]) or "").strip(),
        "year": str(f.get(F["year"]) or "").strip(),
        "loa": (f.get(F["loa"]) or "").strip(),
        "held": sel(f.get(F["route"])) == HELD,
        # location badge follows the listing prefix, which is how the page reads
        "ashore": listing.lower().startswith("dry storage"),
    }


def card(b):
    img = ROOT / "img" / f"{b['code']}.jpg"
    if img.exists():
        cover = (f'<div class="cover"><img src="img/{b["code"]}.jpg" '
                 f'alt="{html.escape(b["title"])}" loading="lazy"></div>')
    else:
        cover = ('<div class="cover ph"><div><span class="phi">photo on file</span>'
                 '<span class="phs">not rendered in this preview</span></div></div>')
    rows = []
    for label, val in (("Boat Make", b["make"]), ("Boat Model", b["model"]),
                       ("Boat Year", b["year"]), ("Boat LOA", b["loa"])):
        if val:
            rows.append(f'<div class="f"><span class="k">{label}</span>'
                        f'<span class="v">{html.escape(val)}</span></div>')
    tags = ('<span class="loc ashore">Dry storage</span>' if b["ashore"]
            else '<span class="loc afloat">Wet slip</span>')
    tags += ('<span class="loc title-yes">Title in hand</span>' if b["held"]
             else '<span class="loc title-no">Title in progress</span>')
    return (f'<article class="card" data-slip="{html.escape(b["code"])}">'
            f'{cover}<div class="pad"><h3>{html.escape(b["title"])}</h3>'
            f'<div class="tags">{tags}</div>'
            f'<p class="desc">{html.escape(b["desc"])}</p>{"".join(rows)}</div></article>')


def main():
    token = os.environ.get("AIRTABLE_TOKEN")
    if not token:
        sys.exit("AIRTABLE_TOKEN is not set. In Actions this comes from repo secrets.")

    boats = [boat(r) for r in fetch_records(token)]
    boats = [b for b in boats if b["title"]]
    if not boats:
        sys.exit("Airtable returned no vessels. Refusing to publish an empty page.")

    missing = [b["code"] for b in boats if not (ROOT / "img" / f"{b['code']}.jpg").exists()]

    # title-in-hand first, then in walking order down the property.
    # Plain string sort would put 1-10 ahead of 1-6, so split the code
    # into its letter/number parts: piers by number, then the bulkhead,
    # then dry storage.
    boats.sort(key=lambda b: (not b["held"], sort_key(b["code"])))

    held = sum(1 for b in boats if b["held"])
    ashore = sum(1 for b in boats if b["ashore"])
    afloat = len(boats) - ashore
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%-d %B %Y")

    tally = (f"{len(boats)} vessels<br>{afloat} in wet slips &middot; {ashore} in dry storage"
             f"<br>{held} with title in hand<br>Prepared {stamp}")

    page = (ROOT / "template.html").read_text()
    for k, v in (("{{CARDS}}", "\n".join(card(b) for b in boats)),
                 ("{{TALLY}}", tally),
                 ("{{N_TOTAL_WORD}}", word(len(boats)).capitalize()),
                 ("{{N_HELD_WORD}}", word(held)),
                 ("{{N_PENDING_WORD}}", word(len(boats) - held))):
        if k not in page:
            sys.exit(f"template.html is missing {k}")
        page = page.replace(k, v)

    doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
           '<meta name="robots" content="noindex,nofollow">\n'
           '<meta name="description" content="Vessels available at Holiday Hill Marina, '
           'Rhode River, Mayo MD.">\n' + page + '\n</body>\n</html>\n')
    i = doc.index("</style>") + len("</style>")
    doc = doc[:i] + "\n</head>\n<body>" + doc[i:]

    print(f"{len(boats)} vessels | {held} title in hand | "
          f"{afloat} wet / {ashore} dry | {len(doc)/1024:.0f} KB")
    if missing:
        print(f"WARNING: no photo file for {', '.join(missing)} "
              f"- those cards fall back to a placeholder")

    # The "Prepared" date must not be the only thing that changes, or a nightly
    # cron would commit a new page every day for no reason. Compare against the
    # existing file with both dates normalised: if nothing else moved, leave the
    # file alone. The date then means "content last revised", not "job last ran".
    out = ROOT / "index.html"
    if out.exists():
        stamp_re = r"Prepared \d{1,2} [A-Za-z]+ \d{4}"
        import re as _re
        if _re.sub(stamp_re, "", out.read_text()) == _re.sub(stamp_re, "", doc):
            print("content unchanged - leaving index.html and its date as they are")
            return

    if "--check" in sys.argv:
        print("--check: content HAS changed, but nothing written")
        return
    out.write_text(doc)
    print("wrote index.html")


if __name__ == "__main__":
    main()
