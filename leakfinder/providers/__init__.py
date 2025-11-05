from typing import List, Dict, Pattern, Any


class BaseProvider:
    name = "base"

    def __init__(self, app):
        self.app = app

    def _headers(self) -> Dict[str, str]:
        ua = self.app.config.get('USER_AGENT') or 'LeakFinder/1.0'
        return {
            'Accept': 'application/vnd.github+json',
            'User-Agent': ua,
        }

    def search(self, query: str, owner: str, language: str, patterns: List[Pattern], max_results: int) -> List[Dict[str, Any]]:
        raise NotImplementedError

