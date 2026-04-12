# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Fetch git commit activity from GitHub for a date range.

Usage:
    uv run fetch_git_activity.py [OPTIONS]

Options:
    --last day|week|month|year    Period to look back (default: week)
    --next day|week|month|year    Period to look forward
    --start YYYY-MM-DD            Start of custom date range
    --end YYYY-MM-DD              End of custom date range
    --user USERNAME               GitHub username (default: from gh CLI)
    --format json|markdown|both   Output format (default: both)
    --exclude REPO1,REPO2         Comma-separated repos to exclude (e.g. Notes)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import date, timedelta


def compute_date_range(args: argparse.Namespace) -> tuple[date, date]:
    today = date.today()
    if args.start and args.end:
        return date.fromisoformat(args.start), date.fromisoformat(args.end)

    period = args.last or args.next or "week"
    deltas = {
        "day": timedelta(days=1),
        "week": timedelta(weeks=1),
        "month": timedelta(days=30),
        "year": timedelta(days=365),
    }
    delta = deltas[period]

    if args.next:
        return today, today + delta
    else:
        return today - delta, today


def get_gh_user() -> str:
    result = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("ERROR: gh CLI not authenticated. Run 'gh auth login'", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def parse_commit(item: dict, exclude: list[str], repo_override: str | None = None) -> dict | None:
    """Parse a commit from either the search API or repos API into a normalized dict."""
    if repo_override:
        repo = repo_override
    else:
        repo = item.get("repository", {}).get("full_name", "")
    repo_short = repo.split("/")[-1] if "/" in repo else repo

    if repo_short in exclude:
        return None

    commit_obj = item.get("commit", {})
    msg_lines = commit_obj.get("message", "").split("\n")
    sha = item.get("sha", "")[:7]
    commit_date = commit_obj.get("committer", {}).get("date", "")
    html_url = item.get("html_url", "")

    return {
        "repo": repo,
        "repo_short": repo_short,
        "sha": sha,
        "date": commit_date,
        "message": msg_lines[0],
        "body": "\n".join(msg_lines[1:]).strip()[:500] if len(msg_lines) > 1 else "",
        "url": html_url,
    }


def fetch_commits_search(user: str, start: date, end: date, exclude: list[str]) -> list[dict]:
    """Fetch commits via the search API (covers owned and collaborated repos)."""
    query = f"author:{user}+committer-date:{start}..{end}"
    commits = []
    page = 1

    while True:
        result = subprocess.run(
            ["gh", "api", f"search/commits?q={query}&sort=committer-date&per_page=100&page={page}",
             "--jq", ".items"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"ERROR: GitHub API call failed: {result.stderr}", file=sys.stderr)
            break

        items = json.loads(result.stdout) if result.stdout.strip() else []
        if not items:
            break

        for item in items:
            c = parse_commit(item, exclude)
            if c:
                commits.append(c)

        page += 1
        total = json.loads(subprocess.run(
            ["gh", "api", f"search/commits?q={query}&sort=committer-date&per_page=1",
             "--jq", ".total_count"],
            capture_output=True, text=True
        ).stdout.strip() or "0")
        if page * 100 >= total:
            break

    return commits


def fetch_fork_repos(user: str, since: date | None = None) -> list[str]:
    """List forked repos for the user, filtered to recently-pushed if since is given."""
    repos: list[str] = []
    page = 1
    while True:
        result = subprocess.run(
            ["gh", "api",
             f"users/{user}/repos?type=forks&sort=pushed&direction=desc&per_page=100&page={page}",
             "--jq", '.[] | .full_name + " " + .pushed_at'],
            capture_output=True, text=True
        )
        if result.returncode != 0 or not result.stdout.strip():
            break
        for line in result.stdout.strip().split("\n"):
            parts = line.rsplit(" ", 1)
            if len(parts) != 2:
                continue
            repo_name, pushed_at = parts
            if since and pushed_at < since.isoformat():
                # Sorted by pushed desc — once we pass the cutoff, stop
                return repos
            repos.append(repo_name)
        if len(result.stdout.strip().split("\n")) < 100:
            break
        page += 1
    return repos


def fetch_branches(repo: str) -> list[str]:
    """List all branches for a repo."""
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/branches?per_page=100", "--jq", ".[].name"],
        capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    return result.stdout.strip().split("\n")


def fetch_commits_from_forks(user: str, forks: list[str], start: date, end: date,
                              exclude: list[str]) -> list[dict]:
    """Fetch commits from forked repos via the repos API, scanning all branches."""
    commits = []
    seen_shas: set[str] = set()
    since = f"{start}T00:00:00Z"
    until = f"{end}T23:59:59Z"

    for fork in forks:
        fork_short = fork.split("/")[-1] if "/" in fork else fork
        if fork_short in exclude:
            continue

        branches = fetch_branches(fork)
        if not branches:
            branches = [""]  # fall back to default branch

        for branch in branches:
            sha_param = f"&sha={branch}" if branch else ""
            result = subprocess.run(
                ["gh", "api",
                 f"repos/{fork}/commits?author={user}&since={since}&until={until}&per_page=100{sha_param}"],
                capture_output=True, text=True
            )
            if result.returncode != 0 or not result.stdout.strip():
                continue

            items = json.loads(result.stdout)
            for item in items:
                c = parse_commit(item, exclude, repo_override=fork)
                if c and c["sha"] not in seen_shas:
                    if branch:
                        c["branch"] = branch
                    commits.append(c)
                    seen_shas.add(c["sha"])

    return commits


def fetch_commits(user: str, start: date, end: date, exclude: list[str]) -> list[dict]:
    """Fetch commits from search API + fork repos, deduplicated."""
    # Search API: covers owned repos, orgs, and collaborations
    commits = fetch_commits_search(user, start, end, exclude)
    seen_shas = {c["sha"] for c in commits}

    # Repos API on forks: catches commits the search API may miss
    # Only scan forks pushed to since the start date (avoids scanning all 260+ forks)
    forks = fetch_fork_repos(user, since=start)
    if forks:
        fork_commits = fetch_commits_from_forks(user, forks, start, end, exclude)
        for c in fork_commits:
            if c["sha"] not in seen_shas:
                commits.append(c)
                seen_shas.add(c["sha"])

    commits.sort(key=lambda c: c["date"])
    return commits


def format_markdown_table(commits: list[dict]) -> str:
    lines = ["| Date | Repo | Commit | Message |", "|------|------|--------|---------|"]
    for c in commits:
        d = c["date"][:10] if c["date"] else ""
        lines.append(f"| {d} | {c['repo_short']} | `{c['sha']}` | {c['message'][:80]} |")
    return "\n".join(lines)


def format_text_summary(commits: list[dict]) -> str:
    by_repo: dict[str, list[dict]] = defaultdict(list)
    for c in commits:
        by_repo[c["repo"]].append(c)

    lines = []
    for repo, repo_commits in sorted(by_repo.items()):
        lines.append(f"\n### {repo} ({len(repo_commits)} commits)")
        for c in repo_commits:
            lines.append(f"- `{c['sha']}` {c['message']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub commit activity")
    parser.add_argument("--last", choices=["day", "week", "month", "year"])
    parser.add_argument("--next", choices=["day", "week", "month", "year"])
    parser.add_argument("--start", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", help="End date YYYY-MM-DD")
    parser.add_argument("--user", help="GitHub username (default: from gh CLI)")
    parser.add_argument("--format", choices=["json", "markdown", "both"], default="both")
    parser.add_argument("--exclude", default="", help="Comma-separated repos to exclude")
    args = parser.parse_args()

    if not args.last and not args.next and not args.start:
        args.last = "week"

    user = args.user or get_gh_user()
    start, end = compute_date_range(args)
    exclude = [r.strip() for r in args.exclude.split(",") if r.strip()]

    commits = fetch_commits(user, start, end, exclude)

    # Build per-repo stats
    repo_stats: dict[str, int] = defaultdict(int)
    for c in commits:
        repo_stats[c["repo"]] += 1

    result = {
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "user": user,
        "total_commits": len(commits),
        "repos_touched": len(repo_stats),
        "repo_stats": dict(sorted(repo_stats.items(), key=lambda x: -x[1])),
        "commits": commits,
    }

    if args.format == "json":
        print(json.dumps(result, indent=2))
    elif args.format == "markdown":
        print(f"## Git Activity: {start} to {end} ({len(commits)} commits across {len(repo_stats)} repos)\n")
        print(format_markdown_table(commits))
        print(format_text_summary(commits))
    else:
        print(json.dumps(result, indent=2))
        print("\n---MARKDOWN---\n")
        print(f"## Git Activity: {start} to {end} ({len(commits)} commits across {len(repo_stats)} repos)\n")
        print(format_markdown_table(commits))
        print(format_text_summary(commits))


if __name__ == "__main__":
    main()
