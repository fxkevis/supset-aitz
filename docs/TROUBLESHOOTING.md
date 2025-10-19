# AI Browser Agent Troubleshooting Guide

## Quick Diagnostics

### Health Check Commands

Run these commands to quickly diagnose common issues:

```bash
# 1. Check installation
ai-browser-agent --version

# 2. Validate configuration
ai-browser-agent --validate-config

# 3. Test browser connectivity
python -c "from selenium import webdriver; driver = webdriver.Chrome(); driver.quit(); print('Browser: OK')"

# 4. Test AI API connectivity
python scripts/validate_config.py

# 5. Check log files
tail -20 logs/app.log
```

### Common Error Patterns

| Error Message | Quick Fix |
|---------------|-----------|
| `No API key found` | Add `CLAUDE_API_KEY` or `OPENAI_API_KEY` to `.env` |
| `Browser failed to start` | Install Chrome/Chromium browser |
| `Element not found` | Increase timeout or use debug mode |
| `Token limit exceeded` | Reduce task complexity or increase token limit |
| `Permission denied` | Check file permissions or run with appropriate privileges |

---

## Installation Issues

### Python Version Problems

#### Issue: "Python version not supported"
```
ERROR: Python 3.7 is not supported. Requires Python 3.8+
```

**Solutions:**
```bash
# Check current version
python --version

# Install newer Python (Ubuntu/Debian)
sudo apt update
sudo apt install python3.9 python3.9-pip
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1

# Install newer Python (macOS with Homebrew)
brew install python@3.9
brew link python@3.9

# Install newer Python (Windows)
# Download from python.org and install
```

#### Issue: "python command not found"
```
bash: python: command not found
```

**Solutions:**
```bash
# Try python3 instead
python3 --version

# Create alias (Linux/macOS)
echo "alias python=python3" >> ~/.bashrc
source ~/.bashrc

# Or use python3 throughout
python3 -m ai_browser_agent.main --version
```

### Dependency Installation Issues

#### Issue: "pip install fails with permission errors"
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solutions:**
```bash
# Option 1: User installation
pip install --user -r requirements.txt

# Option 2: Virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
pip install -r requirements.txt

# Option 3: System installation (use carefully)
sudo pip install -r requirements.txt
```

#### Issue: "Package conflicts or version errors"
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed
```

**Solutions:**
```bash
# Clean installation
pip uninstall -r requirements.txt -y
pip cache purge
pip install -r requirements.txt

# Use fresh virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Browser Installation Issues

#### Issue: "ChromeDriver not found"
```
selenium.common.exceptions.WebDriverException: 'chromedriver' executable needs to be in PATH
```

**Solutions:**
```bash
# The agent uses webdriver-manager to auto-download drivers
# If this fails, manually install:

# Ubuntu/Debian
sudo apt update
sudo apt install chromium-chromedriver

# macOS
brew install chromedriver

# Or download manually from:
# https://chromedriver.chromium.org/
```

#### Issue: "Chrome browser not found"
```
selenium.common.exceptions.WebDriverException: unknown error: cannot find Chrome binary
```

**Solutions:**
```bash
# Install Chrome (Ubuntu/Debian)
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install google-chrome-stable

# Install Chrome (macOS)
brew install --cask google-chrome

# Install Chromium (alternative)
sudo apt install chromium-browser  # Linux
brew install --cask chromium       # macOS

# Specify custom browser path in .env
echo "BROWSER_PATH=/path/to/chrome" >> .env
```

---

## Configuration Issues

### API Key Problems

#### Issue: "Invalid API key"
```
AuthenticationError: Invalid API key provided
```

**Solutions:**
```bash
# Check API key format
# Claude keys start with: sk-ant-
# OpenAI keys start with: sk-

# Verify key in .env file
cat .env | grep API_KEY

# Test API key manually
python -c "
import os
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
print('API key is valid')
"
```

#### Issue: "No API key found"
```
ConfigurationError: No AI model API key found
```

**Solutions:**
```bash
# Check if .env file exists
ls -la .env

# Create .env file if missing
cp .env.example .env

# Add API key to .env
echo "CLAUDE_API_KEY=your_key_here" >> .env

# Verify environment variables are loaded
python -c "import os; print(os.getenv('CLAUDE_API_KEY'))"
```

