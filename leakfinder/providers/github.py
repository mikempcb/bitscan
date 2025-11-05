import base64
import re
from typing import List, Dict, Pattern, Any

import requests

from . import BaseProvider


class GitHubProvider(BaseProvider):
    name = 'github'

    def _headers(self) -> Dict[str, str]:
        headers = super()._headers()
        token = self.app.config.get('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        # Build a conservative search query that won't exceed URL size and keeps rate low
        # We avoid broad regex; use keyword + qualifiers
        qualifiers = []
        if owner:
            qualifiers.append(f'user:{owner}')
        if language:
            qualifiers.append(f'language:{language}')

        # Use a default keyword set if empty query
        base_query = query or 'mnemonic OR keystore OR "wallet.dat" OR xprv OR "PRIVATE KEY"'
        q = f"{base_query} {' '.join(qualifiers)} in:file"

        per_page = min(50, max_results)
        url = f'https://api.github.com/search/code?q={requests.utils.quote(q)}&per_page={per_page}'
        resp = requests.get(url, headers=self._headers(), timeout=self.app.config['REQUEST_TIMEOUT'])
        if resp.status_code != 200:
            raise RuntimeError(f'GitHub search failed: {resp.status_code} {resp.text[:200]}')
        data = resp.json()
        items = data.get('items', [])

        results: List[Dict[str, Any]] = []

        for it in items[:max_results]:
            repo = it['repository']['full_name']
            path = it['path']
            contents_url = f"https://api.github.com/repos/{repo}/contents/{path}"
            c_resp = requests.get(contents_url, headers=self._headers(), timeout=self.app.config['REQUEST_TIMEOUT'])
            if c_resp.status_code != 200:
                continue
            content_json = c_resp.json()
            if content_json.get('encoding') == 'base64':
                try:
                    text = base64.b64decode(content_json.get('content', '')).decode('utf-8', errors='ignore')
                except Exception:  # noqa: BLE001
                    text = ''
            else:
                text = ''

            matches = self._find_matches(text, patterns)
            for m in matches:
                preview = self._make_preview(text, m['span'])
                raw_url = content_json.get('download_url')
                html_url = content_json.get('html_url')
                results.append({
                    'provider': self.name,
                    'source': f'{repo}/{path}',
                    'artifact': m['value'],
                    'preview': preview,
                    'chain_hint': m['chain'],
                    'links': [l for l in [html_url, raw_url] if l],
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

