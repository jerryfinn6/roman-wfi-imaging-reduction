# Publish the existing repository

The GitHub remote is `jerryfinn6/roman-wfi-imaging-reduction`. The local main branch already exists. README includes the AI disclosure; LICENSE contains BSD-3-Clause for original project code. Third-party notices remain applicable.

Run from the working directory:

```bash
cd /Users/bangzhengsun/Downloads/roman-wfi-reduction
git add README.md LICENSE UPLOAD.md
git commit -m "Add AI disclosure and BSD 3-Clause license"
git push origin main
```

Then make the existing private repository public (this exposes committed history as well):

```bash
gh repo edit jerryfinn6/roman-wfi-imaging-reduction --visibility public --accept-visibility-change-consequences
gh repo view jerryfinn6/roman-wfi-imaging-reduction --json url,visibility,licenseInfo
```

Alternatively: GitHub repository Settings → General → Danger Zone → Change repository visibility → Public. No new repository or remote is needed.
