# Repository Hygiene

The current local and GitHub default branch is `codex/mvp-procurement-intelligence`; no `main` branch currently exists on the remote. Rename only through an additive, reviewed migration:

```powershell
git fetch origin
git switch codex/mvp-procurement-intelligence
git pull --ff-only
git branch main
git push -u origin main
```

Then change the default branch to `main` in GitHub Settings > Branches. Verify CI and links on `main`. Keep the old branch until the user deliberately decides it is no longer needed; do not force-push, delete branches, or rewrite history.

Internal briefs and agent-context files are intentionally ignored. Secrets, `.env` files, databases, dumps, generated exports/evidence, caches, uploads, build output, and screenshots containing private information must remain untracked.
