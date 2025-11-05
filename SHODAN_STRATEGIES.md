# Creative Shodan Search Strategies for Crypto Leaks

This document describes creative and effective Shodan search strategies for discovering cryptocurrency wallet leaks, private keys, and mnemonics.

## Understanding Shodan

Shodan is a search engine for Internet-connected devices. Unlike Google which indexes web page content, Shodan indexes banner information from services, making it perfect for finding:
- Misconfigured servers
- Exposed databases
- Directory listings
- Backup files
- Development/staging environments

## Strategy Categories

### 1. FTP Server Leaks

FTP servers often have directory listings enabled, exposing file structures.

**Search Queries:**
```
port:21 "wallet"
port:21 "keystore" 
port:21 "230 Login successful" wallet.dat
port:21 ".dat" directory
port:21 "private" "key"
port:21 "backup" "crypto"
```

**What to Look For:**
- `wallet.dat` files in directory listings
- Backup directories containing wallet files
- User directories with cryptocurrency wallets
- Development/test wallets (often unencrypted)

**Example Banner:**
```
220 FTP Server ready
USER anonymous
331 Please specify the password
PASS anonymous
230 Login successful
LIST
drwxr-xr-x   2 ftp      ftp          4096 Jan 01 12:00 wallets
-rw-r--r--   1 ftp      ftp          1024 Jan 01 12:00 wallet.dat
```

### 2. HTTP Directory Listings

Web servers with directory indexing enabled.

**Search Queries:**
```
http.title:"Index of" wallet
http.title:"Directory Listing" keystore
http.html:"Parent Directory" wallet.dat
http.html:"<title>Index of" private
"Index of /backup" wallet
"Index of" "wallet.json"
"Index of /" ".dat"
http.title:"Index of /" "UTC--"
```

**What to Look For:**
- Backup directories (`/backup`, `/old`, `/archive`)
- User directories (`/home/user/`, `/users/`)
- Application data directories
- Development directories (`/dev`, `/test`, `/staging`)

**Advanced Combinations:**
```
http.title:"Index of" (wallet OR keystore OR mnemonic OR "private key")
http.title:"Directory listing" (.dat OR .json OR UTC--)
```

### 3. Exposed Docker Registries

Docker registries may contain images with wallet files or keys in environment variables.

**Search Queries:**
```
http.component:"Docker Registry"
port:5000 "Docker-Distribution-Api-Version"
"Docker-Distribution-Api-Version: registry" wallet
product:"Docker Registry" crypto
```

**What to Look For:**
- Container images with wallet data
- Environment variables in image manifests
- Build secrets in image layers
- Development images with test keys

**How to Investigate:**
1. Access registry at `http://IP:5000/v2/_catalog`
2. List image tags: `/v2/<image>/tags/list`
3. Get manifest: `/v2/<image>/manifests/<tag>`
4. Look for environment variables and layer contents

### 4. Exposed .git Directories

Git repositories exposed via HTTP reveal source code and commit history.

**Search Queries:**
```
http.html:".git/config"
http.title:"Index of /.git"
".git" wallet
"Index of /.git/objects"
http.html:"[core]" "repositoryformatversion"
```

**What to Look For:**
- Keys committed in code
- Keys in commit history (even if removed later)
- Configuration files with keys
- Environment files (`.env`)
- Key files in `.gitignore` (but still in history)

**How to Investigate:**
1. Download `.git/config` to verify
2. Clone repository: `git clone http://IP/.git/`
3. Search commit history: `git log --all -S "private"`
4. Check all branches: `git branch -a`

### 5. Elasticsearch Instances

Open Elasticsearch databases may contain indexed wallet data.

**Search Queries:**
```
port:9200 "You Know, for Search"
port:9200 wallet
port:9200 keystore
product:"Elastic" wallet
port:9200 "cluster_name" wallet
elasticsearch wallet
```

**What to Look For:**
- Indexed application data
- User records with wallet information
- Transaction logs
- Backup indices

**How to Investigate:**
1. List indices: `GET http://IP:9200/_cat/indices`
2. Search all indices: `GET http://IP:9200/_search?q=wallet`
3. Check specific index: `GET http://IP:9200/index_name/_search?q=private`

