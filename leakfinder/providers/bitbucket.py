import re
from typing import List, Dict, Pattern, Any
import requests
from . import BaseProvider


class BitbucketProvider(BaseProvider):
    name = 'bitbucket'

    def _headers(self) -> Dict[str, str]:
        headers = super()._headers()
        # Bitbucket uses basic auth or app passwords
        username = self.app.config.get('BITBUCKET_USERNAME')
        password = self.app.config.get('BITBUCKET_APP_PASSWORD')
        if username and password:
            import base64
            auth_str = base64.b64encode(f'{username}:{password}'.encode()).decode()
            headers['Authorization'] = f'Basic {auth_str}'
        return headers

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        # Bitbucket code search API
        base_query = query or 'keystore OR "wallet.dat" OR xprv OR mnemonic'
        
        # Build search URL
        url = 'https://api.bitbucket.org/2.0/snippets'
        params = {
            'q': base_query,
            'pagelen': min(50, max_results),
        }
        
        # Add owner filter if specified
        if owner:
            params['q'] += f' owner:{owner}'

        resp = requests.get(url, headers=self._headers(), params=params, timeout=self.app.config['REQUEST_TIMEOUT'])
        if resp.status_code != 200:
            raise RuntimeError(f'Bitbucket search failed: {resp.status_code} {resp.text[:200]}')

        data = resp.json()
        snippets = data.get('values', [])
        results: List[Dict[str, Any]] = []

        for snippet in snippets[:max_results]:
            # Get snippet content
            files = snippet.get('files', {})
            for filename, file_info in files.items():
                if 'links' in file_info and 'self' in file_info['links']:
                    content_url = file_info['links']['self']['href']
                    try:
                        content_resp = requests.get(content_url, headers=self._headers(), timeout=self.app.config['REQUEST_TIMEOUT'])
                        if content_resp.status_code == 200:
                            text = content_resp.text
                            matches = self._find_matches(text, patterns)
                            for m in matches:
                                preview = self._make_preview(text, m['span'])
                                web_url = snippet.get('links', {}).get('html', {}).get('href', '')
                                results.append({
                                    'provider': self.name,
                                    'source': f"{snippet.get('owner', {}).get('display_name', 'unknown')}/{filename}",
                                    'artifact': m['value'],
                                    'preview': preview,
                                    'chain_hint': m['chain'],
                                    'links': [web_url] if web_url else [],
                                })
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
