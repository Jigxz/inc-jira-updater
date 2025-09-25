# 🔍 Jira Comment Updater

An intelligent application that automatically analyzes Jira issues and adds comprehensive analysis comments based on historical incident data. The system uses vector embeddings and AI-powered analysis to find similar incidents and provide actionable insights.

## ✨ Features

- **🗂️ Vector-based Incident Search**: Uses sentence transformers to find semantically similar incidents
- **🤖 AI-Powered Analysis**: Leverages LLM (OpenAI) for enhanced pattern recognition and recommendations
- **📝 Automated Jira Comments**: Automatically adds comprehensive analysis comments to Jira issues
- **📊 Historical Pattern Analysis**: Identifies common assignees, groups, and resolution patterns
- **🌐 Web Interface**: User-friendly web interface for easy operation
- **⚡ Batch Processing**: Process multiple Jira issues simultaneously
- **⚙️ Configurable Thresholds**: Adjust similarity thresholds for different use cases
- **🛡️ Robust Error Handling**: Comprehensive error handling and logging
- **🧪 Comprehensive Testing**: Full test suite included

## 🏗️ Architecture

The application consists of several key components:

1. **Data Processing** (`file_scraper.py`): Scrapes XLS incident data and stores in DuckDB with vector embeddings
2. **Core Engine** (`jira_updater_enhanced.py`): Main analysis and Jira integration logic using Atlassian Python API
3. **Configuration** (`config.py`): Centralized configuration management
4. **Web Interface** (`web_interface.py`): Flask-based web application
5. **Testing** (`test_jira_updater.py`): Comprehensive test suite

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: At least 4GB RAM (8GB recommended for LLM features)
- **Storage**: 2GB free space for dependencies and data

### Required Accounts
- **Jira Account**: Valid Jira account with API access
- **OpenAI Account** (Optional): For enhanced AI analysis features

## 🚀 Installation

### Step 1: Clone or Download
```bash
# If using git (recommended)
git clone https://github.com/your-repo/jira-comment-updater.git
cd jira-comment-updater

# Or download and extract the files to a directory
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv jira_env
jira_env\Scripts\activate

# macOS/Linux
python -m venv jira_env
source jira_env/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python -c "import pandas, duckdb, sentence_transformers, atlassian; print('✅ All dependencies installed successfully')"
```

## ⚙️ Configuration

### Step 1: Jira Configuration
Edit `config.py` and update the following:

```python
class Config:
    # Jira Configuration
    JIRA_BASE_URL = "https://your-domain.atlassian.net"  # Your Jira instance URL
    JIRA_USERNAME = "your-email@example.com"             # Your Jira email
    JIRA_API_TOKEN = "your-api-token-here"               # Your Jira API token

    # Database Configuration
    DB_FILE = "local_vector_db.duckdb"
    INCIDENTS_TABLE = "incidents"

    # Analysis Configuration
    SIMILARITY_THRESHOLD = 0.3      # Minimum similarity score (0.0-1.0)
    MAX_SIMILAR_INCIDENTS = 5       # Maximum similar incidents to retrieve
    MIN_INCIDENTS_FOR_ANALYSIS = 3  # Minimum incidents for pattern analysis

    # LLM Configuration (Optional)
    OPENAI_API_KEY = "your-openai-api-key"  # Set as environment variable
    LLM_MODEL = "gpt-3.5-turbo"
    LLM_MAX_TOKENS = 1000

    # File Paths
    EXCEL_FILE_PATH = "INC.xlsx"
```

### Step 2: Get Jira API Token
1. Log into your Jira instance
2. Go to **Account Settings** → **Security**
3. Click **Create and manage API tokens**
4. Click **Create API token**
5. Copy the token and paste it in `config.py`

