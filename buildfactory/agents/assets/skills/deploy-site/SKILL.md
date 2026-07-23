---
name: deploy-site
description: >-
  Apply foundagent.net naming, deployment, domain, and DNS rules. Use when
  publishing a public site or changing its Foundagent domain.
---

# Deploying a site on the foundagent.net rail

`foundagent.net` is the fleet domain. This card carries the facts and hard
rules specific to this rail — the deploy tooling itself you already know.

## Facts

- Google Search Console has a verified Domain property
  `sc-domain:foundagent.net` covering the apex and ALL subdomains. A new
  `<product>.foundagent.net` needs zero Google-side action — do not add
  verification tokens or create new Search Console properties for it.
- Subdomains are self-service, and Cloudflare DNS IS the registry: query
  existing records first; if the name is free, creating the record claims it.
  There is no separate reservation step.
- Standard binding for a Vercel site: add the domain to the Vercel project,
  then create a DNS-only (not proxied) CNAME `<product>.foundagent.net` →
  `cname.vercel-dns.com`. TLS auto-issues. This exact path is proven in
  production (`glp1.foundagent.net`).
- Throwaway verification (e.g. an e2e check that DNS works) can use a TXT
  record instead of binding a real site.

## Norms

- A public-facing site gets a real product name. Name the Vercel project
  explicitly — deploying from a directory named `site` silently creates a
  project named `site` with URL `site-<team>.vercel.app`, and that name
  sticks for the life of the project. This has already happened once in this
  fleet; do not repeat it.
- Public-facing means bound: the site lives at `<product>.foundagent.net`,
  and every external reference — posts, READMEs, sitemaps, canonical URLs —
  uses only the custom domain. The `*.vercel.app` URL is internal preview
  only. A deploy URL that "works" is not a finished public site.
- When to bind: will anyone outside the fleet ever see this URL? Yes → name
  the project and bind the subdomain before referencing it anywhere. No
  (internal, throwaway, e2e) → do not bind; the vercel.app URL is fine, and
  binding would waste the motion and pollute the namespace.

## Prohibitions (hard rules)

- Never delete any `google-site-verification=` TXT record on the apex.
  Google periodically rechecks Domain property ownership; deleting it
  invalidates the Search Console property for the entire fleet.
- Never modify the apex A record or DNS records created by other agents,
  unless the goal explicitly requires a migration. Delete only records you
  created yourself.

## After the site is live

Analytics for a live public site (GA4 property + measurement ID) is covered
by the `provision-ga4` skill.
