# AI Browser Agent Setup Guide

## Quick Setup (5 minutes)

### 1. Prerequisites Check

Before starting, ensure you have:
- **Python 3.8+** installed
- **Chrome or Chromium** browser installed
- **Git** for cloning the repository
- **API key** for Claude or OpenAI

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/ai-browser-agent/ai-browser-agent.git
cd ai-browser-agent

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m ai_browser_agent.main --version
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API key
# Add either:
# CLAUDE_API_KEY=your_claude_key_here
# or
# OPENAI_API_KEY=your_openai_key_here

# Create default configuration
python -m ai_browser_agent.main --create-config

# Validate setup
python -m ai_browser_agent.main --validate-config
```

### 4. First Run

```bash
# Test with a simple task
ai-browser-agent --task "Navigate to google.com and search for 'hello world'"
```

If you see a browser window open and perform the search, you're ready to go!

---

## Detailed Setup Instructions

### System Requirements

#### Operating System
- **Windows 10/11** (64-bit)
- **macOS 10.14+** (Intel or Apple Silicon)
- **Linux** (Ubuntu 18.04+, CentOS 7+, or equivalent)

#### Hardware Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **CPU**: Any modern processor (2+ cores recommended)
- **Network**: Stable internet connection for AI API calls

#### Software Dependencies
- **Python 3.8 - 3.11** (3.9 recommended)
- **Chrome/Chromium 90+** or **Firefox 88+**
- **Git** (for installation from source)

### Step-by-Step Installation

#### Step 1: Install Python

##### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer and check "Add Python to PATH"
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

##### macOS
```bash
# Using Homebrew (recommended)
brew install python@3.9

# Or download from python.org
# Verify installation
python3 --version
pip3 --version
```

##### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
pip3 --version
```

##### Linux (CentOS/RHEL)
```bash
sudo yum install python3 python3-pip
# or for newer versions:
sudo dnf install python3 python3-pip
python3 --version
pip3 --version
```

#### Step 2: Install Browser

