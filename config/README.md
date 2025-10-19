# AI Browser Agent Configuration

This directory contains configuration files for the AI Browser Agent.

## Configuration Files

### app_config.json
Main application configuration file containing:
- **browser**: Browser automation settings (headless mode, timeouts, etc.)
- **security**: Security and safety settings (confirmation requirements, audit logging)
- **ai_model**: AI model configuration (API keys, model selection, parameters)
- **debug_mode**: Enable/disable debug logging
- **log_file**: Path to application log file
- **data_directory**: Directory for application data
- **temp_directory**: Directory for temporary files

## Environment Variables

Configuration can be overridden using environment variables. See `.env.example` for available options.

### Required Environment Variables
At least one AI model API key must be set:
- `CLAUDE_API_KEY`: Your Claude API key (recommended for Russian Federation)
- `OPENAI_API_KEY`: Your OpenAI API key (fallback option)

### Optional Environment Variables
- `AI_PRIMARY_MODEL`: Primary AI model to use (claude/openai)
- `AI_FALLBACK_MODEL`: Fallback AI model
- `BROWSER_HEADLESS`: Run browser in headless mode (true/false)
- `BROWSER_TYPE`: Browser type (chrome/firefox/safari/edge)
- `DEBUG_MODE`: Enable debug logging (true/false)

## Configuration Priority

Configuration is loaded in the following order (later sources override earlier ones):
1. Default values in code
2. Configuration file (app_config.json)
3. Environment variables

## Setup Instructions

1. **Initial Setup**:
   ```bash
   python scripts/setup.py
   ```

2. **Configure API Keys**:
   Edit `.env` file and add your API keys:
   ```bash
   CLAUDE_API_KEY=your_claude_api_key_here
   # or
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Validate Configuration**:
   ```bash
   python -m ai_browser_agent.main --validate-config
   ```

4. **Create Custom Configuration**:
   ```bash
   python -m ai_browser_agent.main --create-config
   ```
   Then edit `config/app_config.json` as needed.

## Security Considerations

- **API Keys**: Never commit API keys to version control. Use environment variables or local .env files.
- **Audit Logging**: Enable audit logging in production to track all security-sensitive actions.
- **Confirmation Settings**: Configure which actions require user confirmation based on your security requirements.
- **Sensitive Domains**: Review and customize the list of domains that require extra caution.

## Troubleshooting

### Configuration Validation Errors
Run the validation script to check your configuration:
```bash
python scripts/validate_config.py
```

### Missing API Keys
Ensure at least one AI model API key is configured:
```bash
export CLAUDE_API_KEY="your_key_here"
# or
export OPENAI_API_KEY="your_key_here"
```

### Directory Permissions
Ensure the application has write permissions for:
- `logs/` directory
- `data/` directory
- `temp/` directory
- `browser_profiles/` directory

### Browser Configuration
If browser automation fails:
1. Check that Chrome/Chromium is installed
2. Verify browser type in configuration matches installed browser
3. Check browser profile path permissions if using custom profiles