### Configuration File Issues

#### Issue: "Configuration file not found"
```
FileNotFoundError: Configuration file not found: config/app_config.json
```

**Solutions:**
```bash
# Create default configuration
ai-browser-agent --create-config

# Or create manually
mkdir -p config
cp config/app_config.json.example config/app_config.json

# Verify file exists
ls -la config/app_config.json
```

#### Issue: "Invalid JSON in configuration"
```
JSONDecodeError: Expecting ',' delimiter: line 15 column 5
```

**Solutions:**
```bash
# Validate JSON syntax
python -m json.tool config/app_config.json

# Common JSON errors:
# - Missing commas between items
# - Trailing commas before closing braces
# - Unescaped quotes in strings
# - Missing quotes around keys

# Reset to default if corrupted
ai-browser-agent --create-config
```

---

## Runtime Issues

### Browser Automation Problems

#### Issue: "Element not found"
```
NoSuchElementException: Unable to locate element
```

**Solutions:**
```bash
# Increase timeout
export BROWSER_TIMEOUT=60
ai-browser-agent --task "your task"

# Use debug mode to see element search process
ai-browser-agent --debug --task "your task"

# Check if page has loaded completely
# The agent will automatically wait, but some sites need longer

# Try more specific task description
ai-browser-agent --task "Wait for the page to load completely, then find the login button"
```

#### Issue: "Page load timeout"
```
TimeoutException: Message: timeout: Timed out receiving message from renderer
```

**Solutions:**
```bash
# Increase browser timeout
echo "BROWSER_TIMEOUT=60" >> .env

# Check internet connection
ping google.com

# Try headless mode (sometimes faster)
ai-browser-agent --headless --task "your task"

# Disable images to speed up loading
# Edit config/app_config.json:
{
  "browser": {
    "disable_images": true
  }
}
```

#### Issue: "Browser crashes or becomes unresponsive"
```
WebDriverException: chrome not reachable
```

**Solutions:**
```bash
# Kill existing browser processes
pkill chrome
pkill chromium

# Clear browser data
rm -rf ~/.config/google-chrome/Default/
# or
rm -rf browser_profiles/*

# Restart with fresh browser instance
ai-browser-agent --task "your task"

# Check system resources
free -h  # Check memory
df -h    # Check disk space
```

### AI Model Issues

#### Issue: "Token limit exceeded"
```
InvalidRequestError: This model's maximum context length is 4000 tokens
```

**Solutions:**
```bash
# Increase token limit in configuration
echo "AI_MAX_TOKENS=8000" >> .env

# Break complex tasks into smaller parts
ai-browser-agent --task "First, navigate to the website"
ai-browser-agent --task "Now, find the search box and search for products"

# Use more specific task descriptions to reduce context
# Instead of: "Do everything on this complex website"
# Use: "Find the login button and click it"
```

#### Issue: "AI API timeout"
```
TimeoutError: Request timed out after 30 seconds
```

**Solutions:**
```bash
# Increase API timeout
echo "AI_TIMEOUT=60" >> .env

# Check internet connection to AI APIs
curl -I https://api.anthropic.com
curl -I https://api.openai.com

# Try fallback model
echo "AI_PRIMARY_MODEL=openai" >> .env
echo "AI_FALLBACK_MODEL=claude" >> .env
```

#### Issue: "Rate limit exceeded"
```
RateLimitError: Rate limit reached for requests
```

**Solutions:**
```bash
# Wait and retry (rate limits are usually temporary)
sleep 60
ai-browser-agent --task "your task"

# Check your API usage and billing
# Visit your AI provider's dashboard

# Reduce task frequency
# Add delays between tasks if running many
```

### Security and Permission Issues

#### Issue: "Security confirmation not working"
```
SecurityError: User confirmation required but no input received
```

**Solutions:**
```bash
# Ensure terminal supports interactive input
ai-browser-agent --task "your task"
# Watch for confirmation prompts and respond with 'yes' or 'no'

# Disable confirmations for testing (not recommended for production)
echo "SECURITY_REQUIRE_PAYMENT_CONFIRMATION=false" >> .env
echo "SECURITY_REQUIRE_DELETION_CONFIRMATION=false" >> .env

# Check if running in non-interactive environment
# If running via cron or script, confirmations won't work
```

