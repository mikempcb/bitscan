# Pattern Detection Guide

This document describes the regex patterns used by BitScan to detect cryptocurrency private keys, mnemonics, and wallet files in various formats.

## Table of Contents
- [Pattern Categories](#pattern-categories)
- [Ethereum Private Keys](#ethereum-private-keys)
- [Bitcoin WIF Keys](#bitcoin-wif-keys)
- [Extended Keys (HD Wallets)](#extended-keys-hd-wallets)
- [Mnemonic Phrases](#mnemonic-phrases)
- [Keystore Files](#keystore-files)
- [Hidden and Obfuscated Keys](#hidden-and-obfuscated-keys)
- [Wallet File References](#wallet-file-references)
- [Custom Patterns](#custom-patterns)

## Pattern Categories

BitScan organizes patterns into these categories:

| Category | Pattern Types | Use Case |
|----------|--------------|----------|
| `eth_priv` | Ethereum private keys in various formats | Finding ETH wallet keys |
| `btc_wif` | Bitcoin WIF format private keys | Finding BTC wallet keys |
| `xprv` | Extended private keys (BIP32) | Finding HD wallet master keys |
| `xpub` | Extended public keys | Finding HD wallet public keys |
| `mnemonic` | BIP39 seed phrases | Finding recovery phrases |
| `keystore` | Ethereum keystore files | Finding encrypted wallet files |
| `base64` | Base64-encoded keys | Finding obfuscated keys |
| `hidden` | Keys in comments, constants | Finding hidden keys in code |
| `wallet_files` | Wallet file references | Finding wallet file mentions |
| `pem` | PEM format private keys | Finding general private keys |

## Ethereum Private Keys

Ethereum private keys are 256-bit (32-byte) numbers, typically represented as 64 hexadecimal characters.

### Standard Format (with 0x prefix)

**Pattern:** `\b0x[a-fA-F0-9]{64}\b`

**Examples:**
```
0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

**Common Locations:**
- Environment variables
- Configuration files
- Smart contract deployment scripts
- Test files

### Without 0x Prefix

**Pattern:** `\b[a-fA-F0-9]{64}\b`

**Examples:**
```
1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

**Note:** This pattern may have false positives (any 64-character hex string), so additional validation is performed.

### Split with Whitespace

**Pattern:** `0x[a-fA-F0-9\s]{64,80}`

**Examples:**
```
0x 1234 5678 90ab cdef 1234 5678 90ab cdef 1234 5678 90ab cdef 1234 5678 90ab cdef
0x1234567890abcdef
1234567890abcdef
1234567890abcdef
```

### In Environment Variables

**Pattern:** `(?:PRIVATE_KEY|ETH_KEY|WALLET_KEY)\s*[=:]\s*["\']?(?:0x)?([a-fA-F0-9]{64})["\']?`

**Examples:**
```
PRIVATE_KEY=0x1234567890abcdef...
ETH_KEY: "1234567890abcdef..."
WALLET_KEY='0x1234567890abcdef...'
```

### In JSON Structures

**Pattern:** `["\'](?:privateKey|private_key|privkey)["\']\\s*:\\s*["\'](?:0x)?([a-fA-F0-9]{64})["\']`

**Examples:**
```json
{
  "privateKey": "0x1234567890abcdef...",
  "address": "0xabcd..."
}

{
  "private_key": "1234567890abcdef..."
}
```

## Bitcoin WIF Keys

Bitcoin WIF (Wallet Import Format) keys are base58check-encoded private keys.

### Standard WIF Format

**Pattern:** `\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b`

**Format Details:**
- Starts with `5` (uncompressed) or `K`/`L` (compressed)
- Uses base58 encoding (no 0, O, I, l)
- Length: 51 characters (uncompressed) or 52 characters (compressed)

**Examples:**
```
# Uncompressed (starts with 5)
5KJvsngHeMpm884wtkJNzQGaCErckhHJBGFsvd3VyK5qMZXj3hS

# Compressed (starts with K or L)
L1aW4aubDFB7yfras2S1mN3bqg9nwySY8nkoLmJebSLD5BWv3ENZ
KwDiBf89QgGbjEhKnhXJuH7LrciVrZi3qYjgd9M7rFU73sVHnoWn
```

### Split WIF (with spaces/newlines)

**Pattern:** `[5KL][1-9A-HJ-NP-Za-km-z\s]{50,60}`

**Examples:**
```
5KJvsngHeMpm884wtkJNzQGaCEr
ckhHJBGFsvd3VyK5qMZXj3hS

L1aW 4aub DFB7 yfra s2S1 mN3b qg9n wySY 8nko LmJe bSLD 5BWv 3ENZ
```

### In Environment Variables

**Pattern:** `(?:PRIV(?:ATE)?_KEY|WIF|WALLET_KEY)\s*[=:]\s*["\']?([5KL][1-9A-HJ-NP-Za-km-z]{50,51})["\']?`

**Examples:**
```bash
PRIVATE_KEY=5KJvsngHeMpm884wtkJNzQGaCErckhHJBGFsvd3VyK5qMZXj3hS
WIF="L1aW4aubDFB7yfras2S1mN3bqg9nwySY8nkoLmJebSLD5BWv3ENZ"
```

## Extended Keys (HD Wallets)

BIP32 extended keys allow deriving multiple keys from a single master key.

### Extended Private Keys (xprv, tprv, yprv, zprv)

**Pattern:** `\b(xprv|tprv|yprv|zprv)[1-9A-HJ-NP-Za-km-z]{100,120}\b`

**Key Prefixes:**
- `xprv` - Mainnet, P2PKH/P2SH (BIP32)
- `tprv` - Testnet
- `yprv` - Mainnet, P2WPKH-P2SH (BIP49)
- `zprv` - Mainnet, P2WPKH (BIP84)

**Examples:**
```
xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi

tprv8ZgxMBicQKsPeRZTNJVGPXTaXLQxDYpxYUJN4qJDpfLjhPfVSKRPKVR7UBGb8cVPzKQUxAiQW2MxKQXVgqRdW2ASqyVCFsKKNFKpmmRLwUD

yprv9s21ZrQH143K2JF8RafpqYiYbjYfqVJNdL8pGGJHQZKwKq8ZPrNnqKPPfBM4VGBo7VFvp5EgJK9kJN7kLDLDfCTe5MYmUBBJnCLmMccQJRn
```

### With Derivation Path

**Pattern:** `(m/\d+'?(?:/\d+'?)*)\s*[:\s]+\s*((?:x|t|y|z)prv[1-9A-HJ-NP-Za-km-z]{100,120})`

**Examples:**
```
m/44'/60'/0'/0: xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi

m/44'/0'/0'/0/0
xprv9xpXFhFpqdQK3...
```

### Extended Public Keys (xpub, tpub, ypub, zpub)

**Pattern:** `\b(xpub|tpub|ypub|zpub)[1-9A-HJ-NP-Za-km-z]{100,120}\b`

**Examples:**
```
xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8

zpub6rFR7y4Q2AijBEqTUquhVz398htDFrtymD9xYYfG1m4wAcvPhXNfE3EfH1r1ADqtfSdVCToUG868RvUUkgDKf31mGDtKsAYz2oz2AGutZYs
```

**Note:** While public keys don't directly expose funds, they can reveal wallet addresses and transaction patterns.

## Mnemonic Phrases

BIP39 mnemonic phrases are human-readable backup phrases for wallets.

### Mnemonic Hint Keywords

**Pattern:** `\b(mnemonic|seed phrase|recovery phrase|bip-?39)\b`

**Examples:**
```
Your mnemonic is:
seed phrase:
recovery phrase =
BIP39 seed:
```

### 12-Word Mnemonic

**Pattern:** `\b([a-z]{3,8}\s+){11}[a-z]{3,8}\b`

**Example:**
```
abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about
```

### 24-Word Mnemonic

**Pattern:** `\b([a-z]{3,8}\s+){23}[a-z]{3,8}\b`

**Example:**
```
abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art
```

### Mnemonic in Array Format

**Pattern:** `\[["\']([a-z]+)["\'](?:\s*,\s*["\']([a-z]+)["\']){11,23}\]`

**Examples:**
```javascript
const mnemonic = ["abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "about"];

["abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "abandon", "about"]
```

### Numbered Mnemonic

**Pattern:** `(?:\d+[\.\)]\s*([a-z]{3,8}\s*)){12,24}`

**Examples:**
```
1. abandon
2. abandon
3. abandon
...
12. about

1) abandon 2) abandon 3) abandon ...
```

## Keystore Files

Ethereum keystore files are JSON files containing encrypted private keys.

### UTC Filename Pattern

**Pattern:** `UTC--\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d+Z--[a-fA-F0-9]{40}`

**Examples:**
```
UTC--2023-01-15T10-30-45.123456789Z--1234567890abcdef1234567890abcdef12345678
UTC--2022-12-01T14-22-33.987654321Z--abcdefabcdefabcdefabcdefabcdefabcdefabcd
```

### Keystore JSON Structure

**Pattern:** `\{[^}]*"crypto"\s*:\s*\{[^}]*"cipher"\s*:`

**Example:**
```json
{
  "version": 3,
  "id": "...",
  "address": "1234567890abcdef1234567890abcdef12345678",
  "crypto": {
    "ciphertext": "...",
    "cipherparams": {...},
    "cipher": "aes-128-ctr",
    "kdf": "scrypt",
    "kdfparams": {...},
    "mac": "..."
  }
}
```

### Keystore Keyword Hint

**Pattern:** `\b(keystore|UTC--|encrypted.*key)\b`

## Hidden and Obfuscated Keys

Keys that developers try to hide but are still present in code.

### Base64-Encoded Keys

**Pattern:** `\b([A-Za-z0-9+/]{43}=)\b`

**Examples:**
```
# Base64-encoded 32-byte key
SGVsbG8gV29ybGQgSGVsbG8gV29ybGQgSGVsbG8h=

# In code
const encodedKey = "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=";
```

**Decoding:**
```python
import base64
decoded = base64.b64decode("SGVsbG8gV29ybGQgSGVsbG8gV29ybGQgSGVsbG8h=")
print(decoded.hex())  # Check if it's a valid key
```

### Hex in Comments

**Pattern:** `(?://|#|\*)\s*([a-fA-F0-9]{64})`

**Examples:**
```javascript
// 1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
// Private key (DO NOT COMMIT): ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

# Private key
# ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

/* 
 * Private key: 1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
 */
```

### Keys in Code Constants

**Pattern:** `(?:const|let|var|final|static)\s+\w*(?:key|priv|secret)\w*\s*=\s*["\']([a-fA-F0-9]{64})["\']`

**Examples:**
```javascript
const privateKey = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef";
let ethPrivKey = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";
var secretKey = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890";
```

```python
PRIVATE_KEY = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
SECRET_KEY = "ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
```

```java
private static final String PRIVATE_KEY = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef";
```

## Wallet File References

Patterns that detect mentions of wallet files (which can be downloaded).

### wallet.dat

**Pattern:** `\bwallet\.dat\b`

**Common in:**
- Bitcoin Core
- Litecoin Core
- Dogecoin Core
- Other Bitcoin-derived wallets

### wallet.json

**Pattern:** `\bwallet\.json\b`

**Common in:**
- Custom wallet implementations
- Web3 applications
- Development tools

### Generic Private Key Files

**Pattern:** `\b[\w\-]+\.(?:key|pem|private)\b`

**Examples:**
```
server.key
private.pem
wallet.key
id_rsa
id_ecdsa
ethereum.private
```

## PEM Format Keys

PEM (Privacy Enhanced Mail) format is used for various types of keys.

**Pattern:** `-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]{100,}?-----END (?:RSA |EC )?PRIVATE KEY-----`

**Examples:**
```
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
...
-----END PRIVATE KEY-----

-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIIGlRW8b6eWX/NeNgKwEcHxlDr2fJI7X3qgEzxlnJEqLoAoGCCqGSM49
...
-----END EC PRIVATE KEY-----

-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAwJfzkJFY7tqU6TDNh+jGv2XLpBZuH2z8Ue4CJPxw3h4YZxG4
...
-----END RSA PRIVATE KEY-----
```

## Custom Patterns

You can add custom patterns for specific key formats or application-specific secrets.

### Adding Custom Patterns

```python
from leakfinder.models import db, Provider, ProviderSettings

provider = Provider.query.filter_by(name='shodan').first()
settings = provider.settings

# Add custom pattern
if not settings.custom_patterns:
    settings.custom_patterns = []

settings.custom_patterns.append({
    'name': 'custom_api_key',
    'regex': r'\bapi_key_[A-Za-z0-9]{32}\b',
    'description': 'Custom API key format',
    'enabled': True
})

db.session.commit()
```

### Pattern Testing

Test patterns before deployment:

```python
import re
from leakfinder.utils.patterns import LeakPatterns

# Test pattern
pattern = re.compile(r'\bapi_key_[A-Za-z0-9]{32}\b')
test_text = "The API key is api_key_abc123def456ghi789jkl012mno345pq"

matches = pattern.findall(test_text)
print(f"Found {len(matches)} matches: {matches}")

# Test with context extraction
matches_with_context = LeakPatterns.extract_with_context(test_text, pattern)
for match in matches_with_context:
    print(f"Match: {match['match']}")
    print(f"Context: {match['context_before']} [{match['match']}] {match['context_after']}")
```

## Pattern Validation

BitScan performs additional validation on matches:

### Ethereum Private Key Validation
1. Check length (64 hex characters)
2. Verify hex character set
3. Attempt to derive public key
4. Verify checksum address generation

### Bitcoin WIF Validation
1. Check length (51-52 characters)
2. Verify base58 character set
3. Validate checksum
4. Attempt to derive address

### Mnemonic Validation
1. Check word count (12, 18, or 24)
2. Verify against BIP39 wordlist
3. Validate checksum
4. Test derivation

## Best Practices

### Pattern Design

1. **Be Specific** - Avoid overly broad patterns that cause false positives
2. **Use Word Boundaries** - Use `\b` to avoid partial matches
3. **Capture Groups** - Use capture groups to extract the key value
4. **Test Thoroughly** - Test patterns on real-world data
5. **Document** - Add clear descriptions for custom patterns

### Performance

1. **Optimize Regex** - Use non-capturing groups `(?:...)` where possible
2. **Limit Backtracking** - Avoid patterns with excessive backtracking
3. **Pattern Order** - Put most common patterns first
4. **Context Window** - Use reasonable context window size (120-200 chars)

### Security

1. **Don't Log Keys** - Never log matched key values
2. **Redact Output** - Always redact keys in user-facing output
3. **Secure Storage** - Encrypt database if storing sensitive data
4. **Access Control** - Limit access to found keys

## Troubleshooting

### Pattern Not Matching

1. **Test Regex** - Use regex101.com to test and debug
2. **Check Escaping** - Ensure special characters are properly escaped
3. **Verify Flags** - Check if case-insensitive or multiline flags are needed
4. **Sample Data** - Test with known samples of the target format

### Too Many False Positives

1. **Add Constraints** - Make pattern more specific
2. **Validation** - Add post-match validation logic
3. **Context Analysis** - Check surrounding context for hints
4. **Whitelist** - Exclude known false positive patterns

### Performance Issues

1. **Simplify Pattern** - Break complex patterns into simpler ones
2. **Limit Text Size** - Process text in chunks
3. **Parallel Processing** - Use multi-threading for large datasets
4. **Cache Results** - Cache validation results for duplicate matches

