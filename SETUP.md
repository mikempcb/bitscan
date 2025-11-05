# LeakFinder Setup Guide

This guide provides detailed setup instructions for LeakFinder and all its data providers.

## 🚀 Quick Setup (No API Keys)

For immediate testing with limited functionality:

```bash
git clone https://github.com/mikempcb/bitscan.git
cd bitscan
pip install -r requirements.txt
python run.py
```

Visit `http://localhost:5000` and use GitHub (limited), Pastebin, and Wayback Machine providers.

## 🔧 Full Setup with API Keys

### 1. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your preferred text editor and add API keys as needed.

### 2. Provider Setup Details

#### GitHub (Recommended - Free)

**Why**: Largest code repository, high-quality results
**Cost**: Free (with rate limits)

1. Go to [GitHub Settings](https://github.com/settings/tokens)
2. Click "Developer settings" → "Personal access tokens" → "Tokens (classic)"
3. Click "Generate new token (classic)"
4. Set expiration and select scopes:
   - `public_repo` (access public repositories)
5. Copy token and add to `.env`:
   ```
   GITHUB_TOKEN=ghp_your_token_here
   ```

**Rate Limits**: 60/hour → 5000/hour with token

#### GitLab (Recommended - Free)

**Why**: Second largest Git platform, different content than GitHub
**Cost**: Free

1. Go to [GitLab User Settings](https://gitlab.com/-/profile/personal_access_tokens)
2. Click "Add new token"
3. Set name and expiration
4. Select scopes:
   - `read_api` (read API access)
   - `read_repository` (read repository data)
5. Copy token and add to `.env`:
   ```
   GITLAB_TOKEN=glpat-your_token_here
   ```

**Rate Limits**: 2000/hour for authenticated requests

#### Shodan (Optional - Freemium)

**Why**: Finds exposed services and devices with crypto data
**Cost**: Free tier (100 queries/month), paid plans available

1. Create account at [shodan.io](https://shodan.io)
2. Go to [Account page](https://account.shodan.io/)
3. Copy API key and add to `.env`:
   ```
   SHODAN_API_KEY=your_key_here
   ```

**Rate Limits**: 100 queries/month (free), 10,000+ (paid)

#### Sourcegraph (Optional - Free)

**Why**: Searches across thousands of public repositories
**Cost**: Free

1. Create account at [sourcegraph.com](https://sourcegraph.com)
2. Go to Settings → Access tokens
3. Create new token with appropriate scopes
4. Add to `.env`:
   ```
   SOURCEGRAPH_TOKEN=sgp_your_token_here
   ```

**Rate Limits**: Generous free tier

#### Google Custom Search (Optional - Freemium)

**Why**: Web-wide search with site filtering
**Cost**: Free tier (100 queries/day)

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new project or select existing
   - Enable "Custom Search API"

2. **Create API Key**:
   - Go to "Credentials" → "Create Credentials" → "API Key"
   - Copy API key

3. **Create Custom Search Engine**:
   - Go to [Google CSE](https://cse.google.com/cse/)
   - Click "Add" to create new search engine
   - Add sites to search (or use `*` for entire web)
   - Get Search Engine ID from control panel

4. **Add to `.env`**:
   ```
   GOOGLE_CSE_API_KEY=your_api_key
   GOOGLE_CSE_ID=your_search_engine_id
   ```

**Rate Limits**: 100 queries/day (free), 10,000/day (paid)

#### Bitbucket (Optional - Requires Account)

**Why**: Code snippets and repositories not on GitHub/GitLab
**Cost**: Free with account

1. Create Bitbucket account
2. Go to Personal settings → App passwords
3. Create app password with permissions:
   - Repositories: Read
   - Snippets: Read
4. Add to `.env`:
   ```
   BITBUCKET_USERNAME=your_username
   BITBUCKET_APP_PASSWORD=your_app_password
   ```

#### Have I Been Pwned Pastes (Optional - Paid)

**Why**: Access to breach data and paste dumps
**Cost**: Paid subscription required

1. Subscribe at [haveibeenpwned.com](https://haveibeenpwned.com/API/Key)
2. Get API key from account dashboard
3. Add to `.env`:
   ```
   HIBP_API_KEY=your_api_key
   ```

**Note**: This is the only paid provider, but provides unique breach data

### 3. No-API-Key Providers

These work automatically without setup:

- **Pastebin**: Uses public scraping API
- **Wayback Machine**: Uses Internet Archive's free API

## 🎛️ Configuration Options

### Request Settings

```bash
# Maximum results per provider (1-100)
MAX_RESULTS_PER_PROVIDER=25

# Request timeout in seconds
REQUEST_TIMEOUT=15

# Custom User-Agent string
USER_AGENT=LeakFinder/1.0 (+https://example.com)
```

### Flask Settings

```bash
# Flask secret key (auto-generated if not set)
SECRET_KEY=your-secret-key-here

# Port to run on
PORT=5000

# Debug mode (development only)
FLASK_DEBUG=0
```

## 🧪 Testing Your Setup

### 1. Basic Functionality Test

```bash
python run.py
```

Visit `http://localhost:5000` and run a scan with default settings.

### 2. Provider-Specific Tests

Test each provider individually by:
1. Unchecking all providers except one
2. Running a scan
3. Checking for results or appropriate error messages

### 3. API Key Validation

Check logs for authentication errors:
- GitHub: "Bad credentials" or rate limit messages
- GitLab: 401 Unauthorized
- Shodan: "Invalid API key"
- Google CSE: "API key not valid"

## 🔍 Optimization Tips

### For Best Results

1. **Start with GitHub + GitLab**: Highest quality results
2. **Add Shodan**: For IoT/server exposure data
3. **Use Google CSE**: For web-wide coverage
4. **Enable all free providers**: Maximum coverage

### Performance Tuning

1. **Reduce MAX_RESULTS_PER_PROVIDER**: Faster scans
2. **Increase REQUEST_TIMEOUT**: For slow networks
3. **Selective provider usage**: Disable unused providers

### Rate Limit Management

1. **Stagger scans**: Don't run continuously
2. **Use owner filters**: Reduce search scope
3. **Monitor quotas**: Check provider dashboards

## 🚨 Troubleshooting

### Common Setup Issues

**"Module not found" errors**:
```bash
pip install -r requirements.txt
```

**"Permission denied" on port 5000**:
```bash
export PORT=8080
python run.py
```

**API key not working**:
- Check for extra spaces/newlines in `.env`
- Verify key permissions/scopes
- Check provider documentation for changes

**No results found**:
- Verify internet connectivity
- Check provider status pages
- Try different search terms
- Enable debug mode: `FLASK_DEBUG=1`

### Debug Mode

Enable detailed logging:
```bash
export FLASK_DEBUG=1
python run.py
```

This shows:
- API request/response details
- Error stack traces
- Provider-specific debug info

### Provider Status

Check if providers are operational:
- [GitHub Status](https://www.githubstatus.com/)
- [GitLab Status](https://status.gitlab.com/)
- [Shodan Status](https://status.shodan.io/)
- [Google Cloud Status](https://status.cloud.google.com/)

## 📊 Expected Performance

### Typical Response Times

| Provider | Response Time | Results Quality |
|----------|---------------|-----------------|
| GitHub | 1-3 seconds | High |
| GitLab | 2-4 seconds | High |
| Shodan | 1-2 seconds | Medium |
| Sourcegraph | 2-5 seconds | High |
| Google CSE | 1-3 seconds | Variable |
| Pastebin | 3-8 seconds | Medium |
| Wayback | 5-15 seconds | Low-Medium |
| Bitbucket | 2-4 seconds | Medium |
| HIBP | 1-2 seconds | High |

### Resource Usage

- **Memory**: ~50-100MB during scans
- **CPU**: Low (I/O bound)
- **Network**: ~1-10MB per scan depending on results

## 🔄 Updates and Maintenance

### Keeping API Keys Fresh

- GitHub tokens: Can be set to never expire
- GitLab tokens: Set long expiration dates
- Other providers: Check expiration policies

### Monitoring Usage

Most providers offer usage dashboards:
- GitHub: Settings → Developer settings → Personal access tokens
- Google: Cloud Console → APIs & Services → Quotas
- Shodan: Account page shows query usage

### Updating Dependencies

```bash
pip install -r requirements.txt --upgrade
```

---

**Need help?** Open an issue on GitHub with your setup details (without API keys!).
