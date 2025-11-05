# LeakFinder - Crypto Wallet Scanner

LeakFinder is a powerful Flask application that helps security researchers and developers find leaked cryptocurrency private keys, keystores, wallet files, mnemonic phrases, and other sensitive information across various public data sources.

## 🚨 Legal Disclaimer

**This tool is for legitimate security research and educational purposes only.** 

- Only searches publicly available data through official APIs
- Does not bypass access controls or authentication
- Users are responsible for complying with all applicable laws and terms of service
- Intended for finding your own leaked credentials or authorized security research

## ✨ Features

- **Multi-Provider Search**: 9 different data sources for comprehensive coverage
- **Pattern Detection**: Identifies ETH private keys, BTC WIF, xprv keys, keystores, and mnemonic phrases
- **Address Derivation**: Automatically derives wallet addresses from found private keys
- **Explorer Integration**: Direct links to block explorers for balance checking
- **Configurable Scanning**: Choose specific leak types and providers
- **Graceful Degradation**: Works with free tiers and handles missing API keys
- **Security-First**: Results are redacted in UI, no data storage

## 🔍 Supported Providers

| Provider | Description | API Key Required | Free Tier |
|----------|-------------|------------------|-----------|
| **GitHub** | Code search across repositories | Optional | 60/hour (5000 with token) |
| **GitLab** | GitLab.com code search | Optional | Yes |
| **Shodan** | Internet-connected device search | Required | 100 queries/month |
| **Bitbucket** | Code snippets search | Required | With app password |
| **Sourcegraph** | Public code search engine | Optional | Yes |
| **Google CSE** | Custom web search | Required | 100 queries/day |
| **Pastebin** | Recent public pastes | None | Rate limited |
| **Wayback Machine** | Internet Archive search | None | Rate limited |
| **HIBP Pastes** | Breach data pastes | Required | Paid service |

## 🛠️ Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/mikempcb/bitscan.git
   cd bitscan
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure your API keys:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
PORT=5000

