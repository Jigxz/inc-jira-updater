"""
Configuration file for Jira Comment Updater
Update these settings with your actual credentials and preferences
"""

import os
from typing import Optional

class Config:
    # Database Configuration
    DB_FILE = "local_vector_db.duckdb"
    INCIDENTS_TABLE = "incidents"

    # Jira Configuration
    JIRA_BASE_URL = "https://your-domain.atlassian.net"  # Replace with your Jira instance URL
    JIRA_USERNAME = "your-email@example.com"  # Replace with your Jira email
    JIRA_API_TOKEN = "your-api-token"  # Replace with your Jira API token

    # Analysis Configuration
    SIMILARITY_THRESHOLD = 0.3
    MAX_SIMILAR_INCIDENTS = 5
    MIN_INCIDENTS_FOR_ANALYSIS = 3

    # LLM Configuration (Optional - for enhanced analysis)
    # Set these if you want to use LLM for better analysis
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # Set your OpenAI API key as environment variable
    LLM_MODEL = "gpt-3.5-turbo"
    LLM_MAX_TOKENS = 1000

    # File Paths
    EXCEL_FILE_PATH = "INC.xlsx"

    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_FILE = "jira_updater.log"

    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is set"""
        required_fields = [
            cls.JIRA_BASE_URL,
            cls.JIRA_USERNAME,
            cls.JIRA_API_TOKEN
        ]

        missing_fields = []
        for field in required_fields:
            if field in ["your-domain.atlassian.net", "your-email@example.com", "your-api-token"]:
                missing_fields.append(field)

        if missing_fields:
            print("⚠️  Configuration Warning:")
            print("The following fields need to be updated in config.py:")
            for field in missing_fields:
                print(f"  - {field}")
            print("\nPlease update these values before running the application.")
            return False

        return True

    @classmethod
    def get_jira_credentials(cls) -> tuple:
        """Get Jira credentials as tuple for requests"""
        return (cls.JIRA_USERNAME, cls.JIRA_API_TOKEN)

    @classmethod
    def has_llm_config(cls) -> bool:
        """Check if LLM configuration is available"""
        return bool(cls.OPENAI_API_KEY and cls.OPENAI_API_KEY != "")

# Example environment variables setup:
# export OPENAI_API_KEY="your-openai-api-key-here"
