"""
Jira Client - Fetches issue data from Jira REST API v3
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()


class JiraClient:

    def __init__(self):
        self.base_url = os.getenv("JIRA_BASE_URL", "http://localhost:4001")
        self.token = os.getenv("JIRA_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def fetch_issue(self, issue_key: str) -> dict:
        """Fetch a Jira issue and return a clean dict with plain-text description."""
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        response = httpx.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()

        fields = data.get("fields", {})
        adf_description = fields.get("description", {})

        return {
            "key": data.get("key"),
            "summary": fields.get("summary", ""),
            "description_text": self._extract_text(adf_description),
            "priority": fields.get("priority", {}).get("name", ""),
            "status": fields.get("status", {}).get("name", "")
        }

    def _extract_text(self, node: dict) -> str:
        """Recursively extract plain text from an ADF (Atlassian Document Format) node."""
        if not node or not isinstance(node, dict):
            return ""

        # Base case: this node is a text leaf
        if node.get("type") == "text":
            return node.get("text", "")

        # Recursive case: walk all children
        parts = []
        for child in node.get("content", []):
            parts.append(self._extract_text(child))

        return "\n".join(part for part in parts if part)
