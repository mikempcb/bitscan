import re
import base64
from typing import List, Pattern, Dict, Any, Tuple


class LeakPatterns:
    """
    Advanced regex patterns for detecting cryptocurrency keys and mnemonics.
    Includes patterns for various encodings, obfuscation, and hidden formats.
    """
    
    # ===================== Bitcoin WIF Keys =====================
    # Standard WIF (uncompressed: 51 chars, compressed: 52 chars)
    BTC_WIF = re.compile(r"\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b")
    
    # WIF with common separators (spaces, newlines, etc.)
    BTC_WIF_SPLIT = re.compile(r"[5KL][1-9A-HJ-NP-Za-km-z\s]{50,60}", re.MULTILINE)
    
    # WIF in JSON/quotes
    BTC_WIF_QUOTED = re.compile(r'["\']([5KL][1-9A-HJ-NP-Za-km-z]{50,51})["\']')
    
    # WIF in environment variables or config
    BTC_WIF_ENV = re.compile(r'(?:PRIV(?:ATE)?_KEY|WIF|WALLET_KEY)\s*[=:]\s*["\']?([5KL][1-9A-HJ-NP-Za-km-z]{50,51})["\']?', re.IGNORECASE)
    
    # ===================== Ethereum Private Keys =====================
    # With 0x prefix
    ETH_PRIVKEY = re.compile(r"\b0x[a-fA-F0-9]{64}\b")
    
    # Without 0x prefix (64 hex chars)
    ETH_PRIVKEY_HEX = re.compile(r"\b[a-fA-F0-9]{64}\b")
    
    # With spaces or formatting
    ETH_PRIVKEY_SPLIT = re.compile(r"0x[a-fA-F0-9\s]{64,80}", re.MULTILINE)
    
    # In quotes or config
    ETH_PRIVKEY_QUOTED = re.compile(r'["\'](?:0x)?([a-fA-F0-9]{64})["\']')
    
    # In environment variables
    ETH_PRIVKEY_ENV = re.compile(r'(?:PRIVATE_KEY|ETH_KEY|WALLET_KEY)\s*[=:]\s*["\']?(?:0x)?([a-fA-F0-9]{64})["\']?', re.IGNORECASE)
    
    # In JSON structures
    ETH_PRIVKEY_JSON = re.compile(r'["\'](?:privateKey|private_key|privkey)["\']\\s*:\\s*["\'](?:0x)?([a-fA-F0-9]{64})["\']', re.IGNORECASE)
    
    # ===================== Extended Keys (xprv, xpub, etc.) =====================
    # Standard xprv
    XPRV = re.compile(r"\b(xprv|tprv|yprv|zprv)[1-9A-HJ-NP-Za-km-z]{100,120}\b")
    
    # With derivation path context
    XPRV_WITH_PATH = re.compile(r"(m/\d+'?(?:/\d+'?)*)\s*[:\s]+\s*((?:x|t|y|z)prv[1-9A-HJ-NP-Za-km-z]{100,120})", re.IGNORECASE)
    
    # xpub (public extended keys - still valuable)
    XPUB = re.compile(r"\b(xpub|tpub|ypub|zpub)[1-9A-HJ-NP-Za-km-z]{100,120}\b")
    
    # ===================== Mnemonic Phrases (BIP39) =====================
    # Common BIP39 word patterns (looking for sequences of common words)
    # This is a simplified pattern - real implementation should check against BIP39 wordlist
    MNEMONIC_HINT = re.compile(r"\b(mnemonic|seed phrase|recovery phrase|bip-?39)\b", re.IGNORECASE)
    
    # Detect 12/18/24 word sequences (common English words)
    MNEMONIC_12_WORDS = re.compile(r"\b([a-z]{3,8}\s+){11}[a-z]{3,8}\b", re.IGNORECASE)
    MNEMONIC_24_WORDS = re.compile(r"\b([a-z]{3,8}\s+){23}[a-z]{3,8}\b", re.IGNORECASE)
    
    # Mnemonic in arrays/lists
    MNEMONIC_ARRAY = re.compile(r'\[["\']([a-z]+)["\'](?:\s*,\s*["\']([a-z]+)["\']){11,23}\]', re.IGNORECASE)
    
    # Mnemonic with numbers (1. word 2. word ...)
    MNEMONIC_NUMBERED = re.compile(r'(?:\d+[\.\)]\s*([a-z]{3,8}\s*)){12,24}', re.IGNORECASE)
    
    # ===================== Keystore Files =====================
    # UTC filename pattern
    KEYSTORE_FILENAME = re.compile(r"UTC--\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d+Z--[a-fA-F0-9]{40}")
    
    # Keystore JSON structure
    KEYSTORE_JSON = re.compile(r'\{[^}]*"crypto"\s*:\s*\{[^}]*"cipher"\s*:', re.IGNORECASE)
    
    # Simple keystore hint
    KEYSTORE_HINT = re.compile(r"\b(keystore|UTC--|encrypted.*key)\b", re.IGNORECASE)
    
    # ===================== Hidden/Encoded Patterns =====================
    # Base64-encoded private keys (common obfuscation)
    # Base64 string that decodes to 32 bytes (64 hex chars)
    BASE64_KEY_CANDIDATE = re.compile(r"\b([A-Za-z0-9+/]{43}=)\b")  # 32 bytes = 43 base64 chars + 1 padding
    
    # Hex in comments
    HEX_IN_COMMENT = re.compile(r'(?://|#|\*)\s*([a-fA-F0-9]{64})', re.MULTILINE)
    
    # Keys in code constants
    CONST_PATTERN = re.compile(r'(?:const|let|var|final|static)\s+\w*(?:key|priv|secret)\w*\s*=\s*["\']([a-fA-F0-9]{64})["\']', re.IGNORECASE)
    
    # ===================== Wallet Files =====================
    WALLET_DAT = re.compile(r'\bwallet\.dat\b', re.IGNORECASE)
    WALLET_JSON = re.compile(r'\bwallet\.json\b', re.IGNORECASE)
    PRIVATE_KEY_FILE = re.compile(r'\b[\w\-]+\.(?:key|pem|private)\b', re.IGNORECASE)
    
    # ===================== PEM Format Private Keys =====================
    PEM_PRIVATE_KEY = re.compile(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]{100,}?-----END (?:RSA |EC )?PRIVATE KEY-----')
    
    @classmethod
    def build(cls, kinds: List[str] = None) -> List[Dict[str, Any]]:
        """
        Build a list of pattern dictionaries for the specified kinds.
        Each dict contains: {'name': str, 'pattern': Pattern, 'description': str}
        """
        patterns: List[Dict[str, Any]] = []
        
        if not kinds:
            kinds = ['eth_priv', 'btc_wif', 'xprv', 'xpub', 'mnemonic', 'keystore', 'base64', 'wallet_files']
        
        if 'eth_priv' in kinds:
            patterns.extend([
                {'name': 'eth_privkey', 'pattern': cls.ETH_PRIVKEY, 'description': 'Ethereum private key with 0x'},
                {'name': 'eth_privkey_hex', 'pattern': cls.ETH_PRIVKEY_HEX, 'description': 'Ethereum private key (64 hex chars)'},
                {'name': 'eth_privkey_split', 'pattern': cls.ETH_PRIVKEY_SPLIT, 'description': 'Ethereum private key with spacing'},
                {'name': 'eth_privkey_env', 'pattern': cls.ETH_PRIVKEY_ENV, 'description': 'Ethereum private key in env var'},
                {'name': 'eth_privkey_json', 'pattern': cls.ETH_PRIVKEY_JSON, 'description': 'Ethereum private key in JSON'},
            ])
        
        if 'btc_wif' in kinds:
            patterns.extend([
                {'name': 'btc_wif', 'pattern': cls.BTC_WIF, 'description': 'Bitcoin WIF private key'},
                {'name': 'btc_wif_split', 'pattern': cls.BTC_WIF_SPLIT, 'description': 'Bitcoin WIF with spacing'},
                {'name': 'btc_wif_env', 'pattern': cls.BTC_WIF_ENV, 'description': 'Bitcoin WIF in env var'},
            ])
        
        if 'xprv' in kinds:
            patterns.extend([
                {'name': 'xprv', 'pattern': cls.XPRV, 'description': 'Extended private key (xprv/tprv/yprv/zprv)'},
                {'name': 'xprv_with_path', 'pattern': cls.XPRV_WITH_PATH, 'description': 'Extended private key with derivation path'},
            ])
        
        if 'xpub' in kinds:
            patterns.append(
                {'name': 'xpub', 'pattern': cls.XPUB, 'description': 'Extended public key'}
            )
        
        if 'mnemonic' in kinds:
            patterns.extend([
                {'name': 'mnemonic_hint', 'pattern': cls.MNEMONIC_HINT, 'description': 'Mnemonic keyword hint'},
                {'name': 'mnemonic_12', 'pattern': cls.MNEMONIC_12_WORDS, 'description': '12-word mnemonic phrase'},
                {'name': 'mnemonic_24', 'pattern': cls.MNEMONIC_24_WORDS, 'description': '24-word mnemonic phrase'},
                {'name': 'mnemonic_array', 'pattern': cls.MNEMONIC_ARRAY, 'description': 'Mnemonic in array format'},
                {'name': 'mnemonic_numbered', 'pattern': cls.MNEMONIC_NUMBERED, 'description': 'Numbered mnemonic phrase'},
            ])
        
        if 'keystore' in kinds:
            patterns.extend([
                {'name': 'keystore_filename', 'pattern': cls.KEYSTORE_FILENAME, 'description': 'Keystore UTC filename'},
                {'name': 'keystore_json', 'pattern': cls.KEYSTORE_JSON, 'description': 'Keystore JSON structure'},
                {'name': 'keystore_hint', 'pattern': cls.KEYSTORE_HINT, 'description': 'Keystore keyword hint'},
            ])
        
        if 'base64' in kinds:
            patterns.append(
                {'name': 'base64_key', 'pattern': cls.BASE64_KEY_CANDIDATE, 'description': 'Base64-encoded key candidate'}
            )
        
        if 'hidden' in kinds:
            patterns.extend([
                {'name': 'hex_in_comment', 'pattern': cls.HEX_IN_COMMENT, 'description': 'Hex key in comment'},
                {'name': 'const_pattern', 'pattern': cls.CONST_PATTERN, 'description': 'Key in code constant'},
            ])
        
        if 'wallet_files' in kinds:
            patterns.extend([
                {'name': 'wallet_dat', 'pattern': cls.WALLET_DAT, 'description': 'wallet.dat file reference'},
                {'name': 'wallet_json', 'pattern': cls.WALLET_JSON, 'description': 'wallet.json file reference'},
                {'name': 'private_key_file', 'pattern': cls.PRIVATE_KEY_FILE, 'description': 'Private key file reference'},
            ])
        
        if 'pem' in kinds:
            patterns.append(
                {'name': 'pem_private_key', 'pattern': cls.PEM_PRIVATE_KEY, 'description': 'PEM format private key'}
            )
        
        return patterns
    
    @staticmethod
    def try_decode_base64(text: str) -> Tuple[bool, str]:
        """
        Attempt to decode base64 text and check if it looks like a key.
        Returns: (is_likely_key, decoded_hex)
        """
        try:
            # Try to decode
            decoded = base64.b64decode(text, validate=True)
            
            # Check if it's 32 bytes (256 bits - common key size)
            if len(decoded) == 32:
                hex_decoded = decoded.hex()
                # Check if it looks like valid hex
                if all(c in '0123456789abcdefABCDEF' for c in hex_decoded):
                    return True, hex_decoded
            
            return False, ''
        except Exception:
            return False, ''
    
    @staticmethod
    def extract_with_context(text: str, pattern: Pattern, context_chars: int = 120) -> List[Dict[str, Any]]:
        """
        Extract matches with surrounding context.
        Returns list of dicts with: match, start, end, context_before, context_after, full_line
        """
        matches = []
        lines = text.split('\n')
        
        for match in re.finditer(pattern, text):
            start, end = match.span()
            matched_text = match.group(0)
            
            # Get context
            context_start = max(0, start - context_chars)
            context_end = min(len(text), end + context_chars)
            context_before = text[context_start:start]
            context_after = text[end:context_end]
            
            # Find line number
            line_num = text[:start].count('\n') + 1
            
            # Get full line
            if line_num <= len(lines):
                full_line = lines[line_num - 1]
            else:
                full_line = matched_text
            
            matches.append({
                'match': matched_text,
                'groups': match.groups() if match.groups() else [],
                'start': start,
                'end': end,
                'context_before': context_before,
                'context_after': context_after,
                'full_line': full_line,
                'line_number': line_num,
            })
        
        return matches
    
    @classmethod
    def determine_key_type(cls, matched_text: str) -> str:
        """Determine the type of key from matched text."""
        if cls.ETH_PRIVKEY.match(matched_text) or cls.ETH_PRIVKEY_HEX.match(matched_text):
            return 'eth_priv'
        elif cls.BTC_WIF.match(matched_text):
            return 'btc_wif'
        elif cls.XPRV.match(matched_text):
            return 'xprv'
        elif cls.XPUB.match(matched_text):
            return 'xpub'
        elif cls.MNEMONIC_12_WORDS.match(matched_text) or cls.MNEMONIC_24_WORDS.match(matched_text):
            return 'mnemonic'
        elif cls.KEYSTORE_JSON.match(matched_text):
            return 'keystore'
        elif cls.BASE64_KEY_CANDIDATE.match(matched_text):
            return 'base64_encoded'
        else:
            return 'unknown'

