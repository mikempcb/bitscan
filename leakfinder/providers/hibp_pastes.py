import re
from typing import List, Dict, Pattern, Any
import requests
from . import BaseProvider


class HIBPPastesProvider(BaseProvider):
    name = 'hibp_pastes'

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        # Have I Been Pwned Pastes API - searches for email addresses in pastes
        # This is a bit different - we'll search for common crypto-related email domains
        
        api_key = self.app.config.get('HIBP_API_KEY')
        if not api_key:
            return [{
                'provider': self.name,
                'source': 'N/A',
                'artifact': None,
                'preview': 'No HIBP_API_KEY configured; skipping.',
                'addresses': [],
                'links': [],
            }]

        # Common email domains used in crypto projects/exchanges
        crypto_domains = [
            'blockchain.com',
            'coinbase.com', 
            'binance.com',
            'crypto.com',
            'metamask.io',
            'ethereum.org',
            'bitcoin.org',
        ]
        
        # If owner is specified, try that as an email domain
        if owner and '.' in owner:
            crypto_domains = [owner]
        elif owner:
            crypto_domains = [f'{owner}.com', f'{owner}.io', f'{owner}.org']

        results: List[Dict[str, Any]] = []
        
        for domain in crypto_domains:
            if len(results) >= max_results:
                break
                
            # Try common email prefixes
            email_prefixes = ['admin', 'support', 'info', 'wallet', 'api', 'dev']
            
            for prefix in email_prefixes:
                if len(results) >= max_results:
                    break
                    
                email = f'{prefix}@{domain}'
                
                url = f'https://haveibeenpwned.com/api/v3/pasteaccount/{email}'
                headers = self._headers()
                headers['hibp-api-key'] = api_key
                
                try:
                    resp = requests.get(url, headers=headers, timeout=self.app.config['REQUEST_TIMEOUT'])
                    if resp.status_code == 200:
                        pastes = resp.json()
                        
                        for paste in pastes:
                            paste_id = paste.get('Id', '')
                            title = paste.get('Title', '') or 'Untitled'
                            source = paste.get('Source', '')
                            
                            # Try to fetch paste content if it's from a known source
                            content = ''
                            paste_url = ''
                            
                            if source == 'Pastebin' and paste_id:
                                paste_url = f'https://pastebin.com/raw/{paste_id}'
                                try:
                                    paste_resp = requests.get(paste_url, headers=self._headers(), timeout=5)
                                    if paste_resp.status_code == 200:
                                        content = paste_resp.text[:5000]  # Limit content
                                except Exception:  # noqa: BLE001
                                    pass
                            
                            # If we have content, search for patterns
                            if content:
                                matches = self._find_matches(content, patterns)
                                for m in matches:
                                    preview = self._make_preview(content, m['span'])
                                    results.append({
                                        'provider': self.name,
                                        'source': f'{source}/{paste_id} ({title})',
                                        'artifact': m['value'],
                                        'preview': preview,
                                        'chain_hint': m['chain'],
                                        'links': [paste_url] if paste_url else [],
                                    })
                            else:
                                # No content available, just report the paste exists
                                results.append({
                                    'provider': self.name,
                                    'source': f'{source}/{paste_id} ({title})',
                                    'artifact': None,
                                    'preview': f'Paste found containing {email} - content not accessible',
                                    'chain_hint': None,
                                    'links': [],
                                })
                                
                    elif resp.status_code == 404:
                        # No pastes found for this email
                        continue
                    else:
                        # Rate limited or other error
                        break
                        
                except Exception:  # noqa: BLE001
                    continue

        return results

    @staticmethod
    def _find_matches(text: str, patterns: List[Pattern]):
        found = []
        for pat in patterns:
            for m in re.finditer(pat, text):
                val = m.group(0)
                chain = 'eth' if '0x' in val or re.fullmatch(r'[a-fA-F0-9]{64}', val or '') else 'btc'
                found.append({'value': val, 'span': m.span(), 'chain': chain})
        return found

    @staticmethod
    def _make_preview(text: str, span):
        start, end = span
        a = max(0, start - 60)
        b = min(len(text), end + 60)
        snippet = text[a:b].replace('\n', ' ')
        return snippet
