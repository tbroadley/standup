"""Todoist API client for standup generation."""

import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import httpx


@dataclass
class Task:
    id: str
    content: str
    due_date: str | None = None
    day_order: int = 0


@dataclass
class CompletedTask:
    id: str
    content: str
    completed_at: datetime


def _get_token() -> str | None:
    return os.environ.get("TODOIST_API_TOKEN")


def get_completed_tasks(
    since: datetime, until: datetime, api_token: str | None = None
) -> list[CompletedTask]:
    """Get tasks completed within the given time range.

    Uses the Todoist Sync API v9 completed/get_all endpoint.
    Returns tasks sorted by completion time (oldest first).
    """
    token = api_token or _get_token()
    if not token:
        return []

    try:
        response = httpx.get(
            "https://api.todoist.com/sync/v9/completed/get_all",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "since": since.strftime("%Y-%m-%dT%H:%M"),
                "until": until.strftime("%Y-%m-%dT%H:%M"),
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError):
        return []

    tasks = []
    for item in data.get("items", []):
        completed_at_str = item.get("completed_at", "")
        if not completed_at_str:
            continue
        completed_at = datetime.fromisoformat(completed_at_str.replace("Z", "+00:00"))
        tasks.append(
            CompletedTask(
                id=item.get("task_id", item.get("id", "")),
                content=item.get("content", ""),
                completed_at=completed_at,
            )
        )

    tasks.sort(key=lambda t: t.completed_at)
    return tasks


def get_today_tasks(api_token: str | None = None) -> list[Task]:
    """Get Todoist tasks due today (includes overdue), sorted by day_order."""
    token = api_token or _get_token()
    if not token:
        return []

    try:
        response = httpx.post(
            "https://api.todoist.com/api/v1/sync",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "sync_token": "*",
                "resource_types": '["items"]',
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError):
        return []

    today_str = date.today().isoformat()
    tasks = []

    for item in data.get("items", []):
        if item.get("checked") or item.get("is_deleted"):
            continue

        due = item.get("due")
        if not due:
            continue

        due_date = due.get("date", "")[:10]
        if due_date > today_str:
            continue

        tasks.append(
            Task(
                id=item["id"],
                content=item["content"],
                due_date=due_date,
                day_order=item.get("day_order", 0),
            )
        )

    tasks.sort(key=lambda t: t.day_order)
    return tasks


def previous_working_day(from_date: date | None = None) -> date:
    """Get the previous working day (Monday-Friday) before the given date."""
    if from_date is None:
        from_date = date.today()

    prev_day = from_date - timedelta(days=1)
    while prev_day.weekday() >= 5:  # Saturday=5, Sunday=6
        prev_day -= timedelta(days=1)
    return prev_day