### Step 3: OpenAI Setup (Optional)
1. Create account at [OpenAI Platform](https://platform.openai.com)
2. Go to **API Keys** section
3. Click **Create new secret key**
4. Copy the API key
5. Set environment variable:
   ```bash
   # Windows
   set OPENAI_API_KEY=your-api-key-here

   # macOS/Linux
   export OPENAI_API_KEY=your-api-key-here
   ```

### Step 4: Prepare Incident Data
1. Ensure `INC.xlsx` file is in the project directory
2. The file should contain columns: INC, Short Desc, Created Date, Updated Date, Assignee, Group, Created By, Updated By
3. The application will automatically process this data and create vector embeddings

## 🧪 Testing

### Run Complete Test Suite
```bash
python test_jira_updater.py
```

Expected output:
```
🚀 Starting Jira Comment Updater Tests
==================================================
✅ Configuration test PASSED
✅ Database Connection test PASSED
✅ Vector Search test PASSED
✅ Analysis Generation test PASSED
✅ Comment Generation test PASSED
==================================================
📊 Test Results: 5/5 tests passed
🎉 All tests passed! The application is ready to use.
```

### Individual Test Components
```bash
# Test configuration only
python -c "from config import Config; print('Config valid:', Config.validate_config())"

# Test database connection
python -c "from duckdb import connect; from config import Config; con = connect(Config.DB_FILE); print('DB connected:', con is not None)"

# Test Jira connection (requires valid credentials)
python -c "from atlassian import Jira; from config import Config; jira = Jira(server=Config.JIRA_BASE_URL, basic_auth=(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)); print('Jira connected:', jira is not None)"
```

## 🎯 Usage

### Method 1: Web Interface (Recommended)

#### Start Web Interface
```bash
python web_interface.py
```

#### Access Application
1. Open browser and go to: `http://localhost:5000`
2. Verify configuration status at the top
3. Use one of the three tabs:

#### Single Issue Processing
1. Click **"Single Issue"** tab
2. Enter Jira issue key (e.g., `PROJ-123`)
3. Adjust similarity threshold (0.0-1.0, default: 0.3)
4. Click **"Process Issue"**
5. View results and status

#### Batch Processing
1. Click **"Batch Processing"** tab
2. Enter multiple issue keys:
   ```
   PROJ-123
   PROJ-124
   PROJ-125
   ```
   Or comma-separated: `PROJ-123, PROJ-124, PROJ-125`
3. Set similarity threshold
4. Click **"Process All Issues"**
5. View detailed results for each issue

#### Test Connection
1. Click **"Test Connection"** tab
2. Click **"Test Connection"** button
3. Verify Jira connectivity

### Method 2: Command Line

#### Process Single Issue
```bash
python jira_updater_enhanced.py
```

#### Process with Custom Threshold
```python
from jira_updater_enhanced import EnhancedJiraCommentUpdater
from config import Config

updater = EnhancedJiraCommentUpdater()
success = updater.process_jira_issue("PROJ-123", threshold=0.5)
print(f"Issue processed: {success}")
```

#### Batch Process Multiple Issues
```python
issue_keys = ["PROJ-123", "PROJ-124", "PROJ-125"]
results = updater.batch_process_issues(issue_keys)

for issue_key, success in results.items():
    print(f"{issue_key}: {'✅ Success' if success else '❌ Failed'}")
```

### Method 3: Python API

```python
from jira_updater_enhanced import EnhancedJiraCommentUpdater

# Initialize
updater = EnhancedJiraCommentUpdater()

# Search for similar incidents
similar_incidents = updater.search_similar_incidents(
    "UI components are not loading properly",
    threshold=0.3,
    limit=5
)

# Analyze patterns
analysis = updater.analyze_historical_patterns(similar_incidents, "UI issue description")

# Generate comment
comment = updater.generate_analysis_comment("UI issue", similar_incidents, analysis)

# Add to Jira issue
success = updater.update_jira_comment("PROJ-123", comment)
```

## 📊 How It Works

### 1. Incident Matching Process
1. **Text Embedding**: Converts Jira issue description to vector using sentence transformers
2. **Similarity Search**: Queries DuckDB for incidents with similar vector embeddings
3. **Threshold Filtering**: Applies similarity threshold to filter relevant results
4. **Ranking**: Returns top N most similar incidents

### 2. Pattern Analysis
1. **Assignee Analysis**: Identifies who typically handles similar issues
2. **Group Analysis**: Determines which teams are usually involved
3. **Temporal Analysis**: Analyzes timing patterns of similar incidents
4. **Resolution Patterns**: Studies common resolution approaches

### 3. AI Enhancement (Optional)
When OpenAI is configured:
1. **Advanced Pattern Recognition**: Uses LLM for sophisticated analysis
2. **Root Cause Identification**: Identifies potential underlying causes
3. **Detailed Recommendations**: Generates specific, actionable recommendations
4. **Confidence Scoring**: Provides confidence levels for analysis

### 4. Comment Generation
Creates comprehensive comments including:
- Original issue description
- List of similar historical incidents with metadata
- Analysis summary and identified patterns
- Root causes (if identified)
- Recommended actions and next steps
- Suggested assignee and group
- Confidence score
- Automated generation notice

## 🔧 Advanced Configuration

### Custom Similarity Thresholds
```python
# In config.py
SIMILARITY_THRESHOLD = 0.5  # Higher = more strict matching
MAX_SIMILAR_INCIDENTS = 10  # Increase for more comprehensive analysis
MIN_INCIDENTS_FOR_ANALYSIS = 2  # Lower for analysis with fewer incidents
```

### LLM Configuration
```python
# In config.py
LLM_MODEL = "gpt-4"           # Use GPT-4 for better analysis
LLM_MAX_TOKENS = 2000         # Increase for more detailed responses
LLM_TEMPERATURE = 0.1         # Lower for more consistent results
```

### Database Configuration
```python
# In config.py
DB_FILE = "custom_database.duckdb"  # Custom database location
INCIDENTS_TABLE = "custom_incidents"  # Custom table name
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Configuration Errors
**Problem**: Configuration validation fails
**Solution**:
```bash
# Check configuration
python -c "from config import Config; Config.validate_config()"

# Verify Jira credentials
python -c "from atlassian import Jira; from config import Config; jira = Jira(server=Config.JIRA_BASE_URL, basic_auth=(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)); print('Connected:', jira.server_info())"
```

#### 2. Database Issues
**Problem**: Cannot connect to database or column errors
**Solution**:
```bash
# Check database exists
python -c "import os; from config import Config; print('DB exists:', os.path.exists(Config.DB_FILE))"

# Verify table structure
python -c "from duckdb import connect; from config import Config; con = connect(Config.DB_FILE); print(con.execute('PRAGMA table_info(incidents)').fetchall())"
```

#### 3. Dependency Issues
**Problem**: Import errors or missing modules
**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check specific module
python -c "import atlassian, duckdb, sentence_transformers; print('All modules imported successfully')"
```

#### 4. Jira Connection Issues
**Problem**: Cannot connect to Jira instance
**Solution**:
```bash
# Test connection manually
python -c "
from atlassian import Jira
from config import Config
try:
    jira = Jira(server=Config.JIRA_BASE_URL, basic_auth=(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN))
    print('✅ Connected to:', jira.server_info().get('serverTitle'))
except Exception as e:
    print('❌ Connection failed:', e)
"
```

#### 5. Vector Search Issues
**Problem**: No similar incidents found
**Solution**:
```bash
# Lower similarity threshold
python -c "
from jira_updater_enhanced import EnhancedJiraCommentUpdater
updater = EnhancedJiraCommentUpdater()
results = updater.search_similar_incidents('your issue description', threshold=0.1)
print(f'Found {len(results)} incidents with lower threshold')
"
```

### Debug Mode
Enable detailed logging by modifying `config.py`:
```python
LOG_LEVEL = "DEBUG"
```

### Performance Optimization
For large datasets:
1. Increase system memory
2. Use SSD storage for database
3. Consider using GPU for vector operations
4. Optimize similarity thresholds

## 📁 Project Structure

```
jira-comment-updater/
├── 📄 README.md                    # This file
├── 📄 requirements.txt             # Python dependencies
├── 📄 config.py                    # Configuration settings
├── 📄 jira_updater_enhanced.py     # Main application
├── 📄 web_interface.py             # Flask web interface
├── 📄 test_jira_updater.py         # Test suite
├── 📄 file_scraper.py              # Data processing utilities
├── 📄 INC.xlsx                     # Incident data file
├── 📄 local_vector_db.duckdb       # Vector database
├── 📁 templates/
│   └── 📄 index.html               # Web interface template
└── 📄 sample_comment.txt           # Example generated comment
```

## 🔒 Security Considerations

### API Token Security
- Store API tokens securely (environment variables recommended)
- Never commit API tokens to version control
- Use read-only tokens when possible
- Rotate tokens regularly

### Data Protection
- Incident data may contain sensitive information
- Ensure proper access controls on database files
- Consider data anonymization for testing
- Implement proper backup strategies

### Network Security
- Use HTTPS for all Jira connections
- Validate SSL certificates
- Implement rate limiting for production use
- Monitor API usage and quotas

## 🚨 Rate Limits and Quotas

### Jira API Limits
- **Jira Cloud**: 1000 requests per hour for basic authentication
- **Jira Server**: Varies by instance configuration
- **Best Practice**: Implement exponential backoff for retries

### OpenAI API Limits
- **Token Limits**: Vary by model and subscription
- **Rate Limits**: 60 requests per minute for GPT-3.5-turbo
- **Best Practice**: Cache results and implement request batching

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd jira-comment-updater

# Create development environment
python -m venv dev_env
source dev_env/bin/activate  # macOS/Linux
# dev_env\Scripts\activate   # Windows

# Install in development mode
pip install -e .
```

### Running Tests
```bash
# Run all tests
python test_jira_updater.py

# Run with coverage
pip install pytest-cov
pytest --cov=jira_updater_enhanced test_jira_updater.py
```

### Code Style
```bash
# Install code quality tools
pip install black flake8 isort

# Format code
black .
isort .
flake8 .
```

## 📈 Monitoring and Analytics

### Application Metrics
- Track processing success/failure rates
- Monitor average processing time per issue
- Log similarity scores and confidence levels
- Monitor API usage and rate limits

### Performance Monitoring
```python
import time
import logging

# Add timing to critical functions
start_time = time.time()
result = updater.process_jira_issue(issue_key)
processing_time = time.time() - start_time

logging.info(f"Processed {issue_key} in {processing_time:.2f}s")
```

## 🔄 Updates and Maintenance

### Regular Updates
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update incident data
python -c "
from file_scraper import DuckDBFileScraper
scraper = DuckDBFileScraper('local_vector_db.duckdb', 'INC.xlsx', 'Short Desc')
scraper.setup_database()
"
```

### Backup Strategy
```bash
# Backup database
import shutil
from config import Config
shutil.copy(Config.DB_FILE, f"{Config.DB_FILE}.backup")

# Backup configuration (without sensitive data)
import json
config_backup = {
    'similarity_threshold': Config.SIMILARITY_THRESHOLD,
    'max_similar_incidents': Config.MAX_SIMILAR_INCIDENTS,
    'min_incidents_for_analysis': Config.MIN_INCIDENTS_FOR_ANALYSIS
}
with open('config_backup.json', 'w') as f:
    json.dump(config_backup, f)
```

## 📞 Support and Help

### Getting Help
1. Check the troubleshooting section above
2. Run the test suite to identify issues
3. Review application logs
4. Check Jira and OpenAI status pages

### Common Questions

**Q: How do I improve analysis accuracy?**
A: Lower the similarity threshold and ensure your incident data has detailed descriptions.

**Q: Can I use this with Jira Server?**
A: Yes, update the JIRA_BASE_URL to your server URL and ensure API access is enabled.

**Q: How do I handle large datasets?**
A: Consider using GPU acceleration for vector operations and optimize database queries.

**Q: Can I customize the comment format?**
A: Yes, modify the `generate_analysis_comment` method in `jira_updater_enhanced.py`.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Atlassian** for the Jira API and Python SDK
- **OpenAI** for the language model capabilities
- **Sentence Transformers** for the embedding models
- **DuckDB** for the efficient vector database

---

**Built with ❤️ for efficient incident management and analysis**

For issues, questions, or contributions, please refer to the project repository or contact the development team.
