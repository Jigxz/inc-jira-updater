import pandas as pd
from sentence_transformers import SentenceTransformer
import duckdb
import numpy as np
import json
from typing import List, Dict, Optional
import os
from datetime import datetime
import openai
from atlassian import Jira
from atlassian.errors import ApiError
from config import Config

class EnhancedJiraCommentUpdater:
    def __init__(self):
        self.db_file = Config.DB_FILE
        self.jira_base_url = Config.JIRA_BASE_URL.rstrip('/')
        self.jira_username = Config.JIRA_USERNAME
        self.jira_api_token = Config.JIRA_API_TOKEN
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.con = duckdb.connect(database=self.db_file, read_only=True)

        # Setup Jira client using Atlassian Python API
        try:
            self.jira = JIRA(
                server=self.jira_base_url,
                basic_auth=(self.jira_username, self.jira_api_token)
            )
            print("✅ Jira client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Jira client: {e}")
            self.jira = None

        # Setup OpenAI if available
        if Config.has_llm_config():
            openai.api_key = Config.OPENAI_API_KEY
            self.llm_available = True
        else:
            self.llm_available = False

    def cosine_similarity(self, a, b):
        """Calculate cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def search_similar_incidents(self, jira_description: str, threshold: float = None, limit: int = None) -> List[Dict]:
        """Search for similar incidents based on Jira description"""
        if threshold is None:
            threshold = Config.SIMILARITY_THRESHOLD
        if limit is None:
            limit = Config.MAX_SIMILAR_INCIDENTS

        # Generate embedding for the Jira description
        query_vector = self.model.encode([jira_description])[0]

        # Create similarity function in DuckDB
        self.con.create_function("cosine_similarity", self.cosine_similarity, ["FLOAT[]", "FLOAT[]"], float)

        # Search query
        sql_query = """
        SELECT INC, "Short Desc", "Created Date", "Updated Date", Assignee, "Group", "Created By", "Updated By ",
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

    def analyze_with_llm(self, jira_description: str, similar_incidents: List[Dict]) -> Dict:
        """Analyze incidents using LLM for better insights"""
        if not self.llm_available or not similar_incidents:
            return self.analyze_historical_patterns(similar_incidents, jira_description)

        try:
            # Prepare context for LLM
            incidents_text = ""
            for incident in similar_incidents:
                incidents_text += f"""
INC-{incident['INC']}: {incident['Short Desc']}
- Created: {incident['Created Date']}, Updated: {incident['Updated Date']}
- Assignee: {incident['Assignee']}, Group: {incident['Group']}
- Created by: {incident['Created By']}, Updated by: {incident['Updated By']}
"""

            prompt = f"""
You are an expert incident analyst. Analyze the following incident description and historical similar incidents to provide insights and recommendations.

Current Incident Description:
{jira_description}

Historical Similar Incidents:
{incidents_text}

Based on this information, provide:
1. Key patterns and similarities you observe
2. Most likely root causes based on historical data
3. Recommended actions and next steps
4. Confidence level (0-1) in your analysis
5. Suggested assignee or team based on who handled similar incidents

Format your response as JSON with the following structure:
{{
    "patterns": ["pattern1", "pattern2"],
    "root_causes": ["cause1", "cause2"],
    "recommendations": ["action1", "action2"],
    "confidence_score": 0.8,
    "suggested_assignee": "team_name",
    "suggested_group": "group_name"
}}
"""

            response = openai.ChatCompletion.create(
                model=Config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=Config.LLM_MAX_TOKENS,
                temperature=0.3
            )

            llm_result = response.choices[0].message.content.strip()

            # Try to parse JSON response
            try:
                parsed_result = json.loads(llm_result)
                return parsed_result
            except json.JSONDecodeError:
                # If LLM didn't return valid JSON, fall back to rule-based analysis
                print("LLM response was not valid JSON, falling back to rule-based analysis")
                return self.analyze_historical_patterns(similar_incidents, jira_description)

        except Exception as e:
            print(f"Error with LLM analysis: {e}")
            return self.analyze_historical_patterns(similar_incidents, jira_description)

    def analyze_historical_patterns(self, similar_incidents: List[Dict], jira_description: str) -> Dict:
        """Analyze historical patterns using rule-based approach"""
        analysis = {
            'patterns': [],
            'root_causes': [],
            'recommendations': [],
            'confidence_score': 0.0,
            'suggested_assignee': 'Unknown',
            'suggested_group': 'Unknown'
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

        analysis['suggested_assignee'] = most_common_assignee
        analysis['suggested_group'] = most_common_group

        # Generate patterns
        analysis['patterns'] = [
            f"Most incidents handled by: {most_common_assignee}",
            f"Most incidents in group: {most_common_group}",
            f"Total similar incidents found: {len(similar_incidents)}"
        ]

        # Generate recommendations
        if len(similar_incidents) >= Config.MIN_INCIDENTS_FOR_ANALYSIS:
            analysis['recommendations'] = [
                f"Assign to {most_common_assignee} as they have handled similar incidents",
                f"Consider involving {most_common_group} team",
                "Review past solutions from similar incidents",
                "Check for common root causes in historical data"
            ]
            analysis['confidence_score'] = min(0.8, len(similar_incidents) * 0.15)
        else:
            analysis['recommendations'] = [
                "Limited historical data available",
                "Consider broader search criteria",
                "Manual review recommended"
            ]
            analysis['confidence_score'] = 0.3

        return analysis

    def get_jira_issue(self, issue_key: str) -> Optional[Dict]:
        """Get Jira issue details using Atlassian Python API"""
        if not self.jira:
            print("❌ Jira client not initialized")
            return None

        try:
            issue = self.jira.get_issue(issue_key)
            # Convert JIRA issue object to dictionary format
            return {
                'key': issue.get('key'),
                'fields': {
                    'summary': issue.get('fields', {}).get('summary', ''),
                    'description': issue.get('fields', {}).get('description', ''),
                    'status': issue.get('fields', {}).get('status', {}).get('name', 'Unknown'),
                    'assignee': issue.get('fields', {}).get('assignee', {}).get('displayName', None),
                    'creator': issue.get('fields', {}).get('creator', {}).get('displayName', 'Unknown'),
                    'created': issue.get('fields', {}).get('created', ''),
                    'updated': issue.get('fields', {}).get('updated', '')
                }
            }
        except ApiError as e:
            print(f"Error fetching Jira issue {issue_key}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching Jira issue {issue_key}: {e}")
            return None

    def update_jira_comment(self, issue_key: str, comment: str) -> bool:
        """Update Jira issue with a comment using Atlassian Python API"""
        if not self.jira:
            print("❌ Jira client not initialized")
            return False

        try:
            self.jira.create_comment(issue_key, comment)
            print(f"✅ Successfully added comment to {issue_key}")
            return True
        except ApiError as e:
            print(f"❌ Error updating Jira comment for {issue_key}: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error updating Jira comment for {issue_key}: {e}")
            return False

    def generate_analysis_comment(self, jira_description: str, similar_incidents: List[Dict], analysis: Dict) -> str:
        """Generate a comprehensive comment for Jira based on analysis"""

        comment = f"""**Automated Incident Analysis Report**

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
"""
        for pattern in analysis['patterns']:
            comment += f"• {pattern}\n"

        comment += f"""
**Root Causes (Identified):**
"""
        for cause in analysis.get('root_causes', []):
            comment += f"• {cause}\n"

        if not analysis.get('root_causes'):
            comment += "• No specific root causes identified from historical data\n"

        comment += f"""
**Recommended Actions:**
"""
        for recommendation in analysis['recommendations']:
            comment += f"• {recommendation}\n"

        comment += f"""
**Suggested Assignment:**
• Assignee: {analysis.get('suggested_assignee', 'TBD')}
• Group: {analysis.get('suggested_group', 'TBD')}

**Analysis Confidence:** {analysis.get('confidence_score', 0):.2f}

---
*This analysis was generated automatically using historical incident data and AI-powered pattern recognition.*
"""
        return comment

    def process_jira_issue(self, issue_key: str, threshold: float = None) -> bool:
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

        # Perform analysis (with LLM if available)
        analysis = self.analyze_with_llm(description, similar_incidents)

        # Generate and add comment
        comment = self.generate_analysis_comment(description, similar_incidents, analysis)
        success = self.update_jira_comment(issue_key, comment)

        return success

    def batch_process_issues(self, issue_keys: List[str]) -> Dict[str, bool]:
        """Process multiple Jira issues and return results"""
        results = {}

        for issue_key in issue_keys:
            try:
                success = self.process_jira_issue(issue_key)
                results[issue_key] = success
            except Exception as e:
                print(f"Error processing {issue_key}: {e}")
                results[issue_key] = False

        return results

def main():
    """Main function for command line usage"""
    if not Config.validate_config():
        return

    updater = EnhancedJiraCommentUpdater()

    # Example usage - Process a specific Jira issue
    issue_key = "PROJ-123"  # Replace with actual issue key
    success = updater.process_jira_issue(issue_key)

    if success:
        print(f"Successfully processed and updated {issue_key}")
    else:
        print(f"Failed to process {issue_key}")

if __name__ == "__main__":
    main()
