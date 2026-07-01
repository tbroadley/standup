"""CLI for generating standup markdown from Todoist."""

import os
from datetime import date, datetime
from pathlib import Path

from standup import todoist


def _get_config_dir() -> Path:
    """Get the config directory, following XDG conventions."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg_config) if xdg_config else Path.home() / ".config"
    return base / "standup"


def generate_standup() -> str:
    """Generate standup markdown from Todoist.

    Yesterday section:
    - ☑️ for tasks completed on the previous working day
    - ❌ for tasks that were due on the previous working day but are still incomplete (overdue)

    Today section:
    - Tasks due today (not overdue)
    """
    today = date.today()
    yesterday = todoist.previous_working_day(today)

    # Get completed tasks from yesterday (midnight to midnight in local time)
    yesterday_start = datetime.combine(yesterday, datetime.min.time())
    yesterday_end = datetime.combine(yesterday, datetime.max.time())
    completed_yesterday = todoist.get_completed_tasks(yesterday_start, yesterday_end)

    # Get tasks completed today (midnight to midnight in local time)
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    completed_today = todoist.get_completed_tasks(today_start, today_end)

    # Get today's tasks (includes overdue)
    today_tasks = todoist.get_today_tasks()

    # Separate overdue (due before today) from actually due today
    overdue = [t for t in today_tasks if t.due_date and t.due_date < today.isoformat()]
    due_today = [t for t in today_tasks if not t.due_date or t.due_date >= today.isoformat()]

    lines = ["#### Yesterday"]

    for task in completed_yesterday:
        lines.append(f"- ☑️ {task.content}")

    for task in overdue:
        lines.append(f"- ❌ {task.content}")

    if len(lines) == 1:
        lines.append("(no tasks)")

    lines.extend(["", "#### Today"])

    for task in completed_today:
        lines.append(f"- ☑️ {task.content}")

    for task in due_today:
        lines.append(f"- {task.content}")

    if lines[-1] == "#### Today":
        lines.append("(no tasks)")

    return "\n".join(lines)


def main() -> None:
    """CLI entry point."""
    from dotenv import find_dotenv, load_dotenv

    # Load .env from XDG config directory, falling back to cwd
    config_env = _get_config_dir() / ".env"
    if config_env.exists():
        load_dotenv(config_env)
    else:
        load_dotenv(find_dotenv(usecwd=True))

    print(generate_standup())


if __name__ == "__main__":
    main()
