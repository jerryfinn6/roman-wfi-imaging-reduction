# Upload to GitHub

This package is prepared locally; it has not been published. Choose repository visibility and a license before public release.

## GitHub CLI

From this folder, after installing Git and GitHub CLI:

```bash
git init -b main
git add .
git diff --cached --stat
git commit -m "Add staged Roman WFI imaging reduction workflow"
gh auth login
gh repo create roman-wfi-reduction --private --source=. --remote=origin --push
```

Use `--public` instead of `--private` only if you want public access. To create under an organization, use `ORGANIZATION/roman-wfi-reduction`. Add collaborators in the repository Settings → Collaborators (or organization access settings).

## Without GitHub CLI

Create an empty repository on GitHub, without an initial README/license/gitignore. Run the git init/add/commit commands above, then:

```bash
git remote add origin https://github.com/YOUR_ACCOUNT/roman-wfi-reduction.git
git push -u origin main
```

Authenticate using your configured Git credential manager, a personal access token or SSH—not your GitHub account password. Review `/path/to/` placeholders and choose a license before advertising the repository as ready for general use.
