#!/usr/bin/env python3
"""
Test script for Jira Comment Updater
This script tests the core functionality without requiring actual Jira credentials
"""

import sys
import os
import json
from unittest.mock import Mock, patch
from jira_updater_enhanced import EnhancedJiraCommentUpdater
from config import Config
from atlassian import Jira

def test_vector_search():
    """Test the vector search functionality"""
    print("🧪 Testing vector search functionality...")

    try:
        # Mock the configuration and Jira client to avoid needing real credentials
        with patch.object(Config, 'validate_config', return_value=True), \
             patch.object(Config, 'has_llm_config', return_value=False), \
             patch('jira_updater_enhanced.Jira') as mock_jira:

            mock_jira_instance = Mock()
            mock_jira.return_value = mock_jira_instance

            updater = EnhancedJiraCommentUpdater()

            # Test search with sample text
            test_description = "UI is not loading for application"
            similar_incidents = updater.search_similar_incidents(test_description, threshold=0.1)

            print(f"✅ Vector search successful. Found {len(similar_incidents)} similar incidents")

            if similar_incidents:
                print("Sample result:")
                incident = similar_incidents[0]
                print(f"  - INC-{incident['INC']}: {incident['Short Desc']}")
                print(f"  - Similarity: {incident['similarity']:.2f}")

            return True

    except Exception as e:
        print(f"❌ Vector search test failed: {e}")
        return False

def test_analysis_generation():
    """Test the analysis generation functionality"""
    print("🧪 Testing analysis generation...")

    try:
        with patch.object(Config, 'validate_config', return_value=True), \
             patch.object(Config, 'has_llm_config', return_value=False):

            updater = EnhancedJiraCommentUpdater()

            # Mock some similar incidents
            mock_incidents = [
                {
                    'INC': '1232325',
                    'Short Desc': 'UI is not loading for scapper application',
                    'Created Date': '2025-01-05',
                    'Updated Date': '2025-10-09',
                    'Assignee': 'jack',
                    'Group': 'app-dev',
                    'Created By': 'RR',
                    'Updated By': 'jack',
                    'similarity': 0.85
                },
                {
                    'INC': '1232321',
                    'Short Desc': 'the data is not loading for scappper application',
                    'Created Date': '2025-01-01',
                    'Updated Date': '2025-01-09',
                    'Assignee': 'xyz',
                    'Group': 'app-dev',
                    'Created By': 'abc',
                    'Updated By': 'xyz',
                    'similarity': 0.72
                }
            ]

            test_description = "UI components are not rendering properly in the application"
            analysis = updater.analyze_historical_patterns(mock_incidents, test_description)

            print("✅ Analysis generation successful")
            print(f"  - Patterns found: {len(analysis['patterns'])}")
            print(f"  - Recommendations: {len(analysis['recommendations'])}")
            print(f"  - Confidence score: {analysis['confidence_score']:.2f}")
            print(f"  - Suggested assignee: {analysis['suggested_assignee']}")

            return True

    except Exception as e:
        print(f"❌ Analysis generation test failed: {e}")
        return False

def test_comment_generation():
    """Test the comment generation functionality"""
    print("🧪 Testing comment generation...")

    try:
        with patch.object(Config, 'validate_config', return_value=True):

            updater = EnhancedJiraCommentUpdater()

            # Mock analysis and incidents
            mock_incidents = [
                {
                    'INC': '1232325',
                    'Short Desc': 'UI is not loading for scapper application',
                    'Created Date': '2025-01-05',
                    'Updated Date': '2025-10-09',
                    'Assignee': 'jack',
                    'Group': 'app-dev',
                    'Created By': 'RR',
                    'Updated By': 'jack',
                    'similarity': 0.85
                }
            ]

            mock_analysis = {
                'patterns': [
                    'Most incidents handled by: jack',
                    'Most incidents in group: app-dev',
                    'Total similar incidents found: 1'
                ],
                'root_causes': ['UI rendering issue', 'Component loading problem'],
                'recommendations': [
                    'Assign to jack as they have handled similar incidents',
                    'Consider involving app-dev team',
                    'Review past solutions from similar incidents'
                ],
                'confidence_score': 0.85,
                'suggested_assignee': 'jack',
                'suggested_group': 'app-dev'
            }

            test_description = "UI components are not rendering properly"
            comment = updater.generate_analysis_comment(test_description, mock_incidents, mock_analysis)

            print("✅ Comment generation successful")
            print(f"  - Comment length: {len(comment)} characters")
            print(f"  - Contains original description: {'Original Description' in comment}")
            print(f"  - Contains recommendations: {'Recommended Actions' in comment}")
            print(f"  - Contains confidence score: {'Confidence Score' in comment}")

            # Save sample comment to file for review
            with open('sample_comment.txt', 'w') as f:
                f.write(comment)
            print("  - Sample comment saved to sample_comment.txt")

            return True

    except Exception as e:
        print(f"❌ Comment generation test failed: {e}")
        return False

def test_configuration():
    """Test configuration validation"""
    print("🧪 Testing configuration...")

    try:
        # Test with default config (should fail validation)
        is_valid = Config.validate_config()
        print(f"✅ Configuration validation works (returns: {is_valid})")

        # Test LLM availability
        llm_available = Config.has_llm_config()
        print(f"✅ LLM availability check works (returns: {llm_available})")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("🧪 Testing database connection...")

    try:
        # This should work since we have the DuckDB file
        from duckdb import connect

        con = connect(Config.DB_FILE, read_only=True)
        result = con.execute("SELECT COUNT(*) FROM incidents").fetchone()
        count = result[0]

        print(f"✅ Database connection successful. Found {count} incidents in database")

        con.close()
        return True

    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("🚀 Starting Jira Comment Updater Tests")
    print("=" * 50)

    tests = [
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("Vector Search", test_vector_search),
        ("Analysis Generation", test_analysis_generation),
        ("Comment Generation", test_comment_generation)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test PASSED")
        else:
            print(f"❌ {test_name} test FAILED")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The application is ready to use.")
        print("\nNext steps:")
        print("1. Update config.py with your Jira credentials")
        print("2. Set up OpenAI API key (optional) for enhanced analysis")
        print("3. Run: python web_interface.py to start the web interface")
        print("4. Or run: python jira_updater_enhanced.py to use command line")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
