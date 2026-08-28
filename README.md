# Holiday Hill Marina — boat listing page

**Live at:** https://modus.github.io/hhm-boats/

The page rebuilds itself from Airtable. Edit a boat in Airtable and the site
follows on its own — there is nothing to upload by hand any more.

---

## How it works

```
Airtable  ──►  build.py  ──►  index.html  ──►  GitHub Pages
(the data)     (nightly)      (committed)      (the live site)
```

| File | What it is |
|---|---|
| `build.py` | Reads the vessels from Airtable and writes `index.html` |
| `template.html` | The page shell — layout, styling, wording round the edges |
| `img/` | One photograph per boat, named by slip (`1-6.jpg`, `DT-29.jpg`) |
| `index.html` | Generated. **Do not edit by hand — the next build overwrites it** |
| `tests/` | Offline checks that run before every build |
| `.github/workflows/build.yml` | The schedule and the commit step |

**Airtable is the only place to change wording.** The page is a view of the
`Charity Description`, `Boat Make/Model/Year/LOA`, `Title Route` and `Listing`
fields on the vessel table, filtered to `Charity List = On list`.

**Do not hand-upload `index.html` any more.** It used to be the way this site
was updated. It is now generated, so a file uploaded by hand survives only
until the next build overwrites it. Edit the boat in Airtable instead.

---

## One-time setup

**1. Make an Airtable token**

At https://airtable.com/create/tokens create a personal access token:

- Scope: **`data.records:read`** only. It never needs write access.
- Access: the **HHM Active Customers** base only.
- Copy the token — Airtable shows it once.

**2. Put it in the repo secrets**

Settings → Secrets and variables → Actions → **New repository secret**

- Name: `AIRTABLE_TOKEN`
- Value: the token

GitHub encrypts it. It is not visible in logs, in the code, or to anyone
reading the repo.

**3. Run it once by hand**

Actions tab → **Rebuild listing from Airtable** → **Run workflow**.

---

## Day to day

Nothing. It runs at 11:00 UTC (about 7am Maryland) every day.

**To publish an Airtable change immediately:** Actions → Rebuild listing from
Airtable → Run workflow. Live about a minute later.

**A run only commits when the page actually changed.** If no boat moved, no
commit appears — quiet weeks leave no trace in the history.

---

## Two things worth knowing

**The "Prepared" date only advances when content changes.** It is not the date
the job last ran. That is deliberate: a nightly cron stamping a fresh date
would commit a new page every day and tell the reader nothing.

**Photographs are not automated.** Every crop was framed by eye — whole hull in
shot, transom name legible. A build cannot redo that. To change a photo, replace
the file in `img/` keeping the slip name, and commit. A boat with no matching
file still gets a card, with a placeholder where the photo goes, and the build
log says which one is missing.

---

## Suppressing an unverified make or model

Some records hold a make or model that came from paperwork and has never been
confirmed. Slip 1-16 is filed as a **Morgan 29** — but Morgan never built a 29,
so that must not appear on a page prospective owners read.

Tick **Hide Make/Model on page** on the record. Airtable keeps what it was told;
the page stays silent until the hull is identified.

Without that field the build would faithfully republish the false claim, which
is exactly what automation does if you let it.

---

## If a run fails

Actions tab → click the red run → read the step that failed.

| Message | Cause |
|---|---|
| `AIRTABLE_TOKEN is not set` | The secret is missing or misnamed |
| `Airtable returned 401` | Token revoked, expired, or lacks access to the base |
| `Airtable returned 403` | Token is missing the `data.records:read` scope |
| `Refusing to publish an empty page` | The Airtable filter matched nothing. **This is a guard, not a bug** — it stops a filter change wiping the live page |
| a `tests/test_build.py` check | Something upstream changed shape; the diagnostics name it |

Nothing is published when a run fails. The live page keeps serving the last
good version.

## Testing a change without a token

```
python3 tests/test_build.py
```

Runs against a captured Airtable response in `tests/fixture.json`. No network,
no token. Refresh that snapshot with:

```
AIRTABLE_TOKEN=pat... python3 tests/make_fixture.py
```

---

## Custom domain, if you ever want one

1. In GoDaddy DNS add a CNAME: name `boats`, value `modus.github.io`
2. Settings → Pages → Custom domain → `boats.holidayhillmarina.com` → Save

GitHub writes the `CNAME` file and issues the certificate. Tick **Enforce
HTTPS** once the check goes green.
