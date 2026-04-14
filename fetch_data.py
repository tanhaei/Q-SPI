"""
Utility script for extracting sprint-level Jira metrics for Q-SPI workflows.

The exported spreadsheet is intended to be joined with sprint-end technical debt
measurements (e.g., SonarQube / SonarCloud) so that TD_new and Q-SPI can be
computed per sprint as described in the article.
"""

from __future__ import annotations

import re
import warnings
from typing import Any, Iterable, Optional, Tuple

import pandas as pd
from jira import JIRA
from jira.exceptions import JIRAError

warnings.simplefilter(action="ignore", category=FutureWarning)

JIRA_SERVER = "https://issues.apache.org/jira"
PROJECT_KEY = "DUBBO"
PAGE_SIZE = 100


def connect_to_jira() -> JIRA:
    print("Connecting to Apache Jira...")
    return JIRA(server=JIRA_SERVER)


def find_field_id(jira: JIRA, field_names: Iterable[str]) -> Optional[str]:
    print(f"Searching for field ID matching: {list(field_names)}...")
    all_fields = jira.fields()
    target_names = {name.lower() for name in field_names}
    for field in all_fields:
        if field["name"].lower() in target_names:
            print(f"Found field: '{field['name']}' -> ID: {field['id']}")
            return field["id"]
    return None


def fetch_all_issues(jira: JIRA, jql: str, fields: list[str]) -> list[Any]:
    """Fetch Jira issues with pagination."""
    issues: list[Any] = []
    start_at = 0

    while True:
        batch = jira.search_issues(
            jql,
            startAt=start_at,
            maxResults=PAGE_SIZE,
            fields=fields,
        )
        issues.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        start_at += len(batch)

    print(f"Fetched {len(issues)} issues.")
    return issues


def get_issues_safe(jira: JIRA, project_key: str, sprint_field_id: str, sp_field_id: Optional[str]):
    """Try story-point extraction first; fall back to issue counting if needed."""
    if sp_field_id:
        try:
            print(f"Attempting to fetch with Story Points ({sp_field_id})...")
            jql = f'project = {project_key} AND sprint is not EMPTY AND "{sp_field_id}" is not EMPTY'
            fields = ["summary", "status", "created", "resolutiondate", sprint_field_id, sp_field_id]
            issues = fetch_all_issues(jira, jql, fields)
            if issues:
                return issues, sp_field_id
            print(">> Zero issues found with Story Points (possible permissions or field availability issue).")
            print(">> Switching to fallback mode (issue counting)...")
        except JIRAError as exc:
            print(f">> API error with Story Points: {exc}")
            print(">> Switching to fallback mode...")

    print("Fetching issues without Story Point filter...")
    jql = f"project = {project_key} AND sprint is not EMPTY"
    fields = ["summary", "status", "created", "resolutiondate", sprint_field_id]
    return fetch_all_issues(jira, jql, fields), None


_SPRINT_NAME_RE = re.compile(r"name=([^,]+)")
_SPRINT_END_RE = re.compile(r"endDate=([^,\]]+)")


def parse_sprint_metadata(raw_sprint: Any) -> Tuple[str, str]:
    """Extract sprint name and end date from common Jira sprint representations."""
    if raw_sprint is None:
        return "Unknown Sprint", ""

    if hasattr(raw_sprint, "name"):
        sprint_name = str(getattr(raw_sprint, "name", "Unknown Sprint"))
        end_date = str(getattr(raw_sprint, "endDate", "") or "")
        return sprint_name, end_date

    raw_text = str(raw_sprint)
    name_match = _SPRINT_NAME_RE.search(raw_text)
    end_match = _SPRINT_END_RE.search(raw_text)
    sprint_name = name_match.group(1) if name_match else raw_text
    end_date = end_match.group(1) if end_match else ""
    return sprint_name, end_date


def is_completed_issue(issue: Any) -> bool:
    """Use resolution information first, then fall back to terminal workflow states."""
    if getattr(issue.fields, "resolutiondate", None):
        return True

    status_name = str(getattr(issue.fields.status, "name", "")).strip().lower()
    return status_name in {"resolved", "closed", "done", "fixed"}


def get_sprint_data(jira: JIRA):
    sp_field_id = find_field_id(jira, ["Story Points", "Story Point", "Story Points Estimate"])
    sprint_field_id = find_field_id(jira, ["Sprint", "Sprint/s"])

    if not sprint_field_id:
        print("Error: Could not find the sprint field. Cannot proceed.")
        return None

    issues, valid_sp_id = get_issues_safe(jira, PROJECT_KEY, sprint_field_id, sp_field_id)
    if not issues:
        print("No issues found even in fallback mode.")
        return None

    sprint_metrics: dict[str, dict[str, Any]] = {}
    print(f"Processing {len(issues)} issues...")

    for issue in issues:
        sprints = getattr(issue.fields, sprint_field_id, None)
        if not sprints:
            continue

        last_sprint = sprints[-1]
        sprint_name, sprint_end_date = parse_sprint_metadata(last_sprint)

        value = 0.0
        if valid_sp_id:
            raw_value = getattr(issue.fields, valid_sp_id, None)
            if raw_value not in (None, ""):
                try:
                    value = float(raw_value)
                except (TypeError, ValueError):
                    value = 0.0

        if value == 0.0 and not valid_sp_id:
            value = 1.0

        if sprint_name not in sprint_metrics:
            sprint_metrics[sprint_name] = {
                "PV": 0.0,
                "EV": 0.0,
                "Issue_Count": 0,
                "Sprint_End_Date": sprint_end_date,
            }

        sprint_metrics[sprint_name]["Issue_Count"] += 1
        sprint_metrics[sprint_name]["PV"] += value
        if is_completed_issue(issue):
            sprint_metrics[sprint_name]["EV"] += value

        if sprint_end_date and not sprint_metrics[sprint_name]["Sprint_End_Date"]:
            sprint_metrics[sprint_name]["Sprint_End_Date"] = sprint_end_date

    return sprint_metrics


def save_to_excel(data) -> None:
    if not data:
        print("No data to save.")
        return

    df = pd.DataFrame.from_dict(data, orient="index")
    df.index.name = "Sprint_Name"
    df.reset_index(inplace=True)

    # Placeholders for the debt side of the article workflow.
    df["TD_SonarQube_Hours"] = ""
    df["TD_New_Hours"] = ""
    df["Beta_Hours_Per_SP"] = ""
    df["Lambda"] = ""
    df["Q_SPI"] = ""

    try:
        df["sort_key"] = df["Sprint_Name"].str.extract(r"(\d+)").astype(float)
        df = df.sort_values(by="sort_key").drop(columns=["sort_key"])
    except Exception:
        df = df.sort_values(by="Sprint_Name")

    filename = f"{PROJECT_KEY}_EVM_Data_Auto.xlsx"
    df.to_excel(filename, index=False)
    print(f"Done! Data saved to {filename}")


if __name__ == "__main__":
    try:
        jira_conn = connect_to_jira()
        metrics = get_sprint_data(jira_conn)
        save_to_excel(metrics)
    except Exception as exc:  # pragma: no cover - defensive CLI handling
        print(f"Critical Error: {exc}")
