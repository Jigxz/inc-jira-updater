from flask import Flask, request, render_template, jsonify
from jira_updater_enhanced import EnhancedJiraCommentUpdater
from config import Config
import json
import os
from atlassian import Jira
from atlassian.errors import ApiError

app = Flask(__name__)

# Initialize the updater
updater = None

def get_updater():
    global updater
    if updater is None:
        if Config.validate_config():
            updater = EnhancedJiraCommentUpdater()
        else:
            updater = None
    return updater

@app.route('/')
def index():
    """Main page with the web interface"""
    return render_template('index.html')

@app.route('/process_issue', methods=['POST'])
def process_issue():
    """Process a single Jira issue"""
    if not get_updater():
        return jsonify({'error': 'Configuration not properly set up'}), 400

    issue_key = request.form.get('issue_key')
    threshold = request.form.get('threshold', Config.SIMILARITY_THRESHOLD)

    try:
        threshold = float(threshold)
    except ValueError:
        threshold = Config.SIMILARITY_THRESHOLD

    if not issue_key:
        return jsonify({'error': 'Issue key is required'}), 400

    try:
        success = updater.process_jira_issue(issue_key, threshold)
        return jsonify({
            'success': success,
            'issue_key': issue_key,
            'message': 'Issue processed successfully' if success else 'Failed to process issue'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/batch_process', methods=['POST'])
def batch_process():
    """Process multiple Jira issues"""
    if not get_updater():
        return jsonify({'error': 'Configuration not properly set up'}), 400

    issue_keys_text = request.form.get('issue_keys', '')
    threshold = request.form.get('threshold', Config.SIMILARITY_THRESHOLD)

    try:
        threshold = float(threshold)
    except ValueError:
        threshold = Config.SIMILARITY_THRESHOLD

    if not issue_keys_text:
        return jsonify({'error': 'Issue keys are required'}), 400

    # Parse issue keys (one per line or comma separated)
    issue_keys = []
    for line in issue_keys_text.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            # Split by comma and clean up
            keys = [key.strip() for key in line.split(',') if key.strip()]
            issue_keys.extend(keys)

    if not issue_keys:
        return jsonify({'error': 'No valid issue keys found'}), 400

    try:
        results = updater.batch_process_issues(issue_keys)
        return jsonify({
            'results': results,
            'total_processed': len(results),
            'successful': sum(1 for r in results.values() if r),
            'failed': sum(1 for r in results.values() if not r)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_connection', methods=['GET'])
def test_connection():
    """Test Jira connection using Atlassian Python API"""
    if not get_updater():
        return jsonify({'error': 'Configuration not properly set up'}), 400

    try:
        # Test the Jira connection by trying to get server info
        if updater.jira:
            # Try to get server information to test connection
            server_info = updater.jira.server_info()
            return jsonify({
                'connection': 'ok',
                'message': f'Jira connection successful - Server: {server_info.get("serverTitle", "Unknown")}'
            })
        else:
            return jsonify({'error': 'Jira client not initialized'}), 500
    except ApiError as e:
        return jsonify({'error': f'Jira connection failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Connection test failed: {str(e)}'}), 500

@app.route('/config_status', methods=['GET'])
def config_status():
    """Get configuration status"""
    config_valid = Config.validate_config()
    llm_available = Config.has_llm_config()

    return jsonify({
        'config_valid': config_valid,
        'llm_available': llm_available,
        'db_file': Config.DB_FILE,
        'jira_base_url': Config.JIRA_BASE_URL
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
