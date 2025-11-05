import re
from typing import List, Dict, Pattern, Any
import requests
from . import BaseProvider


class SourcegraphProvider(BaseProvider):
    name = 'sourcegraph'

    def _headers(self) -> Dict[str, str]:
        headers = super()._headers()
        token = self.app.config.get('SOURCEGRAPH_TOKEN')
        if token:
            headers['Authorization'] = f'token {token}'
        return headers

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        # Use Sourcegraph.com public API
        base_query = query or 'keystore OR wallet.dat OR xprv OR mnemonic'
        
        # Build search query with filters
        search_terms = [base_query]
        if owner:
            search_terms.append(f'repo:{owner}')
        if language:
            search_terms.append(f'lang:{language}')
        
        full_query = ' '.join(search_terms)
        
        url = 'https://sourcegraph.com/.api/search/stream'
        params = {
            'q': full_query,
            'v': 'V3',
            'sm': '1',  # streaming mode
        }

        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=self.app.config['REQUEST_TIMEOUT'])
            if resp.status_code != 200:
                raise RuntimeError(f'Sourcegraph search failed: {resp.status_code} {resp.text[:200]}')

            results: List[Dict[str, Any]] = []
            
            # Parse streaming JSON responses
            for line in resp.text.strip().split('\n'):
                if not line.strip():
                    continue
                try:
                    import json
                    data = json.loads(line)
                    if data.get('type') == 'matches':
                        for match in data.get('data', []):
                            if match.get('type') == 'content':
                                file_match = match.get('file', {})
                                repo_name = file_match.get('repository', {}).get('name', '')
                                file_path = file_match.get('path', '')
                                
                                for line_match in match.get('lineMatches', []):
                                    line_content = line_match.get('line', '')
                                    matches = self._find_matches(line_content, patterns)
                                    for m in matches:
                                        preview = self._make_preview(line_content, m['span'])
                                        web_url = f"https://sourcegraph.com/{repo_name}/-/blob/{file_path}"
                                        results.append({
                                            'provider': self.name,
                                            'source': f'{repo_name}/{file_path}',
                                            'artifact': m['value'],
                                            'preview': preview,
                                            'chain_hint': m['chain'],
                                            'links': [web_url],
                                        })
                                        if len(results) >= max_results:
                                            return results
                except Exception:  # noqa: BLE001
                    continue
                    
            return results
            
        except Exception as e:  # noqa: BLE001
            # Fallback to regular search API if streaming fails
            return self._fallback_search(full_query, patterns, max_results)

    def _fallback_search(self, query: str, patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        """Fallback to regular Sourcegraph search API"""
        url = 'https://sourcegraph.com/.api/search'
        params = {
            'q': query,
            'v': 'V3',
        }
        
        resp = requests.get(url, headers=self._headers(), params=params, timeout=self.app.config['REQUEST_TIMEOUT'])
        if resp.status_code != 200:
            return []
            
        data = resp.json()
        results: List[Dict[str, Any]] = []
        
        for result in data.get('results', {}).get('results', []):
            if result.get('__typename') == 'FileMatch':
                repo_name = result.get('repository', {}).get('name', '')
                file_path = result.get('file', {}).get('path', '')
                
                for line_match in result.get('lineMatches', []):
                    line_content = line_match.get('line', '')
                    matches = self._find_matches(line_content, patterns)
                    for m in matches:
                        preview = self._make_preview(line_content, m['span'])
                        web_url = f"https://sourcegraph.com/{repo_name}/-/blob/{file_path}"
                        results.append({
                            'provider': self.name,
                            'source': f'{repo_name}/{file_path}',
                            'artifact': m['value'],
                            'preview': preview,
                            'chain_hint': m['chain'],
                            'links': [web_url],
                        })
                        if len(results) >= max_results:
                            return results
        
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
