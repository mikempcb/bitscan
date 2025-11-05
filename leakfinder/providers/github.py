import base64
import re
from typing import List, Dict, Pattern, Any
import logging

import requests

from . import BaseProvider
from ..utils.gh_search_wrapper import GhSearchWrapper
from .provider_limits import get_max_results, supports_regex
from .search_strategies import GitHubStrategies
from ..utils.scan_depth import ScanDepthManager

logger = logging.getLogger(__name__)


class GitHubProvider(BaseProvider):
    name = 'github'

    def __init__(self, app):
        super().__init__(app)
        self.github_token = app.config.get('GITHUB_TOKEN')
        self.gh_search = GhSearchWrapper(self.github_token)
        self.use_gh_search = True  # Prefer gh-search over API

    def _headers(self) -> Dict[str, str]:
        headers = super()._headers()
        if self.github_token:
            headers['Authorization'] = f'Bearer {self.github_token}'
        return headers

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], 
              max_results: int, scan_depth: str = 'medium') -> List[Dict[str, Any]]:
        """
        Search GitHub using gh-search CLI with strategy-based approach.
        Falls back to API if gh-search is not available.
        """
        # Use maximum results for provider
        actual_max_results = min(max_results, get_max_results(self.name))
        
        # Try gh-search first if available and regex is supported
        if self.use_gh_search and supports_regex(self.name):
            try:
                return self._search_with_gh_search(query, owner, language, patterns, 
                                                 actual_max_results, scan_depth)
            except Exception as e:
                logger.warning(f"gh-search failed, falling back to API: {e}")
                # Fall through to API search
        
        # Fallback to original API search
        return self._search_with_api(query, owner, language, patterns, actual_max_results)
    
    def _search_with_gh_search(self, query: str, owner: str, language: str, 
                              patterns: List[Pattern], max_results: int, 
                              scan_depth: str) -> List[Dict[str, Any]]:
        """Search using gh-search CLI with multiple strategies."""
        
        # Get GitHub search strategies
        all_strategies = self._get_github_strategies(query, owner, language, patterns)
        
        # Filter strategies by scan depth
        filtered_strategies = ScanDepthManager.filter_strategies_by_depth(
            self.name, all_strategies, scan_depth
        )
        
        # Calculate results per strategy
        results_per_strategy = max(1, max_results // max(1, len(filtered_strategies)))
        
        # Execute searches using gh-search
        gh_results = self.gh_search.search_with_multiple_strategies(
            filtered_strategies, results_per_strategy
        )
        
        # Process results and find pattern matches
        results = []
        for gh_result in gh_results[:max_results]:
            content = gh_result.get('content', '')
            matches = self._find_matches(content, patterns)
            
            for match in matches:
                preview = self._make_preview(content, match['span'])
                results.append({
                    'provider': self.name,
                    'source': f"{gh_result.get('repository', 'unknown')}/{gh_result.get('path', 'unknown')}",
                    'artifact': match['value'],
                    'preview': preview,
                    'chain_hint': match['chain'],
                    'links': [l for l in [gh_result.get('html_url'), gh_result.get('raw_url')] if l],
                    'strategy': gh_result.get('strategy', 'unknown'),
                    'strategy_score': gh_result.get('strategy_score', 0),
                })
        
        return results
    
    def _search_with_api(self, query: str, owner: str, language: str, 
                        patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        """Fallback search using GitHub API."""
        qualifiers = []
        if owner:
            qualifiers.append(f'user:{owner}')
        if language:
            qualifiers.append(f'language:{language}')

        # Use a default keyword set if empty query
        base_query = query or 'mnemonic OR keystore OR "wallet.dat" OR xprv OR "PRIVATE KEY"'
        q = f"{base_query} {' '.join(qualifiers)} in:file"

        per_page = min(100, max_results)  # Use higher limit
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
    
    def _get_github_strategies(self, query: str, owner: str, language: str, 
                              patterns: List[Pattern]) -> List[Dict[str, Any]]:
        """Generate GitHub search strategies based on input parameters."""
        strategies = []
        
        # Strategy 1: Direct wallet file searches
        wallet_queries = GitHubStrategies.wallet_file_queries()
        for i, wallet_query in enumerate(wallet_queries[:3]):  # Limit to top 3
            strategies.append({
                'name': f'wallet_files_{i+1}',
                'query': f'{wallet_query} {query}'.strip(),
                'owner': owner,
                'language': language,
                'use_regex': False,  # Use GitHub qualifiers
                'likelihood_score': 10 - i,  # Decreasing score
            })
        
        # Strategy 2: Private key searches with regex
        if patterns:
            # Convert patterns to regex strings
            pattern_strings = [pattern.pattern if hasattr(pattern, 'pattern') else str(pattern) 
                             for pattern in patterns[:2]]  # Limit patterns
            regex_query = self.gh_search.build_regex_query(pattern_strings, [query] if query else None)
            strategies.append({
                'name': 'private_keys_regex',
                'query': regex_query,
                'owner': owner,
                'language': language,
                'use_regex': True,
                'likelihood_score': 8,
            })
        
        # Strategy 3: Config file searches
        config_queries = GitHubStrategies.config_file_queries()
        for i, config_query in enumerate(config_queries[:2]):  # Limit to top 2
            strategies.append({
                'name': f'config_files_{i+1}',
                'query': f'{config_query} {query}'.strip(),
                'owner': owner,
                'language': language,
                'use_regex': False,
                'likelihood_score': 6 - i,
            })
        
        return strategies

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
