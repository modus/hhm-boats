# Holiday Hill Marina — Vessels Offered for Donation

A single self-contained page listing the vessels HHM is offering to a charity partner.
All photographs are embedded in `index.html`; there are no other assets.

## Publishing

1. Push this folder to a GitHub repository.
2. Settings → Pages → Source: *Deploy from a branch* → `main` / `/ (root)`.
3. The page appears at `https://<username>.github.io/<repo>/` within a minute or two.

### Custom domain (optional)

Add a file named `CNAME` containing one line, e.g. `boats.holidayhillmarina.com`,
then create a CNAME DNS record pointing that subdomain at `<username>.github.io`.

## Updating

`index.html` is a snapshot. To refresh it, regenerate the page and replace this file,
then commit and push. GitHub Pages redeploys automatically.

## Note

The page carries `<meta name="robots" content="noindex,nofollow">` so search engines
should not index it. That is a request, not enforcement — a public repository and a
public Pages site are reachable by anyone who has, or guesses, the URL.
