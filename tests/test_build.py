#!/usr/bin/env python3
"""Offline checks on the page generator. No token, no network.

    python3 tests/test_build.py

Feeds build.py a captured Airtable response (tests/fixture.json) and asserts
the things that would actually hurt if they broke.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build  # noqa: E402

fixture = json.loads((HERE / "fixture.json").read_text())
build.fetch_records = lambda token: fixture

fails = []


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        fails.append(name)


boats = [build.boat(r) for r in fixture]
boats.sort(key=lambda b: (not b["held"], b["code"]))
by = {b["code"]: b for b in boats}

check("22 vessels parsed", len(boats) == 22, f"got {len(boats)}")
check("every vessel has a slip code", all(b["code"] for b in boats))
check("every vessel has a title", all(b["title"] for b in boats))
check("every vessel has a description", all(b["desc"] for b in boats))

held = [b["code"] for b in boats if b["held"]]
check("5 hold title", len(held) == 5, f"got {held}")
check("the right 5 hold title",
      set(held) == {"1-7", "1-17", "1-27", "2-3", "DT-29"}, str(sorted(held)))
check("title-in-hand sort first",
      all(b["held"] for b in boats[:5]) and not any(b["held"] for b in boats[5:]))

ashore = {b["code"] for b in boats if b["ashore"]}
check("6 in dry storage", len(ashore) == 6, str(sorted(ashore)))
check("dry storage set is right",
      ashore == {"CDS-22", "DT-2", "DT-17", "DT-29", "DT-34", "DT-44"}, str(sorted(ashore)))
check("bulkhead counts as a wet slip", not by["B-3"]["ashore"])

# the reason the suppression field exists
check("1-16 make suppressed", by["1-16"]["make"] == "", repr(by["1-16"]["make"]))
check("1-16 model suppressed", by["1-16"]["model"] == "", repr(by["1-16"]["model"]))
check("suppression is targeted, not global", by["1-6"]["make"] == "Catalina")

# house style the charity page is held to
alldesc = " ".join(b["desc"] for b in boats)
check("no em dashes in any description", "—" not in alldesc)
check("no condition language", not re.search(r"\b(derelict|sunk|rotten|debris|abandoned)\b",
                                             alldesc, re.I))
check("no collection-timing note on 2-3", "autumn" not in by["2-3"]["desc"].lower())
check("2-3 carries no unconfirmed name", "4.fun" not in by["2-3"]["title"])

# photographs
missing = [b["code"] for b in boats if not (HERE.parent / "img" / f"{b['code']}.jpg").exists()]
check("every vessel has a photo file", not missing, str(missing))

# rendering
cards = "\n".join(build.card(b) for b in boats)
check("22 cards rendered", cards.count('<article class="card"') == 22)
check("no placeholder cards", 'class="cover ph"' not in cards)
check("5 title-in-hand badges", cards.count("title-yes") == 5)
check("17 title-in-progress badges", cards.count("title-no") == 17)
check("images referenced by path, not embedded", "base64" not in cards)

tmpl = (HERE.parent / "template.html").read_text()
for ph in ("{{CARDS}}", "{{TALLY}}", "{{N_TOTAL_WORD}}", "{{N_HELD_WORD}}", "{{N_PENDING_WORD}}"):
    check(f"template has {ph}", ph in tmpl)
check("template carries no embedded images", "base64" not in tmpl)

# nothing private may reach the page
page = tmpl.replace("{{CARDS}}", cards)
visible = " ".join(re.findall(r">([^<>]+)<", page))
for surname in ("Simpkins", "Galleher", "Perez", "Lewis", "Catalanotto", "Morrison",
                "Davis", "Sorrels", "Minniefield", "Coan", "Harrington", "Benitez",
                "McElroy", "Cortes"):
    check(f"no customer surname: {surname}", surname.lower() not in visible.lower())
check("no HIN on the page", not re.search(r"\b[A-Z]{3}[A-Z0-9]{8,9}\b", visible))
check("no dollar figures", "$" not in visible)

print()
if fails:
    print(f"{len(fails)} FAILED: {', '.join(fails)}")
    sys.exit(1)
print("all checks passed")
