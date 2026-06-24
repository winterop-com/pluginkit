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

Managing rulesets needs admin. The built-in `GITHUB_TOKEN` is often rejected for
ruleset writes, so set a fine-grained PAT with **Administration: read and write** on
the repo as the `RULESETS_TOKEN` secret. The workflow uses it when present and falls
back to `GITHUB_TOKEN` otherwise.

## Reuse across repos

Copy this folder + `.github/workflows/rulesets.yml` into any repo and it
self-applies. To avoid duplicating the workflow body, host it once as a reusable
workflow (`on: workflow_call`) in a shared repo and have each repo call it with a
one-line caller that passes `secrets: inherit`.
