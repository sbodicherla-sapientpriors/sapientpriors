# Letting /api/try authenticate to the product API

`/api/try` calls the demo API as the `playground-runtime` service account. It needs a
Google ID token, and the point of this setup is that **no long-lived key is stored
anywhere** — Vercel mints an OIDC token per invocation, Google trades it for an
impersonated ID token, and both expire on their own.

Values below are the real ones, read off the Vercel project's OIDC Federation panel on
2026-09-15. Nothing is a placeholder.

| | |
| --- | --- |
| Vercel team slug | `raveeshu-pahujas-projects` |
| Vercel project | `sapientpriors` |
| Issuer mode | **Team** |
| `iss` | `https://oidc.vercel.com/raveeshu-pahujas-projects` |
| `aud` | `https://vercel.com/raveeshu-pahujas-projects` |
| `sub` (production) | `owner:raveeshu-pahujas-projects:project:sapientpriors:environment:production` |

Make sure that panel is **Saved** with Team selected. Switching it to Global later
changes `iss` and silently breaks the provider below.

## Status: done on the GCP side

Applied to `adaptive-agent-sp` on 2026-09-15. Pool `vercel` and provider `vercel-oidc` are
ACTIVE, and `playground-runtime@` carries `roles/iam.workloadIdentityUser` for both the
**production** and **preview** subjects of the `sapientpriors` Vercel project. Preview is
bound so a PR deployment can be tested end to end; it spends the same credits as production
against the same agent, and revoking it is the same command with `--remove-iam-policy-binding`.

**What is left is the four environment variables in section 2.** Until they are set,
`/api/try` answers 503 and the pane reports that it is not connected.

Section 1 is kept as the record of what was applied, and to rebuild it in another project.

## Who can run this

Needs `roles/iam.workloadIdentityPoolAdmin` and `roles/iam.serviceAccountAdmin` on
`adaptive-agent-sp`. Project `editor` is **not** enough: `iam.workloadIdentityPools.create`
is not in it.

## 1. Pool, provider, and the impersonation grant

```sh
PROJECT=adaptive-agent-sp
PROJECT_NUMBER=176844439652
TEAM=raveeshu-pahujas-projects
SA=playground-runtime@adaptive-agent-sp.iam.gserviceaccount.com
SUBJECT="owner:$TEAM:project:sapientpriors:environment:production"

gcloud iam workload-identity-pools create vercel \
  --location=global --project="$PROJECT" --display-name="Vercel"

# Mapped on `sub` alone, and the condition matches a prefix of it. Vercel's token does
# carry owner/project/environment as separate claims, but the panel only shows the seven
# standard ones, so nothing here depends on a claim that has not been seen.
gcloud iam workload-identity-pools providers create-oidc vercel-oidc \
  --location=global --project="$PROJECT" \
  --workload-identity-pool=vercel \
  --issuer-uri="https://oidc.vercel.com/$TEAM" \
  --allowed-audiences="https://vercel.com/$TEAM" \
  --attribute-mapping="google.subject=assertion.sub" \
  --attribute-condition="assertion.sub.startsWith('owner:$TEAM:project:sapientpriors:')"

# Exact subject, not a wildcard: only the production deployment of this one Vercel
# project may become the service account. A preview deployment has a different `sub`
# and is refused, which is deliberate — previews would otherwise spend the playground's
# credits and write into the live agent's threads.
gcloud iam service-accounts add-iam-policy-binding "$SA" \
  --project="$PROJECT" \
  --role=roles/iam.workloadIdentityUser \
  --member="principal://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/vercel/subject/$SUBJECT"
```

To let preview deployments work too, repeat the last command with
`environment:preview` in `$SUBJECT`.

## 2. Vercel environment variables

```
GCP_WORKLOAD_IDENTITY_PROVIDER = //iam.googleapis.com/projects/176844439652/locations/global/workloadIdentityPools/vercel/providers/vercel-oidc
GCP_SERVICE_ACCOUNT_EMAIL      = playground-runtime@adaptive-agent-sp.iam.gserviceaccount.com
PRODUCT_API_BASE_URL           = https://adaptive-agent-web-demo-2fjhwkpjsa-uc.a.run.app
PLAYGROUND_AGENT_ID            = agent_01M2JVH3FD5651QY3TXMFYAMZ5
```

`PRODUCT_API_BASE_URL` is also the ID token audience, and the server checks it against
its own `SERVICE_TOKEN_AUDIENCE`. Use the `...-2fjhwkpjsa-uc.a.run.app` form exactly;
the `...-176844439652.us-central1.run.app` alias serves the same service but is a
different audience string and the token will be rejected.

The rival Opus/Haiku panes additionally need `ANTHROPIC_API_KEY` and
`ANTHROPIC_MANUAL_FILE_ID` (see `upload-manual.mjs`). They are switched off in
`try-demo.js` right now, so the page works without either.

## 3. Checking it

The server already trusts this account: `AUTH_SERVICE_EMAILS` lists
`playground-runtime@…` and `AUTH_SERVICE_ORGANIZATIONS` maps it to
`org_playground_demo`, so nothing on the product side has to change.

Locally, without any of the above, `/api/try` falls back to Application Default
Credentials impersonating the same account:

```sh
gcloud auth application-default login \
  --impersonate-service-account=playground-runtime@adaptive-agent-sp.iam.gserviceaccount.com
```

That path is guarded on `GCP_WORKLOAD_IDENTITY_PROVIDER` being unset, so it can never
win on Vercel.
