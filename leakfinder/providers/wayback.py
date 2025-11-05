import re
from typing import List, Dict, Pattern, Any
import requests
from . import BaseProvider


class WaybackProvider(BaseProvider):
    name = 'wayback'

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        # Search Internet Archive's Wayback Machine for archived pages
        # We'll search for common crypto-related file patterns
        
        base_query = query or 'wallet.dat OR keystore OR mnemonic OR "private key"'
        
        # Search for URLs that might contain crypto files
        search_urls = [
            'github.com',
            'gitlab.com',
            'pastebin.com',
            'gist.github.com',
        ]
        
        if owner:
            search_urls = [f'{owner}.github.io', f'github.com/{owner}']

        results: List[Dict[str, Any]] = []
        
        for search_url in search_urls:
            if len(results) >= max_results:
                break
                
            # Use Wayback Machine CDX API to find archived URLs
            cdx_url = 'http://web.archive.org/cdx/search/cdx'
            params = {
                'url': f'{search_url}/*',
                'output': 'json',
                'limit': min(50, max_results),
                'filter': 'statuscode:200',
                'collapse': 'urlkey',
            }
            
            try:
                resp = requests.get(cdx_url, headers=self._headers(), params=params, timeout=self.app.config['REQUEST_TIMEOUT'])
                if resp.status_code != 200:
                    continue
                    
                data = resp.json()
                if not data:
                    continue
                    
                # Skip header row
                for row in data[1:]:
                    if len(results) >= max_results:
                        break
                        
                    if len(row) < 7:
                        continue
                        
                    timestamp = row[1]
                    original_url = row[2]
                    
                    # Filter for potentially interesting URLs
                    url_lower = original_url.lower()
                    if not any(keyword in url_lower for keyword in ['wallet', 'key', 'crypto', 'btc', 'eth', 'mnemonic', '.dat', '.json']):
                        continue
                    
                    # Construct Wayback URL
                    wayback_url = f'http://web.archive.org/web/{timestamp}/{original_url}'
                    
                    # Try to fetch the archived content
                    try:
                        content_resp = requests.get(wayback_url, headers=self._headers(), timeout=self.app.config['REQUEST_TIMEOUT'])
                        if content_resp.status_code == 200:
                            content = content_resp.text[:10000]  # Limit content size
                            matches = self._find_matches(content, patterns)
                            
                            for m in matches:
                                preview = self._make_preview(content, m['span'])
                                results.append({
                                    'provider': self.name,
                                    'source': f'wayback:{original_url}',
                                    'artifact': m['value'],
                                    'preview': preview,
                                    'chain_hint': m['chain'],
                                    'links': [wayback_url, original_url],
                                })
                                
                    except Exception:  # noqa: BLE001
                        continue
                        
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
