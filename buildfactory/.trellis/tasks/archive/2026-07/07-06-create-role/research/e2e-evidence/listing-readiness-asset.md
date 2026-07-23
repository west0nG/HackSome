# Marketplace Listing Readiness — Gumroad

_Checked: 2026-07-06, live from the operator browser._

## TL;DR
Gumroad is up and reachable, but there is **no logged-in seller session**. We
cannot publish a listing yet. A human must give us account access (and clear any
login gate I cannot automate), and Gumroad will require payout/identity
onboarding before a product can actually sell.

## 1. Is the seller dashboard reachable right now?
**Yes.** Navigating to `https://app.gumroad.com/dashboard` returned a working
Gumroad page (real HTTP response, not a DNS/network/timeout error). The service
is up and reachable from this browser.

## 2. Does any logged-in session exist?
**No.** The dashboard URL redirected to
`https://gumroad.com/login?next=%2Fdashboard` — the unauthenticated log-in
screen. There is no authenticated seller cookie/session in this browser.

I did **not** attempt to log in: I hold no credentials, and I do not create
accounts, enter credentials, or accept platform terms on my own.

Log-in options the page offers: **Google, X, and Stripe** OAuth; **email +
password**; and **passkey**.

## 3. What a human must still provide before a first listing can be published

**Blocking — needed just to reach the dashboard:**
1. **A Gumroad seller account we control.** If one already exists, provide the
   login method: email + password, or authorization via one of the OAuth
   options (Google / X / Stripe). If none exists, a human must create it — I do
   not create accounts.
2. **Completion of any interactive login gate I cannot clear headlessly:** OAuth
   consent screens, a passkey prompt, and/or 2FA / email-verification codes.

**Very likely required before a product can be sold/published:**
3. **Seller onboarding Gumroad enforces before payouts:** a payout destination
   (bank account or PayPal) and identity/tax details (name, address, tax ID /
   SSN or business info). This is human-owned PII I cannot supply.

**Per-listing (arrives with each goal, not a standing blocker):**
4. The finished **product artifact** to upload, plus listing details — title,
   description, price, cover image.

## What I can do once items 1–2 are in place
Drive the browser through Gumroad's product-creation flow, upload the artifact,
set price/description, publish, then verify the listing opens **logged-out** and
record the public URL under `/company/assets`.
