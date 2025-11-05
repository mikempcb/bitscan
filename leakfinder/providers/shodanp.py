from typing import List, Dict, Pattern, Any
import re
import requests

from . import BaseProvider


class ShodanProvider(BaseProvider):
    name = 'shodan'

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        api_key = self.app.config.get('SHODAN_API_KEY')
        if not api_key:
            # Graceful message if no key
            return [{
                'provider': self.name,
                'source': 'N/A',
                'artifact': None,
                'preview': 'No SHODAN_API_KEY configured; skipping.',
                'addresses': [],
                'links': [],
            }]

        # default query if none provided
        base_query = query or 'wallet.dat OR keystore OR mnemonic'
        params = {
            'key': api_key,
            'query': base_query,
            'page': 1,
        }
        url = 'https://api.shodan.io/shodan/host/search'
        resp = requests.get(url, params=params, headers=self._headers(), timeout=self.app.config['REQUEST_TIMEOUT'])
        if resp.status_code != 200:
            raise RuntimeError(f'Shodan search failed: {resp.status_code} {resp.text[:200]}')

        data = resp.json()
        matches = data.get('matches', [])
        results: List[Dict[str, Any]] = []
        count = 0

        for m in matches:
            # inspect banner data for leaks
            banner = m.get('data', '')
            host = m.get('ip_str')
            for pat in patterns:
                for mm in re.finditer(pat, banner):
                    val = mm.group(0)
                    preview = self._make_preview(banner, mm.span())
                    results.append({
                        'provider': self.name,
                        'source': host,
                        'artifact': val,
                        'preview': preview,
                        'chain_hint': 'eth' if '0x' in val else 'btc',
                        'links': [f'https://www.shodan.io/host/{host}'],
                    })
                    count += 1
                    if count >= max_results:
                        return results
        return results

    @staticmethod
    def _make_preview(text: str, span):
        start, end = span
        a = max(0, start - 60)
        b = min(len(text), end + 60)
        snippet = text[a:b].replace('\n', ' ')
        return snippet

