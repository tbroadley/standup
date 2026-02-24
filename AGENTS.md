# Standup

## Installation

Installed globally via `uv tool install 'standup @ git+https://github.com/tbroadley/standup.git'`. After pushing changes, reinstall with `uv tool install --reinstall --force 'standup @ git+https://github.com/tbroadley/standup.git'`.

## Todoist API

- The old Sync API v9 (`sync/v9/completed/get_all`) is deprecated and returns 410 Gone. Use `api/v1/tasks/completed` instead. Same query params (`since`, `until`, `limit`, `offset`) work.
- The `api/v1/tasks/completed` endpoint paginates via `offset` (not cursor). Default page size is small; request `limit=200` to minimize round trips.

## Gotchas

- Error handling in API calls returns empty lists on failure. This means API deprecations or auth issues silently show as "(no tasks)" with no indication of failure.
