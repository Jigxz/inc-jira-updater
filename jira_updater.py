import pandas as pd
from sentence_transformers import SentenceTransformer
import duckdb
import numpy as np
import json
import requests
from typing import List, Dict, Optional
import os
from datetime import datetime

class JiraCommentUpdater:
    def __init__(self, db_file: str, jira_base_url: str, jira_username: str, jira_api_token: str):
        self.db_file = db_file
        self.jira_base_url = jira_base_url.rstrip('/')
        self.jira_username = jira_username
        self.jira_api_token = jira_api_token
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.con = duckdb.connect(database=self.db_file, read_only=True)

        # Setup authentication
        self.auth = (self.jira_username, self.jira_api_token)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def cosine_similarity(self, a, b):
        """Calculate cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def search_similar_incidents(self, jira_description: str, threshold: float = 0.3, limit: int = 5) -> List[Dict]:
        """Search for similar incidents based on Jira description"""
        # Generate embedding for the Jira description
        query_vector = self.model.encode([jira_description])[0]

        # Create similarity function in DuckDB
        self.con.create_function("cosine_similarity", self.cosine_similarity, ["FLOAT[]", "FLOAT[]"], float)

        # Search query
        sql_query = """
        SELECT "INC", "Short Desc", "Created Date", "Updated Date", "Assignee", "Group", "Created By", "Updated By",
               cosine_similarity(vector, ?::FLOAT[]) AS similarity
        FROM incidents
        ORDER BY similarity DESC
        LIMIT ?
        """

        results = self.con.execute(sql_query, [query_vector.tolist(), limit]).fetchall()

        similar_incidents = []
        for row in results:
            if row[8] >= threshold:  # similarity score
                similar_incidents.append({
                    'INC': row[0],
                    'Short Desc': row[1],
                    'Created Date': row[2],
                    'Updated Date': row[3],
                    'Assignee': row[4],
                    'Group': row[5],
                    'Created By': row[6],
                    'Updated By': row[7],
                    'similarity': row[8]
                })

        return similar_incidents

    def analyze_historical_patterns(self, similar_incidents: List[Dict], jira_description: str) -> Dict:
        """Analyze historical patterns using LLM to determine similar fixes"""
        # This is a placeholder for LLM analysis
        # In a real implementation, you would integrate with OpenAI, Claude, or another LLM

        analysis = {
            'similar_patterns': [],
            'common_fixes': [],
            'recommended_actions': [],
            'confidence_score': 0.0
        }

        if not similar_incidents:
            return analysis

        # Group by assignee and group to find patterns
        assignee_patterns = {}
        group_patterns = {}

        for incident in similar_incidents:
            assignee = incident.get('Assignee', 'Unknown')
            group = incident.get('Group', 'Unknown')

            if assignee not in assignee_patterns:
                assignee_patterns[assignee] = []
            assignee_patterns[assignee].append(incident)

            if group not in group_patterns:
                group_patterns[group] = []
            group_patterns[group].append(incident)

        # Find most common assignee and group
        most_common_assignee = max(assignee_patterns.keys(), key=lambda k: len(assignee_patterns[k]))
        most_common_group = max(group_patterns.keys(), key=lambda k: len(group_patterns[k]))

        analysis['similar_patterns'] = [
            f"Most incidents handled by: {most_common_assignee}",
            f"Most incidents in group: {most_common_group}",
            f"Total similar incidents found: {len(similar_incidents)}"
        ]

        # Generate recommended actions based on patterns
        if len(similar_incidents) >= 3:
            analysis['recommended_actions'] = [
                f"Assign to {most_common_assignee} as they have handled similar incidents",
                f"Consider involving {most_common_group} team",
                "Review past solutions from similar incidents"
            ]
            analysis['confidence_score'] = min(0.8, len(similar_incidents) * 0.15)

        return analysis

    def get_jira_issue(self, issue_key: str) -> Optional[Dict]:
        """Get Jira issue details"""
        url = f"{self.jira_base_url}/rest/api/2/issue/{issue_key}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Jira issue {issue_key}: {e}")
            return None

    def update_jira_comment(self, issue_key: str, comment: str) -> bool:
        """Update Jira issue with a comment"""
        url = f"{self.jira_base_url}/rest/api/2/issue/{issue_key}/comment"
        payload = {"body": comment}

        try:
            response = requests.post(url, auth=self.auth, headers=self.headers, json=payload)
            response.raise_for_status()
            print(f"Successfully added comment to {issue_key}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error updating Jira comment for {issue_key}: {e}")
            return False

    def generate_analysis_comment(self, jira_description: str, similar_incidents: List[Dict], analysis: Dict) -> str:
        """Generate a comprehensive comment for Jira based on analysis"""

        comment = f"""🔍 **Automated Analysis for Incident**

**Original Description:** {jira_description}

**Similar Historical Incidents Found:**
"""

        for incident in similar_incidents:
            comment += f"""
• **INC-{incident['INC']}**: {incident['Short Desc']}
  - Created: {incident['Created Date']}
  - Updated: {incident['Updated Date']}
  - Assignee: {incident['Assignee']}
  - Group: {incident['Group']}
  - Similarity: {incident['similarity']:.2f}
"""

        comment += f"""
**Analysis Summary:**
- {analysis['similar_patterns'][0]}
- {analysis['similar_patterns'][1]}
- {analysis['similar_patterns'][2]}

**Recommended Actions:**
"""
        for action in analysis['recommended_actions']:
            comment += f"• {action}\n"

        comment += f"""
**Confidence Score:** {analysis['confidence_score']:.2f}

---
*This analysis was generated automatically based on historical incident data.*
"""
        return comment

    def process_jira_issue(self, issue_key: str, threshold: float = 0.3) -> bool:
        """Main function to process a Jira issue and update its comments"""
        print(f"Processing Jira issue: {issue_key}")

        # Get Jira issue details
        issue = self.get_jira_issue(issue_key)
        if not issue:
            print(f"Could not fetch issue {issue_key}")
            return False

        # Extract description
        description = issue['fields'].get('description', '')
        if not description:
            print(f"No description found for issue {issue_key}")
            return False

        print(f"Analyzing description: {description[:100]}...")

        # Search for similar incidents
        similar_incidents = self.search_similar_incidents(description, threshold)

        if not similar_incidents:
            print(f"No similar incidents found for {issue_key}")
            return False

        print(f"Found {len(similar_incidents)} similar incidents")

        # Perform historical analysis
        analysis = self.analyze_historical_patterns(similar_incidents, description)

        # Generate and add comment
        comment = self.generate_analysis_comment(description, similar_incidents, analysis)
        success = self.update_jira_comment(issue_key, comment)

        return success

def main():
    # Configuration - Update these with your actual Jira credentials
    JIRA_BASE_URL = "https://your-domain.atlassian.net"  # Replace with your Jira instance URL
    JIRA_USERNAME = "your-email@example.com"  # Replace with your Jira email
    JIRA_API_TOKEN = "your-api-token"  # Replace with your Jira API token

    # Initialize the updater
    updater = JiraCommentUpdater(
        db_file="local_vector_db.duckdb",
        jira_base_url=JIRA_BASE_URL,
        jira_username=JIRA_USERNAME,
        jira_api_token=JIRA_API_TOKEN
    )

    # Example usage - Process a specific Jira issue
    issue_key = "PROJ-123"  # Replace with actual issue key
    success = updater.process_jira_issue(issue_key)

    if success:
        print(f"Successfully processed and updated {issue_key}")
    else:
        print(f"Failed to process {issue_key}")

if __name__ == "__main__":
    main()
