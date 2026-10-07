"""CLI for generating standup markdown from the status-dashboard task store."""

import datetime as dt
import os
import sys
from collections.abc import Callable
from pathlib import Path

from status_dashboard.clients.tasks import (
    COL_COMPLETED_AT,
    COL_CONTENT,
    COL_DONE,
    COL_DUE,
    COL_ORDER,
)
from status_dashboard.task_store import Rows, StoreError, TaskStore


def _config_base() -> Path:
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    return Path(xdg_config) if xdg_config else Path.home() / ".config"


def previous_working_day(from_date: dt.date) -> dt.date:
    """Get the previous working day (Monday-Friday) before the given date."""
    prev_day = from_date - dt.timedelta(days=1)
    while prev_day.weekday() >= 5:
        prev_day -= dt.timedelta(days=1)
    return prev_day


def _is_done(row: list[str]) -> bool:
    return row[COL_DONE].strip().upper() == "TRUE"


def _order(row: list[str]) -> int:
    order = row[COL_ORDER].strip()
    return int(order) if order.lstrip("-").isdigit() else 0


def _completed_at(row: list[str]) -> dt.datetime | None:
    raw = row[COL_COMPLETED_AT].strip()
    if not raw:
        return None
    try:
        parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone().replace(tzinfo=None) if parsed.tzinfo else parsed


def _completed_on(rows: Rows, day: dt.date) -> list[str]:
    done = [
        (at, row[COL_CONTENT].strip())
        for row in rows
        if _is_done(row) and (at := _completed_at(row)) and at.date() == day
    ]
    return [content for _, content in sorted(done, key=lambda item: item[0])]


def _open_due(rows: Rows, keep: Callable[[str], bool]) -> list[str]:
    open_rows = [
        row
        for row in rows
        if not _is_done(row) and (due := row[COL_DUE].strip()[:10]) and keep(due)
    ]
    return [row[COL_CONTENT].strip() for row in sorted(open_rows, key=_order)]


def generate_standup(rows: Rows, today: dt.date | None = None) -> str:
    """Generate standup markdown from task-store rows.

    Yesterday section:
    - ☑️ for tasks completed on the previous working day
    - ❌ for open tasks due before today (overdue)

    Today section:
    - ☑️ for tasks completed today
    - Open tasks due today
    """
    today = today or dt.date.today()
    today_str = today.isoformat()
    yesterday = previous_working_day(today)

    lines = ["#### Yesterday"]
    lines += [f"- ☑️ {c}" for c in _completed_on(rows, yesterday)]
    lines += [f"- ❌ {c}" for c in _open_due(rows, lambda due: due < today_str)]
    if len(lines) == 1:
        lines.append("(no tasks)")

    lines.extend(["", "#### Today"])
    lines += [f"- ☑️ {c}" for c in _completed_on(rows, today)]
    lines += [f"- {c}" for c in _open_due(rows, lambda due: due == today_str)]
    if lines[-1] == "#### Today":
        lines.append("(no tasks)")

    return "\n".join(lines)


def main() -> None:
    """CLI entry point."""
    from dotenv import find_dotenv, load_dotenv

    # Standup's own config wins; status-dashboard's config supplies the shared
    # task store location (load_dotenv never overrides variables already set).
    found = False
    for name in ("standup", "status-dashboard"):
        env = _config_base() / name / ".env"
        if env.exists():
            load_dotenv(env)
            found = True
    if not found:
        load_dotenv(find_dotenv(usecwd=True))

    try:
        rows = TaskStore().read().rows
    except StoreError as error:
        print(f"standup: {error}", file=sys.stderr)
        sys.exit(1)

    print(generate_standup(rows))


if __name__ == "__main__":
    main()