#### Issue: "File permission errors"
```
PermissionError: [Errno 13] Permission denied: 'logs/app.log'
```

**Solutions:**
```bash
# Create directories with proper permissions
mkdir -p logs screenshots session_data browser_profiles
chmod 755 logs screenshots session_data browser_profiles

# Fix ownership if needed
sudo chown -R $USER:$USER .

# Run with appropriate user permissions
# Don't run as root unless necessary
```

---

## Performance Issues

### Slow Task Execution

#### Issue: "Tasks take too long to complete"

**Diagnosis:**
```bash
# Check what's taking time
ai-browser-agent --debug --task "your task"
# Look for:
# - Long page load times
# - Multiple element search attempts
# - Large content processing
```

**Solutions:**
```bash
# Optimize browser settings
# Edit config/app_config.json:
{
  "browser": {
    "disable_images": true,
    "disable_plugins": true,
    "timeout": 15
  }
}

# Use headless mode for faster execution
ai-browser-agent --headless --task "your task"

# Simplify task descriptions
# Instead of: "Navigate to the website, find all products, compare prices, and make a decision"
# Use: "Navigate to the website and find the product search box"
```

### High Memory Usage

#### Issue: "System running out of memory"

**Diagnosis:**
```bash
# Monitor memory usage
top -p $(pgrep -f ai_browser_agent)
# or
htop

# Check browser memory usage
ps aux | grep chrome
```

**Solutions:**
```bash
# Limit browser memory usage
# Edit config/app_config.json:
{
  "browser": {
    "window_size": [1024, 768],
    "disable_images": true,
    "disable_plugins": true
  }
}

# Close browser between tasks
# The agent should do this automatically, but you can force it:
pkill chrome

# Use headless mode (uses less memory)
ai-browser-agent --headless --task "your task"

# Increase system swap if needed (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Network and Connectivity Issues

### Internet Connection Problems

#### Issue: "Network timeouts or connection errors"
```
ConnectionError: Failed to establish a new connection
```

**Solutions:**
```bash
# Test basic connectivity
ping google.com
ping api.anthropic.com
ping api.openai.com

# Check DNS resolution
nslookup api.anthropic.com
nslookup api.openai.com

# Test with curl
curl -I https://api.anthropic.com
curl -I https://api.openai.com

# Configure proxy if needed
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

### Firewall and Proxy Issues

#### Issue: "Requests blocked by firewall"
```
ProxyError: Cannot connect to proxy
```

**Solutions:**
```bash
# Configure proxy in environment
export HTTP_PROXY=http://username:password@proxy.company.com:8080
export HTTPS_PROXY=http://username:password@proxy.company.com:8080

# Or in configuration file
# Edit config/app_config.json:
{
  "network": {
    "proxy": "http://proxy.company.com:8080",
    "verify_ssl": false
  }
}

# Whitelist required domains in firewall:
# - api.anthropic.com
# - api.openai.com
# - chromedriver.storage.googleapis.com
```

---

## Platform-Specific Issues

### Windows Issues

#### Issue: "Path length limitations"
```
FileNotFoundError: [Errno 2] No such file or directory: 'very/long/path/...'
```

**Solutions:**
```bash
# Enable long path support
# Run as Administrator:
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or use shorter paths
# Move project to C:\ai-agent\
```

#### Issue: "Antivirus blocking execution"
```
Access denied or file quarantined
```

**Solutions:**
```bash
# Add exclusions to antivirus:
# - Project directory
# - Python executable
# - Chrome/Chromium executable
# - Temporary directories

# Temporarily disable real-time protection for testing
# (Re-enable after confirming it works)
```

### macOS Issues

#### Issue: "Gatekeeper blocking execution"
```
"chromedriver" cannot be opened because the developer cannot be verified
```

**Solutions:**
```bash
# Allow chromedriver to run
xattr -d com.apple.quarantine /path/to/chromedriver

# Or allow in System Preferences > Security & Privacy
# Click "Allow Anyway" when prompted
```

