# AI Browser Agent

An AI-powered browser automation agent that autonomously controls a web browser to perform complex multi-step tasks. The agent operates in Python with visible browser control, uses AI models available in the Russian Federation, and can handle tasks like email management, online ordering, and web navigation with minimal user intervention.

## Features

- **Autonomous Task Execution**: Submit complex multi-step tasks and let the AI agent handle them automatically
- **Visible Browser Control**: Watch the automation process in a real browser window
- **AI-Powered Decisions**: Uses Claude or OpenAI models for intelligent decision-making
- **Security Layer**: Prompts for confirmation before destructive actions
- **Context Management**: Efficiently handles large web pages within AI token limits
- **Specialized Handlers**: Built-in support for email management and online ordering

## Requirements

- Python 3.8 or higher
- Chrome or Chromium browser
- AI model API access (Claude or OpenAI)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ai-browser-agent/ai-browser-agent.git
cd ai-browser-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. For development:
```bash
pip install -r requirements-dev.txt
```

## Quick Start

```python
from ai_browser_agent import AIAgent

# Initialize the agent
agent = AIAgent()

# Submit a task
result = agent.execute_task("Check my email and delete any spam messages")

# View the results
print(result.report)
```

## Configuration

Create a `.env` file in the project root:

```env
# AI Model Configuration
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key

# Browser Configuration
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=30

# Security Configuration
REQUIRE_CONFIRMATION_FOR_PAYMENTS=true
REQUIRE_CONFIRMATION_FOR_DELETIONS=true
```

## Project Structure

```
ai_browser_agent/
├── core/           # Core AI agent components
├── controllers/    # Browser control components
├── managers/       # Task and context management
├── models/         # Data models and configurations
├── interfaces/     # Base interfaces and abstractions
├── security/       # Security and validation components
├── ui/            # User interface components
└── main.py        # Application entry point
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[User Guide](docs/USER_GUIDE.md)** - Complete usage guide with examples
- **[Setup Guide](docs/SETUP_GUIDE.md)** - Detailed installation instructions  
- **[Examples](docs/EXAMPLES.md)** - Practical task examples and workflows
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Architecture](docs/ARCHITECTURE.md)** - System design and architecture
- **[Contributing](docs/CONTRIBUTING.md)** - Development and contribution guidelines

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black ai_browser_agent/
isort ai_browser_agent/

# Type checking
mypy ai_browser_agent/
```

### Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for:

- Development setup and workflow
- Code standards and best practices
- Testing guidelines
- Pull request process

## License

MIT License - see LICENSE file for details.