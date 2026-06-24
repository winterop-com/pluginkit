# Rulesets as code

Each `*.json` here is a GitHub **repository ruleset** (the modern replacement for
branch protection). The [`rulesets` workflow](../workflows/rulesets.yml) applies
them to this repo on push and on manual dispatch - creating each by name, or
updating it in place if it already exists. No GitHub Enterprise required: repo-level
rulesets are available to everyone (private repos need GitHub Team).

## Add or change a ruleset

1. Drop a JSON file here (or edit an existing one). The body is exactly the
   ruleset API payload - `name`, `target`, `enforcement`, `conditions`, `rules`,
   `bypass_actors`. Export an existing one as a starting point:
   ```bash
   gh api repos/OWNER/REPO/rulesets/ID \
     --jq '{name, target, enforcement, conditions, rules, bypass_actors}'
   ```
2. Commit and push. The workflow applies it. `name` is the key - keep it stable so
   updates land on the same ruleset instead of creating duplicates.

## Token

Managing rulesets needs admin, and the built-in `GITHUB_TOKEN` can **not** be
granted it - the workflow `permissions:` block has no `administration` scope, so the
token can never manage rulesets. Set a fine-grained PAT with **Administration: read
and write** on the repo as the `RULESETS_TOKEN` secret:

```bash
gh secret set RULESETS_TOKEN --repo OWNER/REPO   # paste the PAT when prompted
```

Without that secret the job emits a warning and skips (it stays green rather than
failing), so rulesets remain whatever you last applied by hand.

## Reuse across repos

The workflow supports `workflow_call`, so host one canonical copy (e.g. in
`winterop-com/.github`) and have every other repo call it instead of duplicating the
body. Each repo keeps its own `.github/rulesets/*.json` plus a small caller:

```yaml
# .github/workflows/rulesets.yml in any repo
name: rulesets
on:
  push: { branches: [main], paths: ['.github/rulesets/**'] }
  workflow_dispatch:
jobs:
  apply:
    uses: winterop-com/.github/.github/workflows/rulesets.yml@main
    secrets: inherit   # passes RULESETS_TOKEN through
```

`checkout` inside the reusable workflow runs against the **caller** repo, so each
repo applies its own rulesets to itself. Set `RULESETS_TOKEN` once as an
**organization secret** (Settings -> Secrets and variables -> Actions) and every
repo inherits it - no per-repo token setup.