##### Chrome (Recommended)
- **Windows/macOS**: Download from [google.com/chrome](https://www.google.com/chrome/)
- **Linux**: 
  ```bash
  # Ubuntu/Debian
  wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
  sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
  sudo apt update
  sudo apt install google-chrome-stable
  
  # CentOS/RHEL
  sudo yum install -y wget
  wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
  sudo yum localinstall google-chrome-stable_current_x86_64.rpm
  ```

##### Chromium (Alternative)
```bash
# Ubuntu/Debian
sudo apt install chromium-browser

# macOS
brew install --cask chromium

# CentOS/RHEL
sudo yum install chromium
```

#### Step 3: Clone Repository

```bash
# Clone the repository
git clone https://github.com/ai-browser-agent/ai-browser-agent.git
cd ai-browser-agent

# Verify files
ls -la
```

You should see:
```
ai_browser_agent/
config/
docs/
tests/
requirements.txt
setup.py
README.md
```

#### Step 4: Set Up Python Environment

##### Option A: Virtual Environment (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

##### Option B: System-wide Installation
```bash
# Install directly (not recommended for production)
pip install -r requirements.txt
```

##### Option C: Development Installation
```bash
# For development with additional tools
pip install -r requirements-dev.txt

# Install in editable mode
pip install -e .
```

#### Step 5: Obtain API Keys

##### Claude API (Recommended)
1. Visit [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)

##### OpenAI API (Alternative)
1. Visit [platform.openai.com](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)

#### Step 6: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

Add your API key:
```env
# For Claude (recommended)
CLAUDE_API_KEY=sk-ant-your-key-here

# For OpenAI (alternative)
OPENAI_API_KEY=sk-your-key-here

# Optional: Set primary model
AI_PRIMARY_MODEL=claude
AI_FALLBACK_MODEL=openai
```

#### Step 7: Create Configuration Files

```bash
# Generate default configuration
python -m ai_browser_agent.main --create-config

# This creates config/app_config.json
```

#### Step 8: Validate Installation

```bash
# Check configuration
python -m ai_browser_agent.main --validate-config
```

Expected output:
```
✓ Configuration loaded and validated successfully
✓ API keys are configured

Configuration Summary:
- Primary AI Model: claude
- Browser: chrome (visible mode)
- Security: confirmations enabled
- Logging: enabled
```

#### Step 9: Test Installation

```bash
# Simple test
ai-browser-agent --task "Navigate to example.com and tell me the page title"
```

You should see:
1. Browser window opens
2. Navigates to example.com
3. Agent reports the page title
4. Task completes successfully

### Advanced Configuration

#### Custom Browser Configuration

Edit `config/app_config.json`:

```json
{
  "browser": {
    "headless": false,
    "window_size": [1920, 1080],
    "timeout": 30,
    "browser_type": "chrome",
    "profile_path": "/path/to/custom/profile",
    "download_directory": "/path/to/downloads",
    "disable_images": false,
    "user_agent": "custom user agent string"
  }
}
```

#### Security Configuration

```json
{
  "security": {
    "require_confirmation_for_payments": true,
    "require_confirmation_for_deletions": true,
    "require_confirmation_for_modifications": true,
    "sensitive_domains": [
      "paypal.com",
      "stripe.com",
      "banking.example.com"
    ],
    "max_task_duration": 3600,
    "audit_log_enabled": true
  }
}
```

#### AI Model Configuration

```json
{
  "ai_model": {
    "primary_model": "claude",
    "fallback_model": "openai",
    "max_tokens": 4000,
    "temperature": 0.7,
    "timeout": 30,
    "max_context_length": 8000
  }
}
```

### Troubleshooting Installation

#### Common Issues

##### 1. Python Version Issues
```bash
# Check Python version
python --version

# If version is < 3.8, install newer Python
# Use python3 instead of python if needed
python3 --version
```

##### 2. Permission Errors
```bash
# On Linux/macOS, use sudo for system-wide installation
sudo pip install -r requirements.txt

# Or use user installation
pip install --user -r requirements.txt
```

##### 3. Browser Not Found
```bash
# Check if Chrome is installed
google-chrome --version
# or
chromium --version

# If not found, install browser first
```

##### 4. API Key Issues
```bash
# Validate API key format
# Claude keys start with: sk-ant-
# OpenAI keys start with: sk-

# Test API connectivity
python -c "
import os
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
print('Claude API: OK')
"
```

##### 5. Network/Firewall Issues
```bash
# Test internet connectivity
curl -I https://api.anthropic.com
curl -I https://api.openai.com

# Check if corporate firewall blocks AI APIs
```

##### 6. Module Import Errors
```bash
# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Platform-Specific Issues

##### Windows
- **Path issues**: Ensure Python and Scripts directories are in PATH
- **Long path names**: Enable long path support in Windows
- **Antivirus**: Whitelist the project directory

##### macOS
- **Xcode tools**: Install with `xcode-select --install`
- **Homebrew**: Use Homebrew for Python installation
- **Permissions**: Use `sudo` carefully, prefer user installations

##### Linux
- **Package managers**: Use system package manager for Python
- **Display**: For headless servers, install Xvfb for virtual display
- **Permissions**: Ensure user has access to browser binaries

### Development Setup

For contributors and developers:

```bash
# Clone with development branch
git clone -b develop https://github.com/ai-browser-agent/ai-browser-agent.git

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run code formatting
black ai_browser_agent/
isort ai_browser_agent/

# Run type checking
mypy ai_browser_agent/
```

### Docker Setup (Optional)

For containerized deployment:

```bash
# Build Docker image
docker build -t ai-browser-agent .

# Run with environment variables
docker run -e CLAUDE_API_KEY=your_key \
           -e BROWSER_HEADLESS=true \
           ai-browser-agent \
           --task "Navigate to example.com"
```

### Next Steps

After successful installation:

1. **Read the User Guide**: Check `docs/USER_GUIDE.md` for usage examples
2. **Try Example Tasks**: Start with simple navigation tasks
3. **Configure Security**: Adjust confirmation settings as needed
4. **Set Up Logging**: Configure log levels and file locations
5. **Explore Advanced Features**: Session persistence, task chaining, etc.

### Getting Help

If you encounter issues:

1. **Check logs**: `tail -f logs/app.log`
2. **Run validation**: `ai-browser-agent --validate-config`
3. **Use debug mode**: `ai-browser-agent --debug --task "simple task"`
4. **Check documentation**: Review user guide and troubleshooting sections
5. **Report issues**: Create GitHub issue with logs and configuration details