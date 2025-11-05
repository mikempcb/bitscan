import re
from typing import List, Dict, Pattern, Any
import requests
from . import BaseProvider


class PastebinProvider(BaseProvider):
    name = 'pastebin'

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        # Pastebin doesn't have a public search API, but we can use their scraping API
        # This searches recent public pastes
        
        # Get recent pastes list
        url = 'https://scrape.pastebin.com/api_scraping.php'
        params = {
            'limit': min(250, max_results * 5),  # Get more to filter through
        }

        resp = requests.get(url, headers=self._headers(), params=params, timeout=self.app.config['REQUEST_TIMEOUT'])
        if resp.status_code != 200:
            raise RuntimeError(f'Pastebin scraping failed: {resp.status_code} {resp.text[:200]}')

        try:
            pastes = resp.json()
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f'Pastebin response parsing failed: {e}')

        results: List[Dict[str, Any]] = []
        count = 0

        for paste in pastes:
            if count >= max_results:
                break
                
            paste_key = paste.get('key', '')
            title = paste.get('title', '') or 'Untitled'
            
            # Skip if title doesn't seem relevant (basic filtering)
            title_lower = title.lower()
            if not any(keyword in title_lower for keyword in ['key', 'wallet', 'crypto', 'btc', 'eth', 'mnemonic', 'seed']):
                # Still check some pastes even if title doesn't match
                if count % 3 != 0:  # Check every 3rd paste regardless
                    continue

            # Fetch paste content
            paste_url = f'https://scrape.pastebin.com/api_scrape_item.php?i={paste_key}'
            try:
                paste_resp = requests.get(paste_url, headers=self._headers(), timeout=self.app.config['REQUEST_TIMEOUT'])
                if paste_resp.status_code != 200:
                    continue
                    
                content = paste_resp.text
                matches = self._find_matches(content, patterns)
                
                for m in matches:
                    preview = self._make_preview(content, m['span'])
                    web_url = f'https://pastebin.com/{paste_key}'
                    results.append({
                        'provider': self.name,
                        'source': f'pastebin/{paste_key} ({title})',
                        'artifact': m['value'],
                        'preview': preview,
                        'chain_hint': m['chain'],
                        'links': [web_url],
                    })
                    count += 1
                    if count >= max_results:
                        break
                        
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
