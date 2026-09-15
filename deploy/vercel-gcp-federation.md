# Letting /api/try authenticate to the product API

`/api/try` calls the demo API as the `playground-runtime` service account. It needs a
Google ID token, and the point of this setup is that **no long-lived key is stored
anywhere** — Vercel mints an OIDC token per invocation, Google trades it for an
impersonated ID token, and both expire on their own.

Needs an account with `roles/iam.workloadIdentityPoolAdmin` and
`roles/iam.serviceAccountAdmin` on `adaptive-agent-sp`. Project `editor` is **not**
enough — `iam.workloadIdentityPools.create` is not in it.

## 0. Turn OIDC on in Vercel first

Vercel project → Settings → Security → **OIDC Federation**. Note which **issuer mode**
it is in, because the two produce different issuer URLs and a mismatch fails as an
opaque `invalid_grant`:

| Issuer mode | `--issuer-uri`                      | `--allowed-audiences`            |
| ----------- | ----------------------------------- | -------------------------------- |
| Team        | `https://oidc.vercel.com/<TEAM>`    | `https://vercel.com/<TEAM>`      |
| Global      | `https://oidc.vercel.com`           | `https://vercel.com/<TEAM>`      |

`<TEAM>` is the Vercel team slug, the same one in the dashboard URL.

## 1. Pool, provider, and the impersonation grant

```sh
TEAM=<vercel-team-slug>            # <- the one thing you have to fill in
PROJECT=adaptive-agent-sp
PROJECT_NUMBER=176844439652
SA=playground-runtime@adaptive-agent-sp.iam.gserviceaccount.com

gcloud iam workload-identity-pools create vercel \
  --location=global --project="$PROJECT" --display-name="Vercel"

# attribute.owner is what the grant below is scoped to, and the condition is what stops
# any other Vercel team's token from being accepted by this provider at all.
gcloud iam workload-identity-pools providers create-oidc vercel-oidc \
  --location=global --project="$PROJECT" \
  --workload-identity-pool=vercel \
  --issuer-uri="https://oidc.vercel.com/$TEAM" \
  --allowed-audiences="https://vercel.com/$TEAM" \
  --attribute-mapping="google.subject=assertion.sub,attribute.owner=assertion.owner,attribute.project=assertion.project_id,attribute.environment=assertion.environment" \
  --attribute-condition="assertion.owner == '$TEAM'"

# Scoped to the team, not to a single deployment: preview URLs get their own subjects,
# and pinning the grant to one would break every preview build.
gcloud iam service-accounts add-iam-policy-binding "$SA" \
  --project="$PROJECT" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/vercel/attribute.owner/$TEAM"
```

To narrow it further later, map on `attribute.project` and grant
`.../attribute.project/<vercel-project-id>` instead.

## 2. Vercel environment variables

```
GCP_WORKLOAD_IDENTITY_PROVIDER = //iam.googleapis.com/projects/176844439652/locations/global/workloadIdentityPools/vercel/providers/vercel-oidc
GCP_SERVICE_ACCOUNT_EMAIL      = playground-runtime@adaptive-agent-sp.iam.gserviceaccount.com
PRODUCT_API_BASE_URL           = https://adaptive-agent-web-demo-2fjhwkpjsa-uc.a.run.app
PLAYGROUND_AGENT_ID            = agent_01M2JQ1HXDAFSHBF2B69VTMP8C
```

`PRODUCT_API_BASE_URL` is also the ID token audience, and the server checks it against
its own `SERVICE_TOKEN_AUDIENCE`. Use the `...-2fjhwkpjsa-uc.a.run.app` form exactly;
the `...-176844439652.us-central1.run.app` alias serves the same service but is a
different audience string and the token will be rejected.

The rival panes additionally need `ANTHROPIC_API_KEY` and `ANTHROPIC_MANUAL_FILE_ID`
(see `upload-manual.mjs`). They are switched off in `try-demo.js` right now, so the page
works without either.

## 3. Checking it

The server already trusts this account:
`AUTH_SERVICE_EMAILS` lists `playground-runtime@…` and `AUTH_SERVICE_ORGANIZATIONS`
maps it to `org_playground_demo`, so nothing on the product side has to change.

Locally, without any of the above, `/api/try` falls back to Application Default
Credentials impersonating the same account:

```sh
gcloud auth application-default login \
  --impersonate-service-account=playground-runtime@adaptive-agent-sp.iam.gserviceaccount.com
```

That path is guarded on `GCP_WORKLOAD_IDENTITY_PROVIDER` being unset, so it can never
win on Vercel.
