# Configuration Guide

This document describes how to configure BitScan (LeakFinder) with advanced search strategies, rate limiting, and provider-specific settings.

## Table of Contents
- [Database Configuration](#database-configuration)
- [Provider Configuration](#provider-configuration)
- [Search Strategies](#search-strategies)
- [Rate Limiting](#rate-limiting)
- [Pattern Configuration](#pattern-configuration)

## Database Configuration

BitScan now uses SQLAlchemy with SQLite for persistent storage of search results, extracted keys, and wallet addresses.

### Environment Variables

```bash
# Database path (default: instance/leakfinder.db)
DATABASE_PATH=/path/to/leakfinder.db

# Enable SQL query logging (for debugging)
SQL_ECHO=1
```

### Database Initialization

The database is automatically initialized on first run. To manually initialize:

```bash
python -c "from leakfinder import create_app; app = create_app(); app.app_context().push(); from leakfinder.database import init_db; init_db(app)"
```

## Provider Configuration

Each provider has configurable settings stored in the database:

### Provider Settings Table

| Provider | Default Rate Limit | Notes |
|----------|-------------------|-------|
| Shodan | 1 req/sec, 100/day | Free tier limits |
| GitHub | 30 req/min | Authenticated API |
| GitLab | 30 req/min | Authenticated API |
| Google CSE | 100 req/day | Free tier |
| Bitbucket | 60 req/min | |
| Sourcegraph | 20 req/min | |
| Pastebin | 10 req/min | |
| Wayback | 1 req/sec | |
| HIBP Pastes | 10 req/min | |

### Configuring API Keys

Set API keys via environment variables:

```bash
# Required for each provider
SHODAN_API_KEY=your_shodan_key_here
GITHUB_TOKEN=your_github_token_here
GITLAB_TOKEN=your_gitlab_token_here
GOOGLE_CSE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id
HIBP_API_KEY=your_hibp_key_here

# Bitbucket requires username and app password
BITBUCKET_USERNAME=your_username
BITBUCKET_APP_PASSWORD=your_app_password

# Sourcegraph
SOURCEGRAPH_TOKEN=your_sourcegraph_token
```

## Search Strategies

BitScan includes advanced DORK operators and search strategies for each provider.

### Shodan Strategies

Shodan strategies target specific services and misconfigurations:

#### Available Strategies

1. **FTP Leaks** - FTP servers with directory listings
   ```
   port:21 "wallet"
   port:21 "keystore"
   ```

2. **Directory Listings** - Misconfigured web servers
   ```
   http.title:"Index of" wallet
   http.html:"Parent Directory" wallet.dat
   ```

3. **Docker Registries** - Exposed Docker registries
   ```
   http.component:"Docker Registry"
   port:5000 "Docker-Distribution-Api-Version"
   ```

4. **Git Exposure** - Exposed .git directories
   ```
   http.html:".git/config"
   http.title:"Index of /.git"
   ```

5. **Elasticsearch** - Open Elasticsearch instances
   ```
   port:9200 "You Know, for Search"
   port:9200 wallet
   ```

6. **MongoDB** - Exposed MongoDB databases
   ```
   product:"MongoDB" port:27017
   ```

7. **Redis** - Open Redis instances
   ```
   product:"Redis" port:6379
   port:6379 -authentication
   ```

8. **S3 Buckets** - Exposed S3 buckets
   ```
   ssl.cert.subject.CN:*.s3.amazonaws.com
   org:"Amazon" has_screenshot:true wallet
   ```

9. **Backup Files** - Exposed backup files
   ```
   http.html:".sql" "backup"
   "backup.zip" OR "backup.tar"
   ```

10. **Config Files** - Exposed configuration files
    ```
    http.html:".env" OR http.html:"config.php"
    http.html:"PRIVATE_KEY"
    ```

### GitHub Strategies

GitHub code search supports advanced qualifiers:

```
# Search by filename
filename:wallet.dat
filename:keystore extension:json

# Search by path
path:.env PRIVATE_KEY
path:config private_key

# Search by extension
extension:json "private_key"
extension:env ETHEREUM_PRIVATE_KEY

# Search by language
language:Python "ecdsa" "private"
language:JavaScript privateKey

# Search by size
size:>1000 "BEGIN PRIVATE KEY"

# Combine qualifiers
PRIVATE_KEY extension:env path:config language:Text
```

### Google CSE Strategies

Google Custom Search supports these operators:

```
# Site-specific searches
site:github.com wallet.dat
site:pastebin.com "private key"

# File type searches
filetype:json keystore
filetype:env PRIVATE_KEY

# URL patterns
inurl:backup wallet
inurl:.git config

# Title searches
intitle:"index of" wallet
intitle:"directory listing" keystore

# Text searches
intext:"wallet.dat"
intext:"BEGIN PRIVATE KEY"
```

## Rate Limiting

BitScan implements token bucket rate limiting with per-provider limits.

### Rate Limit Windows

- **Per-second** - For high-frequency providers
- **Per-minute** - Standard API rate limits
- **Per-day** - Daily quota limits (Google CSE, Shodan free tier)

### Rate Limit Behavior

1. **Automatic Enforcement** - Requests are blocked when limits are reached
2. **Graceful Degradation** - Error messages explain when limits reset
3. **Persistent Tracking** - Limits persist across application restarts
4. **Per-Provider** - Each provider has independent rate limits

### Checking Rate Limit Status

```python
from leakfinder.utils.rate_limiter import get_rate_limit_status_all

status = get_rate_limit_status_all()
for provider_status in status:
    print(f"{provider_status['provider']}:")
    for limit in provider_status['limits']:
        print(f"  {limit['window']}: {limit['used']}/{limit['limit']} ({limit['remaining']} remaining)")
```

### Resetting Rate Limits (Admin)

```python
from leakfinder.models import db, Provider
from leakfinder.utils.rate_limiter import RateLimiter

provider = Provider.query.filter_by(name='shodan').first()
limiter = RateLimiter(provider)
limiter.reset_all()
```

## Pattern Configuration

BitScan includes sophisticated regex patterns for detecting various key formats.

### Supported Pattern Types

| Type | Description | Example |
|------|-------------|---------|
| `eth_priv` | Ethereum private keys | `0x1234...` |
| `btc_wif` | Bitcoin WIF keys | `5KJvsn...` |
| `xprv` | Extended private keys | `xprv9s21...` |
| `xpub` | Extended public keys | `xpub661...` |
| `mnemonic` | BIP39 mnemonic phrases | `abandon abandon...` |
| `keystore` | Keystore JSON files | `{"crypto": ...}` |
| `base64` | Base64-encoded keys | `SGVsbG8=` |
| `hidden` | Keys in comments/constants | `// 0x1234...` |
| `wallet_files` | File references | `wallet.dat` |
| `pem` | PEM format keys | `-----BEGIN PRIVATE KEY-----` |

### Pattern Examples

#### Ethereum Private Keys
- Standard: `0x1234567890abcdef...` (64 hex chars)
- Without prefix: `1234567890abcdef...`
- In env vars: `PRIVATE_KEY=0x1234...`
- In JSON: `"privateKey": "0x1234..."`
- Split with spaces: `0x 1234 5678 90ab...`

#### Bitcoin WIF
- Uncompressed: `5KJvsngHeMpm884wtkJNzQGaCErckhHJBGFsvd3VyK5qMZXj3hS`
- Compressed: `L1aW4aubDFB7yfras2S1mN3bqg9nwySY8nkoLmJebSLD5BWv3ENZ`
- In env vars: `WIF=5KJvs...`

#### Mnemonics
- 12 words: `abandon abandon abandon ... about`
- 24 words: `abandon abandon abandon ... about`
- Numbered: `1. abandon 2. abandon 3. abandon...`
- Arrays: `["abandon", "abandon", "abandon"...]`

### Configuring Patterns

Patterns can be configured per-provider in the database:

```python
from leakfinder.models import db, Provider, ProviderSettings

provider = Provider.query.filter_by(name='shodan').first()
settings = provider.settings

# Enable specific patterns
settings.enabled_patterns = ['eth_priv', 'btc_wif', 'mnemonic']

# Add custom patterns
settings.custom_patterns = [
    {
        'name': 'custom_key',
        'regex': r'\bCUSTOM[A-Z0-9]{32}\b',
        'description': 'Custom key format'
    }
]

# Adjust context window
settings.context_window_chars = 200  # More context around matches

db.session.commit()
```

### Pattern Sensitivity

- **Low** - Only exact, high-confidence matches
- **Normal** - Balanced between false positives and false negatives (default)
- **High** - Include potential matches with lower confidence

## Advanced Configuration

### Content Snapshot Settings

```python
# Maximum content size to store (KB)
settings.max_content_size_kb = 2048

# Whether to fetch full page content
settings.fetch_full_content = True
```

### Address Derivation Settings

```python
# Automatically derive wallet addresses from keys
settings.auto_derive_addresses = True

# Maximum addresses to derive per key
settings.max_addresses_per_key = 10

# Custom derivation paths (for HD wallets)
settings.derivation_paths = [
    "m/44'/60'/0'/0/0",  # ETH
    "m/44'/0'/0'/0/0",   # BTC
]
```

## Best Practices

1. **Start with Conservative Rate Limits** - Avoid hitting API quotas
2. **Use Specific Queries** - Narrow searches reduce noise and API usage
3. **Enable Only Needed Patterns** - Reduces false positives
4. **Monitor Rate Limit Status** - Check status before large scans
5. **Archive Old Searches** - Use cleanup commands to manage database size
6. **Test Patterns First** - Validate custom patterns on sample data

## Troubleshooting

### Rate Limit Issues

If you're hitting rate limits frequently:
1. Check current status with `get_rate_limit_status_all()`
2. Increase timeout between requests
3. Upgrade to paid API tiers if available
4. Distribute searches across multiple API keys

### Pattern Not Matching

If patterns aren't finding expected keys:
1. Check pattern is enabled in provider settings
2. Verify pattern regex in `patterns.py`
3. Test pattern against sample data
4. Adjust pattern sensitivity
5. Check context window size

### Database Growth

If database grows too large:
1. Run cleanup command to remove old searches
2. Reduce `max_content_size_kb` setting
3. Disable `fetch_full_content` for some providers
4. Archive important results and reset database

