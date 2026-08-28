#!/usr/bin/env python3
"""Capture a live Airtable response as tests/fixture.json.

Run once with a token to refresh the fixture:
    AIRTABLE_TOKEN=pat... python3 tests/make_fixture.py
The fixture lets test_build.py exercise the generator with no network and no token.
"""
import json, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import build

token = os.environ.get("AIRTABLE_TOKEN") or sys.exit("AIRTABLE_TOKEN not set")
recs = build.fetch_records(token)
out = pathlib.Path(__file__).parent / "fixture.json"
out.write_text(json.dumps(recs, indent=1, ensure_ascii=False))
print(f"wrote {out} with {len(recs)} records")
