---
name: provision-ga4
description: >-
  Create a GA4 property and web stream for a deployed Foundagent site. Use when
  the live site needs a measurement ID.
---

# Provision GA4 For A Site

Use this skill only after a site is live or has a stable public URL. It creates a
GA4 property under the account declared by `GA4_ACCOUNT_ID`, creates one web data
stream, and returns the `measurementId` that must be embedded in the site.

Do not try to create a GA4 account here. GA4 account creation requires a human to
accept Google's Terms of Service in Analytics UI. If `GA4_ACCOUNT_ID` is missing,
stop and report the manual prerequisite instead of starting an OAuth flow or
creating a different account.

## Inputs

Required:

- `SITE_URL`: canonical public URL, including `https://`
- `DISPLAY_NAME`: GA4 property display name, usually the hostname

Defaults:

- Service account key: `${GOOGLE_APPLICATION_CREDENTIALS:-/account/google-sa.json}`
- GA4 account id: `$GA4_ACCOUNT_ID`
- Time zone: `America/Los_Angeles`
- Currency: `USD`

The service account must be an Editor on the GA4 account. The account package is
mounted read-only at `/account`; do not write credentials back to it.

## Command

Run this from an agent container:

```sh
python3 - <<'PY'
import json
import os
import sys

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

site_url = os.environ.get("SITE_URL", "").strip()
display_name = os.environ.get("DISPLAY_NAME", "").strip()
account_id = os.environ.get("GA4_ACCOUNT_ID", "").strip()
key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "/account/google-sa.json")
time_zone = os.environ.get("GA4_TIME_ZONE", "America/Los_Angeles")
currency = os.environ.get("GA4_CURRENCY", "USD")

missing = [
    name
    for name, value in {
        "SITE_URL": site_url,
        "DISPLAY_NAME": display_name,
        "GA4_ACCOUNT_ID": account_id,
    }.items()
    if not value
]
if missing:
    raise SystemExit("missing required env: " + ", ".join(missing))
if not site_url.startswith("https://"):
    raise SystemExit("SITE_URL must be canonical and start with https://")
if not os.path.exists(key_path):
    raise SystemExit(f"service account key not found: {key_path}")

creds = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/analytics.edit"],
)
creds.refresh(Request())
headers = {
    "Authorization": f"Bearer {creds.token}",
    "Content-Type": "application/json",
}
base = "https://analyticsadmin.googleapis.com/v1beta"

prop_resp = requests.post(
    f"{base}/properties",
    headers=headers,
    json={
        "parent": f"accounts/{account_id}",
        "displayName": display_name,
        "timeZone": time_zone,
        "currencyCode": currency,
    },
    timeout=30,
)
prop_resp.raise_for_status()
prop = prop_resp.json()

stream_resp = requests.post(
    f"{base}/{prop['name']}/dataStreams",
    headers=headers,
    json={
        "type": "WEB_DATA_STREAM",
        "displayName": "web",
        "webStreamData": {"defaultUri": site_url},
    },
    timeout=30,
)
stream_resp.raise_for_status()
stream = stream_resp.json()

measurement_id = stream.get("webStreamData", {}).get("measurementId")
if not measurement_id:
    print(json.dumps(stream, indent=2, sort_keys=True), file=sys.stderr)
    raise SystemExit("GA4 data stream response did not include measurementId")

print("property=" + prop["name"])
print("data_stream=" + stream["name"])
print("measurement_id=" + measurement_id)
PY
```

Example:

```sh
export SITE_URL=https://example.foundagent.net
export DISPLAY_NAME=example.foundagent.net
# then run the Python command above
```

## After Provisioning

Embed the returned `measurement_id` in the site through the product's normal
analytics integration path. Do not create the property before the site has a real
URL; placeholder properties create cleanup work and do not validate tracking.

For `*.foundagent.net`, Search Console is already covered by the
`foundagent.net` Domain property. GA4 property creation is per site because each
site needs its own measurement ID and stream.
