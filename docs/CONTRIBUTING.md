# Contributing to AI Browser Agent

## Table of Contents
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Architecture Guidelines](#architecture-guidelines)
- [Documentation Standards](#documentation-standards)

---

## Getting Started

We welcome contributions to the AI Browser Agent project! Whether you're fixing bugs, adding features, improving documentation, or helping with testing, your contributions are valuable.

### Ways to Contribute

- **Bug Reports**: Help us identify and fix issues
- **Feature Requests**: Suggest new functionality
- **Code Contributions**: Implement features, fix bugs, improve performance
- **Documentation**: Improve guides, API docs, and examples
- **Testing**: Add test cases, improve test coverage
- **Reviews**: Review pull requests and provide feedback

### Before You Start

1. **Read the Documentation**: Familiarize yourself with the project architecture and design principles
2. **Check Existing Issues**: Look for existing issues or discussions related to your contribution
3. **Discuss Major Changes**: For significant features or architectural changes, open an issue first to discuss the approach

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Chrome or Chromium browser
- AI model API access (Claude or OpenAI)

### Setup Steps

1. **Fork and Clone**
   ```bash
   # Fork the repository on GitHub
   git clone https://github.com/your-username/ai-browser-agent.git
   cd ai-browser-agent
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   # Install development dependencies
   pip install -r requirements-dev.txt
   
   # Install in editable mode
   pip install -e .
   ```

4. **Configure Environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Add your API keys to .env
   # CLAUDE_API_KEY=your_key_here
   # OPENAI_API_KEY=your_key_here
   ```

5. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

6. **Verify Setup**
   ```bash
   # Run tests
   pytest
   
   # Validate configuration
   python -m ai_browser_agent.main --validate-config
   ```

### Development Tools

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing
- **pre-commit**: Git hooks for quality checks

---

## Code Standards

### Python Style Guide

We follow PEP 8 with some modifications enforced by Black:

- **Line Length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Sorted with isort

### Code Formatting

```bash
# Format code with Black
black ai_browser_agent/

# Sort imports with isort
isort ai_browser_agent/

# Check linting with flake8
flake8 ai_browser_agent/

# Type checking with mypy
mypy ai_browser_agent/
```

### Type Hints

All new code must include type hints:

```python
from typing import Dict, List, Optional, Any

def process_page_content(
    content: str, 
    keywords: List[str], 
    max_tokens: int = 4000
) -> Dict[str, Any]:
    """Process page content with type hints."""
    result: Dict[str, Any] = {}
    # Implementation here
    return result
```

### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def extract_relevant_content(
    self, 
    page_content: PageContent, 
    task_keywords: List[str]
) -> str:
    """Extract content relevant to task keywords.
    
    Args:
        page_content: Full page content to process
        task_keywords: Keywords related to current task
        
    Returns:
        Filtered relevant content string
        
    Raises:
        ContentExtractionError: If content extraction fails
        
    Example:
        >>> extractor = ContentExtractor()
        >>> content = extractor.extract_relevant_content(page, ["login", "signin"])
        >>> print(content)
        "Login form with username and password fields..."
    """
```

### Error Handling

Use specific exception types and provide meaningful error messages:

```python
class TaskExecutionError(AIBrowserAgentError):
    """Raised when task execution fails."""
    
    def __init__(self, message: str, task: Task, step: Optional[TaskStep] = None):
        super().__init__(message)
        self.task = task
        self.step = step

# Usage
try:
    result = execute_task_step(step)
except ElementNotFoundError as e:
    raise TaskExecutionError(
        f"Failed to find element for step: {step.description}",
        task=current_task,
        step=step
    ) from e
```

### Logging

Use structured logging with appropriate levels:

```python
import logging

logger = logging.getLogger(__name__)

def execute_action(self, action: Action) -> ActionResult:
    """Execute browser action with proper logging."""
    logger.info(
        "Executing action",
        extra={
            "action_type": action.type,
            "target": action.target,
            "confidence": action.confidence
        }
    )
    
    try:
        result = self._perform_action(action)
        logger.debug("Action completed successfully", extra={"result": result})
        return result
    except Exception as e:
        logger.error(
            "Action execution failed",
            extra={
                "action": action.to_dict(),
                "error": str(e)
            },
            exc_info=True
        )
        raise
```

---

## Testing Guidelines

### Test Structure

We use pytest with the following test organization:

```
tests/
├── unit/                 # Unit tests for individual components
│   ├── test_ai_agent.py
│   ├── test_browser_controller.py
│   └── test_security_layer.py
├── integration/          # Integration tests for component interactions
│   ├── test_email_workflow.py
│   ├── test_ordering_workflow.py
│   └── test_security_validation.py
├── fixtures/            # Test fixtures and mock data
│   ├── mock_pages.py
│   └── test_data.py
└── conftest.py          # Pytest configuration and shared fixtures
```

### Writing Tests

#### Unit Tests

Test individual components in isolation:

```python
import pytest
from unittest.mock import Mock, patch
from ai_browser_agent.core.decision_engine import DecisionEngine
from ai_browser_agent.models.page_content import PageContent

class TestDecisionEngine:
    @pytest.fixture
    def mock_ai_model(self):
        """Mock AI model for testing."""
        mock = Mock()
        mock.generate_response.return_value = "click login button"
        return mock
    
    @pytest.fixture
    def decision_engine(self, mock_ai_model):
        """Decision engine with mocked dependencies."""
        return DecisionEngine(ai_model=mock_ai_model)
    
    def test_analyze_page_returns_actions(self, decision_engine):
        """Test that analyze_page returns valid actions."""
        # Arrange
        page_content = PageContent(
            url="https://example.com",
            title="Test Page",
            text_content="Login form with username and password",
            elements=[{"tag": "button", "text": "Login"}]
        )
        
        # Act
        actions = decision_engine.analyze_page(page_content, "login to website")
        
        # Assert
        assert len(actions) > 0
        assert all(hasattr(action, 'type') for action in actions)
        assert all(hasattr(action, 'confidence') for action in actions)
```

#### Integration Tests

Test component interactions:

```python
import pytest
from ai_browser_agent.core.ai_agent import AIAgent
from ai_browser_agent.ui.terminal_interface import TerminalInterface

class TestEmailWorkflow:
    @pytest.fixture
    def agent_with_test_config(self):
        """AI agent configured for testing."""
        config = {
            "debug": True,
            "app_config": self.create_test_config()
        }
        ui = TerminalInterface()
        agent = AIAgent(config=config, user_interface=ui)
        agent.initialize()
        return agent
    
    def test_email_spam_detection_workflow(self, agent_with_test_config):
        """Test complete email spam detection workflow."""
        # This would use a test email service or mock
        task = "Check Gmail inbox and identify spam emails"
        
        with patch('ai_browser_agent.controllers.browser_controller.webdriver'):
            result = agent_with_test_config.execute_task(task)
            
        assert "spam" in result.lower()
        assert "emails" in result.lower()
```

#### Mock Guidelines

Use mocks appropriately:

```python
# Good: Mock external dependencies
@patch('ai_browser_agent.interfaces.claude_model.anthropic.Anthropic')
def test_claude_model_integration(self, mock_anthropic):
    mock_client = Mock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value.content = [Mock(text="test response")]
    
    model = ClaudeModel("test-key")
    response = model.generate_response("test prompt", "test context")
    
    assert response == "test response"

# Avoid: Mocking internal logic that should be tested
# Don't mock the method you're testing
```

### Test Data and Fixtures

Create reusable test data:

```python
# tests/fixtures/test_data.py
@pytest.fixture
def sample_page_content():
    """Sample page content for testing."""
    return PageContent(
        url="https://test.example.com",
        title="Test Page",
        text_content="This is a test page with login form",
        elements=[
            {"tag": "input", "type": "text", "name": "username"},
            {"tag": "input", "type": "password", "name": "password"},
            {"tag": "button", "type": "submit", "text": "Login"}
        ]
    )

@pytest.fixture
def mock_browser_controller():
    """Mock browser controller for testing."""
    mock = Mock()
    mock.get_page_content.return_value = sample_page_content()
    return mock
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_ai_agent.py

# Run with coverage
pytest --cov=ai_browser_agent --cov-report=html

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_ai_agent.py::TestAIAgent::test_execute_task
```

---

## Pull Request Process

### Before Submitting

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number-description
   ```

2. **Make Changes**
   - Follow code standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Run Quality Checks**
   ```bash
   # Format code
   black ai_browser_agent/
   isort ai_browser_agent/
   
   # Run linting
   flake8 ai_browser_agent/
   
   # Type checking
   mypy ai_browser_agent/
   
   # Run tests
   pytest
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new task handler for social media automation"
   ```

### Commit Message Format

Use conventional commit format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(browser): add support for Firefox browser automation

fix(security): resolve issue with payment confirmation prompts

docs(api): update API reference for new context manager methods

test(integration): add tests for email workflow error handling
```

### Pull Request Template

When creating a pull request, include:

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] New tests added for new functionality

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings or errors introduced

## Related Issues
Closes #123
Related to #456
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Code Review**: Maintainers review code for quality, design, and standards
3. **Testing**: Reviewers may test functionality manually
4. **Approval**: At least one maintainer approval required
5. **Merge**: Squash and merge after approval

---

## Issue Guidelines

### Bug Reports

Use the bug report template:

```markdown
## Bug Description
Clear description of the bug and expected behavior.

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Environment
- OS: [e.g., Windows 10, macOS 12, Ubuntu 20.04]
- Python Version: [e.g., 3.9.7]
- Browser: [e.g., Chrome 96.0.4664.110]
- AI Browser Agent Version: [e.g., 1.0.0]

## Logs
```
Relevant log output or error messages
```

## Additional Context
Any additional information that might help.
```

### Feature Requests

Use the feature request template:

```markdown
## Feature Description
Clear description of the proposed feature.

## Use Case
Describe the problem this feature would solve.

## Proposed Solution
Describe your preferred solution.

## Alternatives Considered
Describe alternative solutions you've considered.

## Additional Context
Any additional information or mockups.
```

### Issue Labels

We use labels to categorize issues:

- **Type**: `bug`, `enhancement`, `documentation`, `question`
- **Priority**: `low`, `medium`, `high`, `critical`
- **Component**: `browser`, `ai-model`, `security`, `ui`
- **Status**: `needs-triage`, `in-progress`, `blocked`

---

## Architecture Guidelines

### Adding New Components

When adding new components:

1. **Follow Interface Pattern**
   ```python
   class NewComponentInterface(ABC):
       @abstractmethod
       def main_method(self, param: Type) -> ReturnType:
           pass
   
   class NewComponent(NewComponentInterface):
       def main_method(self, param: Type) -> ReturnType:
           # Implementation
           pass
   ```

2. **Use Dependency Injection**
   ```python
   class NewComponent:
       def __init__(self, dependency: DependencyInterface):
           self.dependency = dependency
   ```

3. **Add Configuration Support**
   ```python
   @dataclass
   class NewComponentConfig:
       setting1: str
       setting2: int = 10
   ```

4. **Include Error Handling**
   ```python
   class NewComponentError(AIBrowserAgentError):
       pass
   ```

### Extending Existing Components

When extending components:

1. **Maintain Backward Compatibility**
2. **Add New Methods Rather Than Modifying Existing Ones**
3. **Use Optional Parameters for New Features**
4. **Update Tests and Documentation**

### Performance Considerations

- **Async Operations**: Use async/await for I/O operations where appropriate
- **Caching**: Implement caching for expensive operations
- **Resource Management**: Properly manage browser and AI model resources
- **Memory Usage**: Monitor and optimize memory usage

---

## Documentation Standards

### Code Documentation

- **All public methods must have docstrings**
- **Use type hints for all parameters and return values**
- **Include examples in docstrings for complex methods**
- **Document exceptions that can be raised**

### API Documentation

When adding new APIs:

1. **Update API Reference**: Add to `docs/API_REFERENCE.md`
2. **Include Examples**: Provide usage examples
3. **Document Parameters**: Describe all parameters and return values
4. **Note Breaking Changes**: Clearly mark any breaking changes

### User Documentation

When adding user-facing features:

1. **Update User Guide**: Add to `docs/USER_GUIDE.md`
2. **Add Examples**: Include practical examples in `docs/EXAMPLES.md`
3. **Update Setup Guide**: If setup changes, update `docs/SETUP_GUIDE.md`
4. **Add Troubleshooting**: Document common issues in `docs/TROUBLESHOOTING.md`

### Architecture Documentation

For architectural changes:

1. **Update Architecture Guide**: Modify `docs/ARCHITECTURE.md`
2. **Update Diagrams**: Keep Mermaid diagrams current
3. **Document Design Decisions**: Explain why changes were made
4. **Update Component Interactions**: Show how components work together

---

## Release Process

### Version Numbering

We use Semantic Versioning (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update Version Numbers**
2. **Update CHANGELOG.md**
3. **Run Full Test Suite**
4. **Update Documentation**
5. **Create Release Notes**
6. **Tag Release**
7. **Deploy to Package Repositories**

---

## Community Guidelines

### Code of Conduct

- **Be Respectful**: Treat all contributors with respect
- **Be Inclusive**: Welcome contributors from all backgrounds
- **Be Constructive**: Provide helpful feedback and suggestions
- **Be Patient**: Remember that everyone is learning

### Communication

- **GitHub Issues**: For bug reports and feature requests
- **Pull Requests**: For code contributions and reviews
- **Discussions**: For general questions and community interaction

### Recognition

We recognize contributors through:

- **Contributors File**: Listed in CONTRIBUTORS.md
- **Release Notes**: Mentioned in release announcements
- **GitHub Recognition**: Contributor badges and statistics

---

Thank you for contributing to AI Browser Agent! Your contributions help make web automation more accessible and powerful for everyone.