#### Issue: "Permission issues with browser"
```
Permission denied: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
```

**Solutions:**
```bash
# Grant accessibility permissions
# System Preferences > Security & Privacy > Privacy > Accessibility
# Add Terminal or your IDE to allowed applications

# Or run with sudo (not recommended)
sudo ai-browser-agent --task "your task"
```

### Linux Issues

#### Issue: "Display issues on headless servers"
```
selenium.common.exceptions.WebDriverException: unknown error: no display specified
```

**Solutions:**
```bash
# Install virtual display
sudo apt install xvfb

# Run with virtual display
xvfb-run -a ai-browser-agent --task "your task"

# Or use headless mode
ai-browser-agent --headless --task "your task"

# Set display environment variable
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
ai-browser-agent --task "your task"
```

#### Issue: "Missing system libraries"
```
ImportError: libgobject-2.0.so.0: cannot open shared object file
```

**Solutions:**
```bash
# Install missing libraries (Ubuntu/Debian)
sudo apt update
sudo apt install -y \
    libnss3-dev \
    libgconf-2-4 \
    libxss1 \
    libappindicator1 \
    fonts-liberation \
    libappindicator3-1 \
    libasound2-dev \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libgtk-3-0

# For CentOS/RHEL
sudo yum install -y \
    nss \
    atk \
    at-spi2-atk \
    gtk3 \
    cups-libs \
    libdrm \
    libxkbcommon \
    libxcomposite \
    libxdamage \
    libxrandr \
    libgbm \
    alsa-lib
```

---

## Debugging and Logging

### Enable Debug Mode

```bash
# Run with debug output
ai-browser-agent --debug --task "your task"

# Enable debug in configuration
echo "DEBUG_MODE=true" >> .env

# Check debug logs
tail -f logs/app.log
```

### Log Analysis

```bash
# View recent logs
tail -20 logs/app.log

# Search for errors
grep -i error logs/app.log

# Search for specific issues
grep -i "element not found" logs/app.log
grep -i "timeout" logs/app.log
grep -i "api" logs/app.log

# View security audit logs
tail -f logs/audit.log
```

### Verbose Logging

Edit `config/app_config.json`:
```json
{
  "browser": {
    "enable_logging": true,
    "log_level": "DEBUG"
  },
  "debug_mode": true
}
```

---

## Getting Help

### Self-Diagnosis Checklist

Before seeking help, run through this checklist:

1. **✓ Check system requirements**
   - Python 3.8+
   - Chrome/Chromium installed
   - Internet connectivity

2. **✓ Validate configuration**
   ```bash
   ai-browser-agent --validate-config
   ```

3. **✓ Check logs for errors**
   ```bash
   tail -20 logs/app.log
   ```

4. **✓ Test with simple task**
   ```bash
   ai-browser-agent --task "Navigate to google.com"
   ```

5. **✓ Try debug mode**
   ```bash
   ai-browser-agent --debug --task "simple task"
   ```

### Collecting Debug Information

When reporting issues, include:

```bash
# System information
uname -a
python --version
google-chrome --version

# Configuration validation
ai-browser-agent --validate-config

# Recent logs
tail -50 logs/app.log

# Environment variables (remove sensitive data)
env | grep -E "(CLAUDE|OPENAI|AI_|BROWSER_|DEBUG)" | sed 's/=.*/=***/'
```

### Support Channels

1. **Documentation**: Check user guide and troubleshooting sections
2. **GitHub Issues**: Report bugs with debug information
3. **Community Forums**: Ask questions and share solutions
4. **Debug Mode**: Use `--debug` flag for detailed output

### Common Solutions Summary

| Problem Category | First Try | If That Fails |
|------------------|-----------|---------------|
| Installation | Use virtual environment | Check Python version |
| Configuration | Run `--validate-config` | Recreate config files |
| Browser Issues | Increase timeout | Try headless mode |
| API Issues | Check API keys | Try fallback model |
| Network Issues | Test connectivity | Configure proxy |
| Performance | Use headless mode | Simplify tasks |
| Permissions | Check file permissions | Run with proper user |

Remember: Most issues are configuration-related and can be resolved by carefully following the setup guide and validating your configuration.