### 6. MongoDB Databases

MongoDB instances without authentication.

**Search Queries:**
```
product:"MongoDB" port:27017
"MongoDB server information" wallet
port:27017 "authentication" -"enabled"
mongodb wallet
```

**What to Look For:**
- User collections with wallet data
- Application databases
- Backup collections
- Configuration collections

**How to Investigate:**
```bash
# Connect with mongo client
mongo IP:27017

# List databases
show dbs

# Search for keys
db.users.find({$or: [{"wallet": {$exists: true}}, {"privateKey": {$exists: true}}]})
```

### 7. Redis Instances

Redis instances without authentication.

**Search Queries:**
```
product:"Redis" port:6379
port:6379 -authentication wallet
redis "private_key"
port:6379 "redis_version"
```

**What to Look For:**
- Cached wallet data
- Session data with keys
- Application cache
- Queue data

**How to Investigate:**
```bash
# Connect with redis-cli
redis-cli -h IP

# List all keys
KEYS *

# Search for wallet keys
KEYS *wallet*
KEYS *private*
KEYS *key*

# Get values
GET key_name
```

### 8. S3 Buckets (via SSL Certificates)

Find S3 buckets through SSL certificate Subject Alternative Names.

**Search Queries:**
```
ssl.cert.subject.CN:*.s3.amazonaws.com
ssl.cert.subject.CN:*.s3.*.amazonaws.com
org:"Amazon" has_screenshot:true wallet
asn:AS16509 backup  # Amazon ASN
ssl:"s3.amazonaws.com"
```

**What to Look For:**
- Public S3 buckets
- Misconfigured bucket permissions
- Backup buckets
- Development/staging buckets

**How to Investigate:**
1. Extract bucket name from certificate
2. Try public access: `https://bucket-name.s3.amazonaws.com/`
3. List objects: `aws s3 ls s3://bucket-name --no-sign-request`

### 9. Exposed Backup Files

Backup files left accessible on web servers.

**Search Queries:**
```
http.html:".sql" "backup"
http.html:".dump" wallet
http.title:"backup"
"backup.zip" OR "backup.tar"
http.html:"mysqldump" wallet
"backup" (wallet OR keystore OR private)
filetype:sql wallet
```

**What to Look For:**
- Database dumps (`.sql`, `.dump`)
- Compressed backups (`.zip`, `.tar.gz`, `.7z`)
- Application backups
- User data exports

### 10. Database Dumps

SQL dumps exposed on web servers.

**Search Queries:**
```
http.html:"CREATE TABLE" wallet
http.html:"INSERT INTO" private
".sql" wallet
"mysqldump" wallet
"INSERT INTO users" wallet
```

**What to Look For:**
- User tables with wallet fields
- Transaction tables
- Application database dumps
- Development database dumps

### 11. Configuration Files

Exposed configuration files with hardcoded keys.

**Search Queries:**
```
http.html:".env" OR http.html:"config.php"
http.html:"PRIVATE_KEY"
http.title:"phpinfo()"
"DB_PASSWORD" wallet
config.json private
```

**What to Look For:**
- `.env` files with keys
- `config.php` with database credentials
- `phpinfo()` pages revealing environment variables
- JSON/YAML config files

### 12. Jupyter Notebooks

Jupyter notebooks sometimes contain development keys.

**Search Queries:**
```
http.title:"Jupyter Notebook" port:8888
"Jupyter" wallet OR "Jupyter" private
port:8888 "Jupyter Notebook"
product:"Jupyter Notebook" crypto
```

**What to Look For:**
- Development notebooks with test keys
- API interaction examples with real keys
- Crypto trading analysis with private keys
- Data science projects with wallet data

### 13. Jenkins Servers

Jenkins CI/CD servers may expose build secrets.

**Search Queries:**
```
http.title:"Dashboard [Jenkins]"
product:"Jenkins" wallet
jenkins "credentials" private
port:8080 "Jenkins" crypto
```

**What to Look For:**
- Build environment variables
- Stored credentials
- Build artifacts
- Pipeline secrets

### 14. Rsync Services

