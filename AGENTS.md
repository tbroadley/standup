# Standup

## Installation

Installed globally via `uv tool install 'standup @ git+https://github.com/tbroadley/standup.git'`. After pushing changes, reinstall with `uv tool install --reinstall --force 'standup @ git+https://github.com/tbroadley/standup.git'`.

## Task source

Tasks come from the same shared S3 task document that status-dashboard uses. Standup depends on the `status-dashboard` package and reads through its `TaskStore`, so schema validation and AWS CLI handling stay in one place. The dependency points at status-dashboard's `main` and is pinned in `uv.lock`, so run `uv lock --upgrade-package status-dashboard` to pick up schema changes.

## Configuration

`TASKS_S3_URI` (and optional `TASKS_AWS_REGION` / `TASKS_AWS_CLI`) are read from `$XDG_CONFIG_HOME/standup/.env`, then `$XDG_CONFIG_HOME/status-dashboard/.env`. Values from the first file take precedence. If neither file exists, `.env` in the working directory is used. Never commit the actual S3 location; this repo is public.

## Gotchas

- Completing a recurring task in status-dashboard rolls its due date forward without recording `completed_at`, so recurring completions don't show as ☑️.
- Store errors (expired AWS SSO, missing document) print to stderr and exit 1 rather than rendering "(no tasks)".
