# This folder is a drop box, nothing more

Files Claude puts here are ready to upload to GitHub:

> https://github.com/modus/hhm-boats/upload/main

Drag the file in, scroll down, click the green **Commit changes**. Same
filename replaces the old version — no prompt, no conflict.

---

## Do not hand-upload index.html any more

The site rebuilds itself from Airtable now. `index.html` is generated. If you
upload one by hand, the next build overwrites it and your change vanishes.

**To change the wording on a boat, edit the boat in Airtable.** That is the
only place content lives.

To publish an Airtable change immediately instead of waiting for the overnight
run: Actions → *Rebuild listing from Airtable* → **Run workflow**.

The full runbook lives on the repo front page at
https://github.com/modus/hhm-boats