Rsync services with open access.

**Search Queries:**
```
port:873 "rsync"
rsync wallet
port:873 "private"
```

**What to Look For:**
- Backup modules
- User home directories
- Application data directories

## Advanced Shodan Filters

### Combining Filters

```
# Specific country + service
port:21 "wallet" country:"US"

# Specific organization + keyword
org:"Digital Ocean" wallet.dat

# Has screenshot (visual confirmation)
has_screenshot:true "Index of" wallet

# Specific ASN (hosting provider)
asn:AS16509 backup  # Amazon

# Before/after dates
port:21 wallet before:01/01/2024

# Multiple ports
port:21,22,80,443 wallet

# Specific product + port
product:"Apache" port:80 "Index of" wallet
```

### Geographic Targeting

```
country:"US" port:9200 wallet
city:"San Francisco" elasticsearch wallet
country:"RU" OR country:"CN" mongodb private
```

### SSL/TLS Targeting

```
ssl.cert.expired:true wallet
ssl.cert.subject.CN:"localhost" wallet
ssl:"self signed" backup
```

### HTTP Response Targeting

```
http.status:200 "Index of" wallet
http.status:403 .git
http.html_hash:XXXXX  # Find similar pages
```

## Responsible Usage Guidelines

⚠️ **IMPORTANT**: Only search for and access data that you are authorized to access.

### Legal Considerations

1. **Permission** - Only access systems you own or have explicit permission to test
2. **Responsible Disclosure** - Report vulnerabilities to system owners
3. **No Exploitation** - Don't extract or use found private keys
4. **Respect Privacy** - Don't access personal data without authorization

### Ethical Research

1. **Educational Purpose** - Use for learning and improving security
2. **Responsible Testing** - Test only on your own systems or with permission
3. **Security Research** - Report findings to help improve security
4. **No Harm** - Don't cause damage or disruption

## Rate Limiting Best Practices

Shodan has strict rate limits:

### Free Tier
- **1 query per second**
- **100 queries per month**

### Membership/API Tiers
- Check current plan limits
- Use query credits wisely
- Cache results locally
- Use specific queries to reduce waste

### Query Optimization

1. **Be Specific** - Use multiple filters to narrow results
2. **Test Queries** - Test on Shodan web interface first
3. **Use Facets** - Analyze with facet to refine before full search
4. **Save Searches** - Save effective queries for reuse
5. **Batch Results** - Process all results from one query before next

## Automation Tips

### Query Rotation

```python
strategies = [
    'port:21 wallet',
    'http.title:"Index of" wallet',
    'port:9200 wallet',
]

for strategy in strategies:
    results = search_shodan(strategy)
    process_results(results)
    time.sleep(2)  # Respect rate limits
```

### Result Caching

```python
import json
from datetime import datetime

def cache_results(query, results):
    cache_file = f"cache_{hash(query)}_{datetime.now().strftime('%Y%m%d')}.json"
    with open(cache_file, 'w') as f:
        json.dump(results, f)
```

### Incremental Searches

```python
# Search by date ranges to avoid duplicates
queries = [
    'wallet after:01/01/2024 before:02/01/2024',
    'wallet after:02/01/2024 before:03/01/2024',
]
```

## Tools Integration

### Shodan CLI

```bash
# Initialize
shodan init YOUR_API_KEY

# Quick search
shodan search "port:21 wallet"

# Download full results
shodan download results.json.gz "port:21 wallet"

# Parse results
shodan parse results.json.gz
```

### Shodan Python API

```python
import shodan

api = shodan.Shodan(API_KEY)

# Search
results = api.search('port:21 wallet')

# Iterate results
for result in results['matches']:
    print(f"IP: {result['ip_str']}")
    print(f"Data: {result['data']}")
```

## Conclusion

Shodan is a powerful tool for discovering exposed services and misconfigurations. When used responsibly and ethically, it can help improve security by identifying vulnerabilities before malicious actors do.

Always remember:
- **Get permission** before accessing any system
- **Report vulnerabilities** responsibly
- **Respect rate limits** to avoid account suspension
- **Use for good** - help improve security, don't exploit weaknesses

