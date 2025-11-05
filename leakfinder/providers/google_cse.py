import re
from typing import List, Dict, Pattern, Any
import requests
from . import BaseProvider


class GoogleCSEProvider(BaseProvider):
    name = 'google_cse'

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        api_key = self.app.config.get('GOOGLE_CSE_API_KEY')
        search_engine_id = self.app.config.get('GOOGLE_CSE_ID')
        
        if not api_key or not search_engine_id:
            return [{
                'provider': self.name,
                'source': 'N/A',
                'artifact': None,
                'preview': 'No GOOGLE_CSE_API_KEY or GOOGLE_CSE_ID configured; skipping.',
                'addresses': [],
                'links': [],
            }]

        # Build search query
        base_query = query or 'keystore OR "wallet.dat" OR xprv OR mnemonic OR "private key"'
        
        # Add site filters for common code/paste sites
        site_filters = [
            'site:github.com',
            'site:gitlab.com', 
            'site:pastebin.com',
            'site:gist.github.com',
            'site:bitbucket.org',
            'site:codeberg.org'
        ]
        
        full_query = f'{base_query} ({" OR ".join(site_filters)})'
        
        if owner:
            full_query += f' "{owner}"'

        url = 'https://www.googleapis.com/customsearch/v1'
        params = {
            'key': api_key,
            'cx': search_engine_id,
            'q': full_query,
            'num': min(10, max_results),  # Google CSE max is 10 per request
        }

        resp = requests.get(url, headers=self._headers(), params=params, timeout=self.app.config['REQUEST_TIMEOUT'])
        if resp.status_code != 200:
            raise RuntimeError(f'Google CSE search failed: {resp.status_code} {resp.text[:200]}')

        data = resp.json()
        items = data.get('items', [])
        results: List[Dict[str, Any]] = []

        for item in items:
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            link = item.get('link', '')
            
            # Try to fetch the actual page content for better pattern matching
            try:
                page_resp = requests.get(link, headers=self._headers(), timeout=5)
                if page_resp.status_code == 200:
                    content = page_resp.text[:10000]  # Limit content size
                else:
                    content = snippet
            except Exception:  # noqa: BLE001
                content = snippet

            matches = self._find_matches(content, patterns)
            for m in matches:
                preview = self._make_preview(content, m['span'])
                results.append({
                    'provider': self.name,
                    'source': title or link,
                    'artifact': m['value'],
                    'preview': preview,
                    'chain_hint': m['chain'],
                    'links': [link],
                })

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
