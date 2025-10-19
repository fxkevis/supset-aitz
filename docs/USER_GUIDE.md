# AI Browser Agent User Guide

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Getting Started](#getting-started)
- [Usage Examples](#usage-examples)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## Overview

The AI Browser Agent is an autonomous system that controls a web browser to perform complex multi-step tasks using artificial intelligence. It can handle tasks like email management, online shopping, form filling, and general web navigation with minimal user intervention.

### Key Features

- **Autonomous Task Execution**: Submit natural language tasks and watch the AI complete them
- **Visible Browser Control**: See exactly what the agent is doing in a real browser window
- **AI-Powered Decision Making**: Uses Claude or OpenAI models for intelligent web interaction
- **Security Layer**: Prompts for confirmation before potentially destructive actions
- **Context Management**: Efficiently processes large web pages within AI token limits
- **Specialized Handlers**: Built-in support for email management and online ordering
- **Session Persistence**: Maintains login sessions across tasks

### Supported Tasks

- **Email Management**: Read, organize, delete spam, manage inbox
- **Online Shopping**: Search products, add to cart, proceed through checkout
- **Form Filling**: Complete web forms with provided information
- **Web Navigation**: Navigate websites, click links, extract information
- **Content Extraction**: Extract specific information from web pages
- **Account Management**: Login to services, update profiles, manage settings

## Installation

### Prerequisites

- **Python 3.8 or higher**
- **Chrome or Chromium browser** (installed and accessible)
- **AI Model API Access** (Claude API recommended for Russian Federation, OpenAI as fallback)
- **Internet connection** for AI model API calls

### Step 1: Clone the Repository

```bash
git clone https://github.com/ai-browser-agent/ai-browser-agent.git
cd ai-browser-agent
```

### Step 2: Install Dependencies

#### Using pip (recommended):
```bash
# Install core dependencies
pip install -r requirements.txt

# For development (optional):
pip install -r requirements-dev.txt
```

#### Using pip with editable install:
```bash
pip install -e .
```

#### Using pip with optional dependencies:
```bash
# Install with AI model support
pip install -e .[ai]

# Install with development tools
pip install -e .[dev]

# Install everything
pip install -e .[ai,dev,testing]
```

### Step 3: Verify Installation

```bash
# Check if the agent is installed correctly
ai-browser-agent --version

# Validate your setup
python -m ai_browser_agent.main --validate-config
```

## Configuration

### Step 1: Create Environment File

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit the `.env` file with your actual values:

```env
# AI Model API Keys (at least one required)
CLAUDE_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# AI Model Configuration
AI_PRIMARY_MODEL=claude
AI_FALLBACK_MODEL=openai
AI_MAX_TOKENS=4000
AI_TEMPERATURE=0.7

# Browser Configuration
BROWSER_HEADLESS=false
BROWSER_TYPE=chrome
BROWSER_TIMEOUT=30

# Security Configuration
SECURITY_REQUIRE_PAYMENT_CONFIRMATION=true
SECURITY_REQUIRE_DELETION_CONFIRMATION=true
SECURITY_MAX_TASK_DURATION=3600

# Application Configuration
DEBUG_MODE=false
LOG_FILE=logs/app.log
DATA_DIRECTORY=data
```

### Step 2: Get API Keys

#### Claude API (Recommended for Russian Federation)
1. Visit [Anthropic's website](https://www.anthropic.com/)
2. Sign up for an account
3. Navigate to API keys section
4. Generate a new API key
5. Add it to your `.env` file as `CLAUDE_API_KEY`

#### OpenAI API (Fallback)
1. Visit [OpenAI's website](https://platform.openai.com/)
2. Sign up for an account
3. Navigate to API keys section
4. Generate a new API key
5. Add it to your `.env` file as `OPENAI_API_KEY`

### Step 3: Create Configuration File

Generate a default configuration file:

```bash
ai-browser-agent --create-config
```

This creates `config/app_config.json` which you can customize as needed.

### Step 4: Validate Configuration

Ensure everything is set up correctly:

```bash
ai-browser-agent --validate-config
```

You should see:
```
✓ Configuration loaded and validated successfully
✓ API keys are configured
```

## Getting Started

### Basic Usage

#### Interactive Mode
Start the agent in interactive mode:

```bash
ai-browser-agent
```

You'll see a prompt where you can enter tasks:
```
AI Browser Agent started. Type 'help' for available commands.
Enter command (or 'quit' to exit): 
```

#### Direct Task Execution
Execute a task directly from the command line:

```bash
ai-browser-agent --task "Check my Gmail inbox and delete any spam emails"
```

#### Debug Mode
Run with detailed logging for troubleshooting:

```bash
ai-browser-agent --debug --task "Navigate to example.com and find the contact page"
```

#### Headless Mode
Run without showing the browser window:

```bash
ai-browser-agent --headless --task "Extract the title from example.com"
```

### Your First Task

Let's start with a simple task to verify everything works:

1. **Start the agent**:
   ```bash
   ai-browser-agent
   ```

2. **Enter a simple task**:
   ```
   Navigate to google.com and search for "AI browser automation"
   ```

3. **Watch the agent work**: You'll see a browser window open and the agent will:
   - Navigate to Google
   - Find the search box
   - Type the search query
   - Click the search button
   - Report the results

4. **Review the results**: The agent will provide a summary of what it accomplished.

## Usage Examples

### Email Management

#### Basic Email Tasks
```bash
# Check inbox and provide summary
ai-browser-agent --task "Check my Gmail inbox and tell me about new emails"

# Delete spam emails
ai-browser-agent --task "Go through my Gmail inbox and delete any obvious spam emails"

# Organize emails by moving to folders
ai-browser-agent --task "Move all emails from newsletters to the 'Newsletters' folder in Gmail"

# Mark important emails
ai-browser-agent --task "Find emails from my boss and mark them as important"
```

#### Advanced Email Management
```bash
# Unsubscribe from unwanted emails
ai-browser-agent --task "Find subscription emails I haven't opened in 6 months and unsubscribe from them"

# Create email filters
ai-browser-agent --task "Create a filter to automatically label emails from 'noreply@company.com' as 'Automated'"

# Clean up old emails
ai-browser-agent --task "Delete emails older than 1 year from the 'Promotions' folder"
```

### Online Shopping

#### Basic Shopping Tasks
```bash
# Search for products
ai-browser-agent --task "Go to Amazon and find wireless headphones under $100"

# Add items to cart
ai-browser-agent --task "Add a pack of AA batteries to my Amazon cart"

# Check order status
ai-browser-agent --task "Check the status of my recent Amazon orders"
```

#### Food Delivery
```bash
# Order from previous orders
ai-browser-agent --task "Order my usual pizza from Domino's using my previous order"

# Find and order specific items
ai-browser-agent --task "Order a large pepperoni pizza and garlic bread from the nearest pizza place on DoorDash"

# Compare prices
ai-browser-agent --task "Compare prices for chicken tikka masala delivery between UberEats and DoorDash"
```

### Web Navigation and Information Extraction

#### Research Tasks
```bash
# Extract specific information
ai-browser-agent --task "Go to the Apple website and find the price of the latest iPhone"

# Compare information across sites
ai-browser-agent --task "Compare the features of Tesla Model 3 on Tesla's website vs. automotive review sites"

# Monitor changes
ai-browser-agent --task "Check if there are any new job postings on the company careers page"
```

#### Form Filling
```bash
# Fill out contact forms
ai-browser-agent --task "Fill out the contact form on example.com with my information: Name: John Doe, Email: john@example.com, Message: Interested in your services"

# Submit applications
ai-browser-agent --task "Fill out the job application form with my resume information and submit it"
```

### Account Management

#### Profile Updates
```bash
# Update social media profiles
ai-browser-agent --task "Update my LinkedIn headline to 'Senior Software Engineer at TechCorp'"

# Change account settings
ai-browser-agent --task "Go to my Twitter settings and enable two-factor authentication"

# Manage subscriptions
ai-browser-agent --task "Cancel my Netflix subscription"
```

## Advanced Features

### Security Confirmations

The agent will automatically prompt you before performing potentially destructive actions:

- **Payment actions**: Making purchases, entering payment information
- **Deletion actions**: Deleting emails, files, or accounts
- **Modification actions**: Changing important settings or information
- **Submission actions**: Submitting forms with sensitive information (optional)

Example security prompt:
```
⚠️  SECURITY CONFIRMATION REQUIRED ⚠️
Action: Delete email "Important Meeting Notes"
Risk Level: HIGH
Details: This action will permanently delete an email that may contain important information.

Do you want to proceed? (yes/no): 
```

### Custom Configuration

#### Browser Settings
Customize browser behavior in `config/app_config.json`:

```json
{
  "browser": {
    "headless": false,
    "window_size": [1920, 1080],
    "timeout": 30,
    "browser_type": "chrome",
    "disable_images": false,
    "enable_logging": true
  }
}
```

#### Security Settings
Configure security behavior:

```json
{
  "security": {
    "require_confirmation_for_payments": true,
    "require_confirmation_for_deletions": true,
    "require_confirmation_for_modifications": true,
    "sensitive_domains": ["paypal.com", "banking.com"],
    "max_task_duration": 3600
  }
}
```

#### AI Model Settings
Adjust AI behavior:

```json
{
  "ai_model": {
    "primary_model": "claude",
    "fallback_model": "openai",
    "max_tokens": 4000,
    "temperature": 0.7,
    "timeout": 30
  }
}
```

### Session Persistence

The agent can maintain browser sessions across tasks:

1. **Login once**: Manually log into services like Gmail, Amazon, etc.
2. **Persistent sessions**: The agent will reuse your login sessions for subsequent tasks
3. **Profile management**: Browser profiles are saved and reused

Example workflow:
```bash
# First, manually log into Gmail in the browser window
ai-browser-agent --task "Navigate to Gmail and wait for me to log in"

# Then use the logged-in session for email tasks
ai-browser-agent --task "Now that I'm logged in, check my inbox and delete spam"
```

### Task Chaining

You can chain multiple tasks together:

```bash
ai-browser-agent --task "First, check my Gmail for any urgent emails. Then, go to Amazon and check if my recent order has shipped. Finally, visit the weather website and tell me tomorrow's forecast."
```

### Error Recovery

The agent includes intelligent error recovery:

- **Automatic retries**: Failed actions are retried with different strategies
- **Alternative approaches**: If one method fails, the agent tries alternative approaches
- **User escalation**: For unresolvable issues, the agent asks for user guidance
- **Graceful degradation**: Partial task completion when full execution isn't possible

## Troubleshooting

### Common Issues

#### 1. "Configuration error: No API key found"

**Problem**: No AI model API key is configured.

**Solution**:
```bash
# Add your API key to .env file
echo "CLAUDE_API_KEY=your_key_here" >> .env
# or
echo "OPENAI_API_KEY=your_key_here" >> .env

# Validate configuration
ai-browser-agent --validate-config
```

#### 2. "Browser failed to start"

**Problem**: Chrome/Chromium browser is not installed or not accessible.

**Solutions**:
- **Install Chrome**: Download and install Google Chrome
- **Check PATH**: Ensure Chrome is in your system PATH
- **Specify browser path**: Set `BROWSER_PATH` in your `.env` file
- **Try different browser**: Set `BROWSER_TYPE=firefox` in configuration

#### 3. "Element not found" errors

**Problem**: The agent can't find web elements on the page.

**Solutions**:
- **Wait for page load**: Increase `BROWSER_TIMEOUT` in configuration
- **Check page changes**: Website might have changed its layout
- **Try different approach**: Restart the task with more specific instructions
- **Debug mode**: Run with `--debug` to see detailed element search logs

#### 4. "Token limit exceeded" errors

**Problem**: Web page content is too large for the AI model.

**Solutions**:
- **Increase token limit**: Set `AI_MAX_TOKENS=8000` in configuration
- **Simplify task**: Break complex tasks into smaller steps
- **Use content filtering**: The agent will automatically optimize content

#### 5. "Task timeout" errors

**Problem**: Task is taking too long to complete.

**Solutions**:
- **Increase timeout**: Set `SECURITY_MAX_TASK_DURATION=7200` (2 hours)
- **Break down task**: Split complex tasks into smaller parts
- **Check internet connection**: Ensure stable internet connectivity
- **Simplify instructions**: Use clearer, more specific task descriptions

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
ai-browser-agent --debug --task "your task here"
```

Debug mode provides:
- Detailed action logs
- Element search strategies
- AI decision-making process
- Network request information
- Error stack traces

### Log Files

Check log files for detailed error information:

```bash
# Application logs
tail -f logs/app.log

# Security audit logs
tail -f logs/audit.log

# Browser logs (if enabled)
tail -f logs/browser.log
```

### Configuration Validation

Validate your configuration setup:

```bash
# Check configuration
ai-browser-agent --validate-config

# Test API connectivity
python scripts/validate_config.py

# Check browser setup
python -c "from selenium import webdriver; driver = webdriver.Chrome(); driver.quit(); print('Browser OK')"
```

### Getting Help

If you're still experiencing issues:

1. **Check the logs**: Look at `logs/app.log` for error details
2. **Run validation**: Use `--validate-config` to check setup
3. **Try debug mode**: Use `--debug` for verbose output
4. **Simplify the task**: Start with basic tasks and gradually increase complexity
5. **Check requirements**: Ensure all dependencies are installed correctly

## FAQ

### General Questions

**Q: What types of tasks can the AI Browser Agent perform?**
A: The agent can perform most web-based tasks including email management, online shopping, form filling, web navigation, information extraction, and account management. It's particularly good at repetitive tasks that involve multiple steps.

**Q: Is it safe to use with sensitive websites like banking?**
A: The agent includes security measures and will prompt for confirmation before potentially destructive actions. However, we recommend using it primarily for non-critical tasks and always reviewing actions before confirming them.

**Q: Can I use it without an internet connection?**
A: No, the agent requires internet connectivity to communicate with AI model APIs (Claude or OpenAI) for decision-making.

**Q: Does it work with all websites?**
A: The agent works with most modern websites, but some sites with heavy JavaScript, CAPTCHAs, or anti-automation measures may be challenging. It works best with standard web interfaces.

### Technical Questions

**Q: Which AI model should I use?**
A: Claude is recommended as the primary model, especially for users in the Russian Federation. OpenAI can be used as a fallback. The agent will automatically switch between them if one fails.

**Q: Can I run multiple agents simultaneously?**
A: Yes, but each instance should use a separate browser profile to avoid conflicts. Configure different profile paths in the configuration.

**Q: How much does it cost to run?**
A: Costs depend on your AI model API usage. Claude and OpenAI charge per token used. Typical tasks use 1000-5000 tokens, costing a few cents per task.

**Q: Can I customize the agent's behavior?**
A: Yes, you can customize browser settings, security requirements, AI model parameters, and more through the configuration files and environment variables.

### Privacy and Security

**Q: What data does the agent collect?**
A: The agent processes web page content locally and sends relevant portions to AI models for decision-making. It logs actions for debugging and security auditing. No personal data is stored permanently unless you configure it to do so.

**Q: Are my API keys secure?**
A: API keys are stored in environment variables or local configuration files. Never commit them to version control. The agent doesn't transmit API keys except to the respective AI model services.

**Q: Can I review actions before they're executed?**
A: Yes, the security layer can be configured to prompt for confirmation before various types of actions. You can also run in debug mode to see what the agent plans to do.

### Troubleshooting

**Q: The agent is making wrong decisions. How can I improve it?**
A: Try providing more specific task descriptions, using debug mode to understand its reasoning, or adjusting the AI model temperature setting for more consistent behavior.

**Q: Tasks are failing frequently. What should I do?**
A: Check your internet connection, validate your configuration, ensure the target websites are accessible, and try breaking complex tasks into smaller steps.

**Q: The browser window is too small/large. How do I change it?**
A: Modify the `window_size` setting in `config/app_config.json` or set `BROWSER_WINDOW_SIZE` environment variable.

**Q: Can I run the agent on a server without a display?**
A: Yes, use headless mode with `--headless` flag or set `BROWSER_HEADLESS=true` in configuration. Note that some websites may detect and block headless browsers.