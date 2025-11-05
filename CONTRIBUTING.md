# Contributing to LeakFinder

Thank you for your interest in contributing to LeakFinder! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Issues

1. **Search existing issues** first to avoid duplicates
2. **Use issue templates** when available
3. **Provide detailed information**:
   - Operating system and Python version
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Error messages (without sensitive data)
   - Configuration details (without API keys)

### Suggesting Features

1. **Check existing feature requests** to avoid duplicates
2. **Describe the use case** and problem being solved
3. **Explain the proposed solution** in detail
4. **Consider implementation complexity** and maintenance burden

## 🔧 Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Text editor or IDE

### Local Development

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/bitscan.git
   cd bitscan
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Add your API keys for testing
   ```

6. **Run the application**:
   ```bash
   python run.py
   ```

### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards below

3. **Test your changes** thoroughly

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

## 📝 Coding Standards

### Python Style

- Follow **PEP 8** style guidelines
- Use **type hints** where appropriate
- Write **docstrings** for functions and classes
- Keep functions **small and focused**
- Use **meaningful variable names**

### Code Organization

```python
# Good example
def search_github_repositories(query: str, max_results: int) -> List[Dict[str, Any]]:
    """
    Search GitHub repositories for the given query.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of repository data dictionaries
    """
    # Implementation here
    pass
```

### Error Handling

- Use **specific exception types** when possible
- **Log errors** appropriately
- **Fail gracefully** - don't crash the entire scan if one provider fails
- **Provide helpful error messages** to users

```python
# Good example
try:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
except requests.exceptions.Timeout:
    logger.warning(f"Timeout accessing {provider_name}")
    return []
except requests.exceptions.RequestException as e:
    logger.error(f"Error accessing {provider_name}: {e}")
    return []
```

## 🔌 Adding New Providers

### Provider Structure

1. **Create provider file** in `leakfinder/providers/`
2. **Inherit from BaseProvider**
3. **Implement required methods**
4. **Handle API keys gracefully**
5. **Add to views.py**
6. **Update configuration**
7. **Update templates**

### Provider Template

```python
import re
from typing import List, Dict, Pattern, Any
import requests
from . import BaseProvider


class YourProvider(BaseProvider):
    name = 'your_provider'

    def _headers(self) -> Dict[str, str]:
        """Return HTTP headers including authentication."""
        headers = super()._headers()
        api_key = self.app.config.get('YOUR_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        return headers

    def search(self, query: str, owner: str, language: str, 
               patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        """
        Search for patterns in your data source.
        
        Args:
            query: User search query
            owner: Owner/organization filter
            language: Language filter
            patterns: Compiled regex patterns to match
            max_results: Maximum results to return
            
        Returns:
            List of result dictionaries with required fields
        """
        # Check for required API key
        if not self.app.config.get('YOUR_API_KEY'):
            return [{
                'provider': self.name,
                'source': 'N/A',
                'artifact': None,
                'preview': 'No YOUR_API_KEY configured; skipping.',
                'addresses': [],
                'links': [],
            }]
        
        # Implementation here
        results = []
        
        # Make API calls, process results, find pattern matches
        # Return standardized result format
        
        return results

    @staticmethod
    def _find_matches(text: str, patterns: List[Pattern]):
        """Find pattern matches in text."""
        found = []
        for pat in patterns:
            for m in re.finditer(pat, text):
                val = m.group(0)
                chain = 'eth' if '0x' in val else 'btc'  # Adjust logic as needed
                found.append({'value': val, 'span': m.span(), 'chain': chain})
        return found

    @staticmethod
    def _make_preview(text: str, span):
        """Create context preview around match."""
        start, end = span
        a = max(0, start - 60)
        b = min(len(text), end + 60)
        snippet = text[a:b].replace('\n', ' ')
        return snippet
```

### Integration Steps

1. **Add import** to `leakfinder/views.py`:
   ```python
   from .providers.your_provider import YourProvider
   ```

2. **Add to provider list** in `_providers()` function:
   ```python
   def _providers(app):
       return [
           # ... existing providers ...
           YourProvider(app),
       ]
   ```

3. **Add configuration** to `leakfinder/__init__.py`:
   ```python
   app.config.from_mapping(
       # ... existing config ...
       YOUR_API_KEY=os.environ.get("YOUR_API_KEY"),
   )
   ```

4. **Add to UI** in `leakfinder/templates/scan.html`:
   ```html
   <label><input type="checkbox" name="providers" value="your_provider" checked> Your Provider</label>
   ```

5. **Update documentation**:
   - Add to README.md provider table
   - Add setup instructions to SETUP.md
   - Update .env.example

### Provider Guidelines

- **Respect rate limits** and terms of service
- **Handle authentication errors** gracefully
- **Use appropriate timeouts** for requests
- **Validate API responses** before processing
- **Return consistent result format**
- **Log important events** for debugging
- **Test with and without API keys**

## 🧪 Testing

### Manual Testing

1. **Test without API keys** - should skip gracefully
2. **Test with invalid API keys** - should show appropriate errors
3. **Test with valid API keys** - should return results
4. **Test edge cases** - empty results, network errors, timeouts
5. **Test UI integration** - checkbox works, results display correctly

### Test Scenarios

- Empty search results
- Network connectivity issues
- API rate limiting
- Invalid API responses
- Large result sets
- Special characters in queries

## 📚 Documentation

### Required Documentation Updates

When adding features:

1. **Update README.md** with new provider information
2. **Update SETUP.md** with configuration instructions
3. **Update .env.example** with new environment variables
4. **Add inline code comments** for complex logic
5. **Update this CONTRIBUTING.md** if adding new patterns

### Documentation Style

- Use **clear, concise language**
- Include **code examples** where helpful
- Provide **step-by-step instructions**
- Use **consistent formatting**
- Include **troubleshooting tips**

## 🔒 Security Considerations

### API Key Handling

- **Never commit API keys** to the repository
- **Use environment variables** for all secrets
- **Provide clear setup instructions** for API keys
- **Handle missing keys gracefully**

### Data Handling

- **Don't store sensitive data** found during scans
- **Redact sensitive information** in UI and logs
- **Use HTTPS** for all API calls
- **Respect data privacy** and terms of service

### Responsible Disclosure

- **Only search public data** through official APIs
- **Don't bypass access controls**
- **Report security issues** privately to maintainers
- **Follow responsible disclosure practices**

## 📋 Pull Request Guidelines

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] API keys are not committed
- [ ] Feature works with and without API keys
- [ ] Error handling is implemented
- [ ] UI is updated if needed

### Pull Request Description

Include:

1. **Summary** of changes made
2. **Motivation** for the changes
3. **Testing** performed
4. **Screenshots** if UI changes
5. **Breaking changes** if any
6. **Related issues** if applicable

### Review Process

1. **Automated checks** must pass
2. **Manual review** by maintainers
3. **Testing** on different environments
4. **Documentation review**
5. **Security review** for new providers

## 🎯 Project Goals

Keep these goals in mind when contributing:

1. **Security First**: Legitimate research only, no malicious use
2. **User Friendly**: Easy setup and clear documentation
3. **Reliable**: Graceful error handling and consistent results
4. **Extensible**: Easy to add new providers and features
5. **Ethical**: Respect privacy, terms of service, and rate limits

## 💬 Communication

- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code contributions and discussions
- **Documentation**: Questions about setup and usage

## 📄 License

By contributing to LeakFinder, you agree that your contributions will be licensed under the same terms as the project.

---

Thank you for contributing to LeakFinder! Your help makes this tool better for the security research community.
