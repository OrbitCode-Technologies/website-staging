# Website staging

Public, temporary PR previews for OrbitCode Technologies.

The **Refresh PR previews** workflow runs approximately every ten minutes, on
changes to this repository, or manually through Actions > Run workflow. GitHub
may delay scheduled runs. Scheduled workflows in public repositories are disabled
after 60 days without repository activity; re-enable the workflow if needed.

The publisher reads open PRs against the website main branch, copies static files
from organization branches, and removes previews for closed PRs. Fork PRs are
excluded. It never executes proposed code or installs PR dependencies.

Pages deploys only `public/`, with one directory per PR. The workflow uses only
this repository's automatically supplied GITHUB_TOKEN; no deploy keys, personal
access tokens, or external hosting services are needed. Commits are attributed to
the GitHub account that triggers the workflow.

Production remains in the separate website repository. Since GitHub Pages inherits
the organization custom domain, preview URLs use
`https://orbitcodetech.in/website-staging/pr-<number>/`.

Previews are public. Robots directives discourage indexing but do not control
access. Relative asset paths are required for previews to render correctly.
