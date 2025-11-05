from typing import List, Dict, Pattern, Any
import re
import requests

from . import BaseProvider
from .search_strategies import ShodanStrategies


class ShodanProvider(BaseProvider):
    name = 'shodan'

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        api_key = self.app.config.get('SHODAN_API_KEY')
        if not api_key:
            return [{
                'provider': self.name,
                'source': 'N/A',
                'artifact': None,
                'preview': 'No SHODAN_API_KEY configured; skipping.',
                'addresses': [],
                'links': [],
            }]

        # Get provider settings from database if available
        try:
            from ..models import db, Provider
            db_provider = Provider.query.filter_by(name=self.name).first()
            if db_provider and db_provider.settings:
                settings = db_provider.settings
                # Use advanced query strategies
                strategy = self.app.config.get('SHODAN_STRATEGY', 'wallet_search')
                base_query = ShodanStrategies.build_query(strategy, query)
            else:
                base_query = query or ShodanStrategies.build_query('wallet_search')
        except Exception:
            # Fallback if database not initialized
            base_query = query or ShodanStrategies.build_query('wallet_search')

        params = {
            'key': api_key,
            'query': base_query,
            'page': 1,
        }
        url = 'https://api.shodan.io/shodan/host/search'
        
        try:
            resp = requests.get(url, params=params, headers=self._headers(), timeout=self.app.config['REQUEST_TIMEOUT'])
            if resp.status_code != 200:
                raise RuntimeError(f'Shodan search failed: {resp.status_code} {resp.text[:200]}')
        except Exception as e:
            return [{
                'provider': self.name,
                'source': 'N/A',
                'artifact': None,
                'preview': f'Shodan API error: {str(e)}',
                'addresses': [],
                'links': [],
                'error': True,
            }]

        data = resp.json()
        matches = data.get('matches', [])
        results: List[Dict[str, Any]] = []
        count = 0

        for m in matches:
            # Get comprehensive metadata
            host = m.get('ip_str')
            port = m.get('port')
            transport = m.get('transport', 'tcp')
            product = m.get('product', '')
            banner = m.get('data', '')
            
            # Build metadata
            metadata = {
                'ip': host,
                'port': port,
                'transport': transport,
                'product': product,
                'org': m.get('org'),
                'isp': m.get('isp'),
                'asn': m.get('asn'),
                'hostnames': m.get('hostnames', []),
                'domains': m.get('domains', []),
                'location': {
                    'country': m.get('location', {}).get('country_name'),
                    'city': m.get('location', {}).get('city'),
                },
                'timestamp': m.get('timestamp'),
            }
            
            # Check if there's screenshot
            screenshot_url = None
            if 'opts' in m and 'screenshot' in m['opts']:
                screenshot_url = f"https://screenshots.shodan.io/{m['opts']['screenshot']['hash']}.jpg"
            
            source_url = f'https://www.shodan.io/host/{host}'
            if screenshot_url:
                metadata['screenshot'] = screenshot_url
            
            # Search banner for patterns
            if banner:
                for pat in patterns:
                    for mm in re.finditer(pat, banner):
                        val = mm.group(0)
                        preview = self._make_preview(banner, mm.span())
                        
                        results.append({
                            'provider': self.name,
                            'source': f'{host}:{port}',
                            'source_url': source_url,
                            'source_type': 'host',
                            'artifact': val,
                            'preview': preview,
                            'chain_hint': 'eth' if '0x' in val else 'btc',
                            'links': [source_url],
                            'metadata': metadata,
                            'content': banner[:10000],  # Store first 10KB of banner
                        })
                        count += 1
                        if count >= max_results:
                            return results
            else:
                # No banner but host matches query - store anyway
                results.append({
                    'provider': self.name,
                    'source': f'{host}:{port}',
                    'source_url': source_url,
                    'source_type': 'host',
                    'artifact': None,
                    'preview': f'Host {host}:{port} matched query but no patterns found in banner',
                    'chain_hint': None,
                    'links': [source_url],
                    'metadata': metadata,
                    'content': banner[:10000] if banner else '',
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

