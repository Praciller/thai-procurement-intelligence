# Repository hygiene

The public default branch is `main`. Branch migrations should remain additive and reviewed: create or update a branch, verify CI and links, then merge through a pull request. Do not force-push, delete shared history, or rewrite commit ancestry as part of routine maintenance.

Internal briefs and development-context files should remain ignored. Secrets, `.env` files, databases, dumps, generated exports/evidence, caches, uploads, build output, and screenshots containing private information must remain untracked.

Before merging public maintenance work, verify that issue titles, branch names, commit messages, pull-request metadata, source files, documentation, tests, and visible screenshots use project-focused wording rather than development-tool provenance.
