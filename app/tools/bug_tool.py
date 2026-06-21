"""IssueTracker bug tracking tool for filing, updating, and querying bug records."""

from crewai.tools import BaseTool
import json


class IssueFileTool(BaseTool):
    name: str = "issue_tracker_file_bug"
    description: str = "File a new bug in IssueTracker (generic issue tracking system) and return the IssueTracker ID"

    def _run(self, title: str, description: str, severity: str, priority: str, reproduction_steps: list[str]) -> str:
        """
        File a bug in IssueTracker.
        In production: calls IssueTracker REST API / MCP server.
        """
        # Placeholder — replace with actual IssueTracker MCP call
        issue_tracker_id = f"CSCwx{hash(title) % 99999:05d}"
        return json.dumps({"issue_tracker_id": issue_tracker_id, "status": "open", "title": title})


class IssueUpdateTool(BaseTool):
    name: str = "issue_tracker_update_bug"
    description: str = "Update the status of an existing IssueTracker bug record"

    def _run(self, issue_tracker_id: str, status: str, comments: str = "") -> str:
        """
        Update IssueTracker bug status.
        In production: calls IssueTracker REST API.
        """
        # Placeholder
        return json.dumps({"issue_tracker_id": issue_tracker_id, "status": status, "updated": True})


class IssueQueryTool(BaseTool):
    name: str = "issue_tracker_query_bug"
    description: str = "Query a IssueTracker bug record by ID to get current status and details"

    def _run(self, issue_tracker_id: str) -> str:
        """
        Query IssueTracker bug record.
        In production: calls IssueTracker REST API.
        """
        # Placeholder
        return json.dumps({"issue_tracker_id": issue_tracker_id, "status": "open", "found": True})


bug_tools = [IssueFileTool(), IssueUpdateTool(), IssueQueryTool()]