# Request Settings
MAX_RESULTS_PER_PROVIDER=25
REQUEST_TIMEOUT=15
USER_AGENT=LeakFinder/1.0 (+https://example.com)

# API Keys (all optional, but improve results)
GITHUB_TOKEN=ghp_your_github_token_here
GITLAB_TOKEN=glpat-your_gitlab_token_here
SHODAN_API_KEY=your_shodan_api_key
BITBUCKET_USERNAME=your_bitbucket_username
BITBUCKET_APP_PASSWORD=your_bitbucket_app_password
SOURCEGRAPH_TOKEN=sgp_your_sourcegraph_token_here
GOOGLE_CSE_API_KEY=your_google_cse_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id
HIBP_API_KEY=your_hibp_api_key
```

### API Key Setup Guides

<details>
<summary><strong>GitHub Token</strong></summary>

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `public_repo` (for public repository access)
4. Copy token to `GITHUB_TOKEN`

**Rate Limits**: 60/hour without token, 5000/hour with token
</details>

<details>
<summary><strong>GitLab Token</strong></summary>

1. Go to GitLab User Settings → Access Tokens
2. Create personal access token
3. Select scopes: `read_api`, `read_repository`
4. Copy token to `GITLAB_TOKEN`

**Rate Limits**: 2000/hour for authenticated requests
</details>

<details>
<summary><strong>Shodan API Key</strong></summary>

1. Create account at [shodan.io](https://shodan.io)
2. Go to Account → API Key
3. Copy API key to `SHODAN_API_KEY`

**Rate Limits**: 100 queries/month (free), more with paid plans
</details>

<details>
<summary><strong>Google Custom Search</strong></summary>

1. Create project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Custom Search API
3. Create API key in Credentials
4. Create Custom Search Engine at [cse.google.com](https://cse.google.com)
5. Set `GOOGLE_CSE_API_KEY` and `GOOGLE_CSE_ID`

**Rate Limits**: 100 queries/day (free)
</details>

<details>
<summary><strong>Other Providers</strong></summary>

- **Bitbucket**: Create app password in Bitbucket settings
- **Sourcegraph**: Create token at sourcegraph.com
- **HIBP**: Paid subscription required for pastes API
- **Pastebin/Wayback**: No API keys needed
</details>

## 🎯 Usage

### Web Interface

1. **Home Page**: Introduction and disclaimer
2. **Scan Form**: Configure your search
   - **Query**: Custom search terms (optional)
   - **Owner**: Filter by organization/user
   - **Language**: Filter by programming language
   - **Max Results**: Limit results per provider
   - **Leak Types**: Choose what to search for
   - **Providers**: Select data sources

3. **Results Page**: View findings with:
   - Redacted artifacts for security
   - Context previews
   - Derived wallet addresses
   - Block explorer links
   - Source links

### Leak Types Detected

- **ETH Private Keys**: `0x` prefixed and raw 64-character hex
- **BTC WIF**: Wallet Import Format (Base58, starts with 5/K/L)
- **BIP32 xprv**: Extended private keys
- **Keystore Files**: Ethereum keystore indicators
- **Mnemonic Phrases**: Seed phrase indicators

### Search Tips

- **Start broad**: Use default settings first
- **Filter by owner**: Target specific organizations
- **Language filtering**: Focus on relevant code
- **Combine providers**: Different sources find different leaks
- **Check addresses**: Use explorer links to verify balances

## 🏗️ Architecture

```
leakfinder/
├── __init__.py          # Flask app factory
├── views.py             # Routes and request handling
├── providers/           # Data source implementations
│   ├── __init__.py      # Base provider class
│   ├── github.py        # GitHub Code Search
│   ├── gitlab.py        # GitLab Search
│   ├── shodan.py        # Shodan API
│   ├── bitbucket.py     # Bitbucket Snippets
│   ├── sourcegraph.py   # Sourcegraph Search
│   ├── google_cse.py    # Google Custom Search
│   ├── pastebin.py      # Pastebin Scraping
│   ├── wayback.py       # Internet Archive
│   └── hibp_pastes.py   # HIBP Pastes API
├── utils/
│   ├── patterns.py      # Regex patterns for leak detection
│   └── crypto.py        # Address derivation utilities
└── templates/           # HTML templates
    ├── base.html        # Base template
    ├── index.html       # Home page
    ├── scan.html        # Scan form
    └── results.html     # Results display
```

## 🔒 Security Considerations

- **No Data Storage**: All processing happens in-memory
- **Result Redaction**: Sensitive data is truncated in UI
- **API Rate Limiting**: Respects provider rate limits
- **Timeout Protection**: Prevents hanging requests
- **Error Handling**: Graceful failure for each provider

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add new providers in `leakfinder/providers/`
4. Update `views.py` to include new providers
5. Add configuration to `__init__.py`
6. Update templates if needed
7. Submit a pull request

### Adding New Providers

1. Inherit from `BaseProvider`
2. Implement `search()` method
3. Use `_find_matches()` for pattern detection
4. Handle API keys gracefully
5. Return standardized result format

## 📝 License

This project is provided for educational and security research purposes. Users are responsible for compliance with all applicable laws and terms of service.

## ⚠️ Responsible Use

- Only search for your own leaked credentials
- Respect API rate limits and terms of service
- Do not use for unauthorized access or malicious purposes
- Report findings through appropriate channels
- Consider the privacy and security implications

## 🐛 Troubleshooting

### Common Issues

**"No results found"**
- Check API key configuration
- Verify internet connectivity
- Try different search terms
- Check provider status pages

**"Rate limit exceeded"**
- Wait for rate limit reset
- Add API keys for higher limits
- Reduce max results per provider

**"Provider error"**
- Check API key validity
- Verify provider service status
- Review error messages in results

### Debug Mode

Enable debug mode for detailed error information:
```bash
export FLASK_DEBUG=1
python run.py
```

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review provider API documentation
- Ensure responsible use practices

---

**Remember**: This tool is for legitimate security research only. Always respect privacy, follow applicable laws, and use responsibly.
