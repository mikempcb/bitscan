import re
from typing import List, Dict, Pattern, Any
import requests
from . import BaseProvider
from .provider_limits import get_max_results
from .search_strategies import GoogleCSEStrategies
from ..utils.scan_depth import ScanDepthManager


class GoogleCSEProvider(BaseProvider):
    name = 'google_cse'

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], 
              max_results: int, scan_depth: str = 'medium') -> List[Dict[str, Any]]:
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

        # Use maximum results for provider
        actual_max_results = min(max_results, get_max_results(self.name))
        
        # Get configured providers to exclude from Google search
        configured_providers = self._get_configured_providers()
        
        # Build search query with exclusions
        base_query = query or 'keystore OR "wallet.dat" OR xprv OR mnemonic OR "private key"'
        
        # Get code hosting sites but exclude configured providers
        all_code_sites = GoogleCSEStrategies.code_hosting_sites()
        excluded_sites = self._get_sites_to_exclude(configured_providers)
        
        # Filter out excluded sites
        allowed_sites = [site for site in all_code_sites if site not in excluded_sites]
        
        # Build query with allowed sites and exclusions
        if allowed_sites:
            site_filters = [f'site:{site}' for site in allowed_sites]
            full_query = f'{base_query} ({" OR ".join(site_filters)})'
        else:
            # If no allowed sites, search broadly but exclude configured sites
            full_query = base_query
            
        # Add exclusions for configured provider sites
        for excluded_site in excluded_sites:
            full_query += f' -site:{excluded_site}'
        
        if owner:
            full_query += f' "{owner}"'

        url = 'https://www.googleapis.com/customsearch/v1'
        params = {
            'key': api_key,
            'cx': search_engine_id,
            'q': full_query,
            'num': min(10, actual_max_results),  # Google CSE max is 10 per request
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
    
    def _get_configured_providers(self) -> List[str]:
        """Get list of configured providers to exclude from Google search."""
        # This would ideally come from the app configuration
        # For now, we'll use a static list of common providers
        return [
            'github',
            'gitlab', 
            'bitbucket',
            'pastebin',
            'sourcegraph',
        ]
    
    def _get_sites_to_exclude(self, configured_providers: List[str]) -> List[str]:
        """Map configured providers to their corresponding sites."""
        provider_site_map = {
            'github': ['github.com', 'gist.github.com'],
            'gitlab': ['gitlab.com'],
            'bitbucket': ['bitbucket.org'],
            'pastebin': ['pastebin.com'],
            'sourcegraph': ['sourcegraph.com'],
        }
        
        excluded_sites = []
        for provider in configured_providers:
            sites = provider_site_map.get(provider, [])
            excluded_sites.extend(sites)
        
        return excluded_sites

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
