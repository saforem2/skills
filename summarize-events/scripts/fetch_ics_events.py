# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "icalendar",
#     "requests",
#     "python-dateutil",
# ]
# ///
"""Fetch and filter calendar events from an Outlook ICS feed.

Usage:
    uv run fetch_ics_events.py [OPTIONS]

Options:
    --last day|week|month|year    Show events from the last period (default: week)
    --next day|week|month|year    Show events for the next period
    --start YYYY-MM-DD            Start of custom date range
    --end YYYY-MM-DD              End of custom date range
    --include-focus               Include "Focus time" events (excluded by default)
    --include-canceled            Include canceled events (excluded by default)
    --format json|markdown|both   Output format (default: both)
    --ics-url URL                 ICS feed URL (overrides env/config)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dateutil.relativedelta import relativedelta
from icalendar import Calendar

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TZ = ZoneInfo("America/Chicago")


def load_ics_url(cli_url: str | None) -> str:
    if cli_url:
        return cli_url
    url = os.environ.get("OUTLOOK_CALENDAR_ICS_URL")
    if url:
        return url
    env_file = SKILL_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("OUTLOOK_CALENDAR_ICS_URL="):
                return line.split("=", 1)[1].strip().strip("\"'")
    print("ERROR: No ICS URL found. Set OUTLOOK_CALENDAR_ICS_URL in .env or pass --ics-url", file=sys.stderr)
    sys.exit(1)


def load_html_url() -> str | None:
    url = os.environ.get("OUTLOOK_CALENDAR_HTML_URL")
    if url:
        return url
    env_file = SKILL_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("OUTLOOK_CALENDAR_HTML_URL="):
                return line.split("=", 1)[1].strip().strip("\"'")
    return None


def compute_date_range(args: argparse.Namespace) -> tuple[date, date]:
    today = date.today()
    if args.start and args.end:
        return date.fromisoformat(args.start), date.fromisoformat(args.end)

    period = args.last or args.next or "week"
    deltas = {
        "day": timedelta(days=1),
        "week": timedelta(weeks=1),
        "month": relativedelta(months=1),
        "year": relativedelta(years=1),
    }
    delta = deltas[period]

    if args.next:
        return today, today + delta
    else:
        return today - delta, today


def normalize_dt(dt_val, tz: ZoneInfo = DEFAULT_TZ) -> datetime:
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=tz)
        return dt_val.astimezone(tz)
    if isinstance(dt_val, date):
        return datetime(dt_val.year, dt_val.month, dt_val.day, tzinfo=tz)
    return dt_val


def fetch_events(ics_url: str, start: date, end: date,
                 include_focus: bool = False,
                 include_canceled: bool = False) -> list[dict]:
    resp = requests.get(ics_url, timeout=30)
    resp.raise_for_status()
    cal = Calendar.from_ical(resp.text)

    start_dt = datetime(start.year, start.month, start.day, tzinfo=DEFAULT_TZ)
    end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=DEFAULT_TZ)

    events = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        summary = str(component.get("summary", ""))
        status = str(component.get("status", "")).upper()

        if not include_canceled and (
            status == "CANCELLED"
            or summary.lower().startswith("canceled")
            or summary.lower().startswith("cancelled")
        ):
            continue

        if not include_focus and "focus time" in summary.lower():
            continue

        dtstart = component.get("dtstart")
        dtend = component.get("dtend")
        if not dtstart:
            continue

        ev_start = normalize_dt(dtstart.dt)
        ev_end = normalize_dt(dtend.dt) if dtend else ev_start + timedelta(hours=1)

        if ev_start > end_dt or ev_end < start_dt:
            continue

        description = str(component.get("description", "")) or ""
        location = str(component.get("location", "")) or ""

        is_all_day = not isinstance(dtstart.dt, datetime)

        events.append({
            "summary": summary,
            "start": ev_start.isoformat(),
            "end": ev_end.isoformat(),
            "date": ev_start.strftime("%Y-%m-%d"),
            "day_of_week": ev_start.strftime("%A"),
            "start_time": "All day" if is_all_day else ev_start.strftime("%-I:%M %p"),
            "end_time": "" if is_all_day else ev_end.strftime("%-I:%M %p"),
            "location": location,
            "description": description[:2000],
            "all_day": is_all_day,
        })

    events.sort(key=lambda e: e["start"])
    return events


def format_markdown_table(events: list[dict]) -> str:
    lines = ["| Date | Time | Event | Location |", "|------|------|-------|----------|"]
    for ev in events:
        time_str = ev["start_time"] if ev["all_day"] else f"{ev['start_time']}–{ev['end_time']}"
        loc = ev["location"][:50] if ev["location"] else ""
        lines.append(f"| {ev['day_of_week'][:3]} {ev['date']} | {time_str} | {ev['summary']} | {loc} |")
    return "\n".join(lines)


def format_text_summary(events: list[dict]) -> str:
    from itertools import groupby

    lines = []
    for day, day_events in groupby(events, key=lambda e: (e["day_of_week"], e["date"])):
        day_name, day_date = day
        lines.append(f"\n### {day_name}, {day_date}")
        for ev in day_events:
            time_str = ev["start_time"] if ev["all_day"] else f"{ev['start_time']}–{ev['end_time']}"
            lines.append(f"- **{ev['summary']}** ({time_str})")
            desc = ev["description"].strip()
            if desc:
                first_line = desc.split("\n")[0][:200]
                if first_line and first_line.lower() != ev["summary"].lower():
                    lines.append(f"  {first_line}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fetch calendar events from ICS feed")
    parser.add_argument("--last", choices=["day", "week", "month", "year"])
    parser.add_argument("--next", choices=["day", "week", "month", "year"])
    parser.add_argument("--start", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", help="End date YYYY-MM-DD")
    parser.add_argument("--include-focus", action="store_true")
    parser.add_argument("--include-canceled", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown", "both"], default="both")
    parser.add_argument("--ics-url")
    args = parser.parse_args()

    if not args.last and not args.next and not args.start:
        args.last = "week"

    ics_url = load_ics_url(args.ics_url)
    html_url = load_html_url()
    start, end = compute_date_range(args)

    events = fetch_events(ics_url, start, end,
                          include_focus=args.include_focus,
                          include_canceled=args.include_canceled)

    result = {
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "event_count": len(events),
        "events": events,
        "html_calendar_url": html_url,
    }

    if args.format == "json":
        print(json.dumps(result, indent=2))
    elif args.format == "markdown":
        print(f"## Calendar Events: {start} to {end}\n")
        print(format_markdown_table(events))
        print(format_text_summary(events))
    else:
        print(json.dumps(result, indent=2))
        print("\n---MARKDOWN---\n")
        print(f"## Calendar Events: {start} to {end}\n")
        print(format_markdown_table(events))
        print(format_text_summary(events))

    if len(events) == 0 and html_url:
        print(f"\n---NO_EVENTS_FOUND---", file=sys.stderr)
        print(f"ICS feed returned no events for {start} to {end}.", file=sys.stderr)
        print(f"HTML calendar URL available for Playwright fallback: {html_url}", file=sys.stderr)


if __name__ == "__main__":
    main()
