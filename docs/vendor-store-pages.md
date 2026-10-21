# Synthetic vendor store on GitHub Pages

The manual `Publish synthetic vendor store` workflow prepares the entire static
store from reviewed GitHub Release wheels. No vendor access, SDK checkout, extra
PAT, package installation or wheel execution occurs. It does not run on push,
tag, release or schedule. This implementation has not deployed a site.

## GitHub setup and first publication

1. Push reviewed workflow/source changes only under separate publication approval.
   Require green catalog CI and a successful reviewed release containing the
   standalone synthetic wheel.
2. In this repository's **Settings → Pages → Build and deployment**, set
   **Source: GitHub Actions** and enable **Enforce HTTPS** if offered. Private repositories need a GitHub plan supporting
   Pages (for example GitHub Pro); do not make the repository public merely to
   enable hosting. The resulting public site exposes the selected proprietary
   synthetic wheel and public metadata; repository visibility does not make the
   site private. Confirm permission to distribute those files publicly first.
3. Allow the pinned GitHub-owned checkout/upload/deploy actions if organization
   policy restricts actions. The workflow grants its build job `contents: read`
   and its deployment job `pages: write` / `id-token: write`. It requires no new
   secret or broad default write permission. Keep the `github-pages` environment
   restricted to `main`; required reviewers may be configured there.
4. Review `.github/vendor-store.json`. Its initial `v0.5.0.dev2` tag is a **local
   release candidate**, with an exact locally verified synthetic-wheel digest;
   release existence and asset bytes on GitHub have not been checked here.
   If that release has not succeeded, publish the reviewed release first or
   deliberately select another successful release with the same reviewed bytes.
   Missing assets and digest mismatches stop the build before deployment.
5. In **Actions → Publish synthetic vendor store → Run workflow**, select `main`,
   enter revision `1` for the first publication, and validity `90` days (1–90).
   Subsequent publications and retries after successful deployment require a
   strictly greater revision. The operator owns this monotonic counter.
6. Review the run summary's exact index SHA-256, expiry and final site URL. After
   deployment, download the index with `Accept-Encoding: identity`, confirm the
   bytes match that SHA-256 and verify wheel URLs return directly without redirects
   or content encoding. BillHarbor fails closed on redirects/encoded responses;
   a successful Pages deployment alone is not application acceptance.

The expected URL without a custom domain is
`https://eckphi.github.io/billharbor-vendors/index.json`. Configure BillHarbor
**Vendor stores → New store** using store ID `billharbor-vendors`, that index URL,
its reviewed exact SHA-256, approved origin `https://eckphi.github.io`, and publisher
`billharbor`. A deployment plugin administrator then checks the store and installs
the synthetic plugin. Target Python is the reviewed `3.13` runtime. Only synthetic
support is advertised; Amazon and Ökostrom remain deferred.

Custom domains and repository renames need an explicit workflow base-URL change
and reviewed BillHarbor trust update before publication. GitHub login-protected
Pages sites are unsuitable for the current unauthenticated store transport.

## Renewal, retention and rollback

The index expires after 90 days by default. Renew manually before expiry with a
higher revision and review/update BillHarbor's exact index trust digest. Renewal
changes issue/expiry bytes and therefore changes the digest even with the same
wheel. No silent automatic trust update or scheduled publication is provided.

Keep **every previously published manifest entry forever**, with its original
tag, filename and SHA-256. Add entries for new plugin versions; set `current` to
false to stop listing an old version while retaining its downloadable wheel.
Never replace an existing distribution/version's bytes; use a new plugin version.
All retained assets are downloaded and checked on every publication, then copied
to `packages/<sha256>/<filename>`. Missing old assets fail the build so a deployment
cannot silently remove historical install/rollback URLs. Preserve GitHub Release
assets and enable GitHub immutable releases when available under release policy.

Rollback to earlier plugin versions by changing the current flags while retaining
all entries, publishing a higher index revision and reviewing the new digest.
Do not deploy an old expired/lower-revision index or delete retained wheels.
Disabling the Pages workflow or site stops future distribution; existing installed
plugins and locks remain engine-owned. Preserve previous verified application
images and immutable install locks.

## Local verification

Download reviewed release wheels separately into
`<wheels>/<sha256>/<filename>`, then run without network or credentials:

```sh
python3 tools/build_pages_store.py --wheels /tmp/reviewed-wheels \
  --output /tmp/new-empty-site \
  --base-url https://eckphi.github.io/billharbor-vendors --revision 1
python3 -m unittest discover -s tests -p test_pages_store.py -v
```

Official setup references: [custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages),
[Pages availability and visibility](https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages).
