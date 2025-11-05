import base64
import re
from typing import List, Dict, Pattern, Any

import requests

from . import BaseProvider


class GitLabProvider(BaseProvider):
    name = 'gitlab'

    def _headers(self) -> Dict[str, str]:
        headers = super()._headers()
        token = self.app.config.get('GITLAB_TOKEN')
        if token:
            headers['PRIVATE-TOKEN'] = token
        return headers

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        # GitLab global search (gitlab.com) - may require token for full results
        base_query = query or 'mnemonic OR keystore OR "wallet.dat" OR xprv OR "PRIVATE KEY"'
        url = 'https://gitlab.com/api/v4/search'
        params = {
            'scope': 'blobs',
            'search': base_query,
            'per_page': min(50, max_results),
        }
        resp = requests.get(url, headers=self._headers(), params=params, timeout=self.app.config['REQUEST_TIMEOUT'])
        if resp.status_code != 200:
            # Be graceful if not authorized or feature limited
            raise RuntimeError(f'GitLab search failed: {resp.status_code} {resp.text[:200]}')

        items = resp.json() if isinstance(resp.json(), list) else []
        results: List[Dict[str, Any]] = []

        for it in items[:max_results]:
            proj = it.get('project_name') or ''
            path = it.get('path') or ''
            # Blob content must be fetched via repository/files API (requires project ID)
            proj_id = it.get('project_id')
            file_path = it.get('path')
            ref = it.get('ref') or 'master'
            if not proj_id or not file_path:
                continue

            file_url = f'https://gitlab.com/api/v4/projects/{proj_id}/repository/files/{requests.utils.quote(file_path, safe="")}?ref={ref}'
            f_resp = requests.get(file_url, headers=self._headers(), timeout=self.app.config['REQUEST_TIMEOUT'])
            if f_resp.status_code != 200:
                continue
            fj = f_resp.json()
            content = fj.get('content', '')
            try:
                text = base64.b64decode(content).decode('utf-8', errors='ignore')
            except Exception:  # noqa: BLE001
                text = ''

            matches = self._find_matches(text, patterns)
            for m in matches:
                preview = self._make_preview(text, m['span'])
                web_url = it.get('url')
                results.append({
                    'provider': self.name,
                    'source': f'{proj}/{path}',
                    'artifact': m['value'],
                    'preview': preview,
                    'chain_hint': m['chain'],
                    'links': [l for l in [web_url] if l],
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

