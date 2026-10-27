# ERIS: notes for Claude sessions

## Read first: the brain folder

Before changing anything, read `brain/README.md`. It holds the project's decisions, the reason for each one, and the
history of every change.

**Standing rule:** every change must, in the same commit:

1. add an entry to `brain/01-timeline.md` (format in `brain/TEMPLATE.md`);
2. update the topic file it touches (`brain/02`–`brain/10`);
3. record the reasoning, the alternatives considered, the trade-offs, and the verification as it was run.

## Commits

- Trailers: `Co-Authored-By: Claude <noreply@anthropic.com>` and the `Claude-Session:` line. Do not name a model in
  commit messages, PR titles or bodies, or any file in the repository.
- Push to the branch you were given. Open a pull request only when asked.

## Checks

- `./check.sh` runs the same checks as CI (Ruff, API tests, web lint and build). Set `E2E=1` to add the Playwright suite.
