"""
Wrapper for gh-search CLI tool integration.
"""
import subprocess
import json
import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class GhSearchWrapper:
    """Wrapper for janeklb/gh-search CLI tool."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize with optional GitHub token."""
        self.github_token = github_token
        self._check_gh_search_available()
    
    def _check_gh_search_available(self) -> bool:
        """Check if gh-search CLI is available."""
        try:
            result = subprocess.run(['gh-search', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("gh-search CLI not found, falling back to GitHub API")
            return False
    
    def search_code(self, query: str, max_results: int = 100, 
                   owner: Optional[str] = None, language: Optional[str] = None,
                   use_regex: bool = True) -> List[Dict[str, Any]]:
        """
        Search GitHub code using gh-search CLI.
        
        Args:
            query: Search query (supports regex if use_regex=True)
            max_results: Maximum number of results
            owner: Filter by repository owner
            language: Filter by programming language
            use_regex: Whether to use regex search
            
        Returns:
            List of search results
        """
        try:
            # Build gh-search command
            cmd = ['gh-search']
            
            # Add regex flag if supported
            if use_regex:
                cmd.append('--regex')
            
            # Add qualifiers
            search_parts = [query] if query else []
            
            if owner:
                search_parts.append(f'user:{owner}')
            if language:
                search_parts.append(f'language:{language}')
            
            # Combine search parts
            full_query = ' '.join(search_parts)
            cmd.extend(['--query', full_query])
            
            # Set result limit
            cmd.extend(['--limit', str(max_results)])
            
            # Output format
            cmd.extend(['--format', 'json'])
            
            # Set environment variables if token available
            env = None
            if self.github_token:
                import os
                env = os.environ.copy()
                env['GITHUB_TOKEN'] = self.github_token
            
            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=60, env=env)
            
            if result.returncode != 0:
                logger.error(f"gh-search failed: {result.stderr}")
                return []
            
            # Parse JSON output
            try:
                results = json.loads(result.stdout)
                return self._process_results(results)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse gh-search JSON output: {e}")
                return []
                
        except subprocess.TimeoutExpired:
            logger.error("gh-search command timed out")
            return []
        except Exception as e:
            logger.error(f"gh-search execution failed: {e}")
            return []
    
    def _process_results(self, raw_results: List[Dict]) -> List[Dict[str, Any]]:
        """Process raw gh-search results into standardized format."""
        processed = []
        
        for item in raw_results:
            try:
                # Extract key information
                repo = item.get('repository', {}).get('full_name', 'unknown/unknown')
                path = item.get('path', 'unknown')
                content = item.get('content', '')
                html_url = item.get('html_url', '')
                raw_url = item.get('raw_url', '')
                
                # Create standardized result
                result = {
                    'repository': repo,
                    'path': path,
                    'content': content,
                    'html_url': html_url,
                    'raw_url': raw_url,
                    'score': item.get('score', 0),
                    'matches': item.get('matches', []),
                }
                
                processed.append(result)
                
            except Exception as e:
                logger.warning(f"Failed to process gh-search result: {e}")
                continue
        
        return processed
    
    def build_regex_query(self, patterns: List[str], base_terms: List[str] = None) -> str:
        """
        Build a regex query for gh-search from patterns and terms.
        
        Args:
            patterns: List of regex patterns to search for
            base_terms: Additional search terms
            
        Returns:
            Combined regex query string
        """
        query_parts = []
        
        # Add base terms
        if base_terms:
            query_parts.extend(base_terms)
        
        # Add regex patterns (combine with OR)
        if patterns:
            # Escape special regex characters for gh-search
            escaped_patterns = []
            for pattern in patterns:
                # Convert Python regex to gh-search compatible format
                escaped = self._escape_regex_for_gh_search(pattern)
                escaped_patterns.append(escaped)
            
            if len(escaped_patterns) == 1:
                query_parts.append(escaped_patterns[0])
            else:
                # Combine multiple patterns with OR
                combined_pattern = '(' + '|'.join(escaped_patterns) + ')'
                query_parts.append(combined_pattern)
        
        return ' '.join(query_parts)
    
    def _escape_regex_for_gh_search(self, pattern: str) -> str:
        """
        Escape regex pattern for gh-search compatibility.
        
        gh-search uses ripgrep under the hood, so we need to ensure
        the regex is compatible with ripgrep's regex engine.
        """
        # Basic escaping for common cases
        # This is a simplified version - may need refinement
        
        # Remove Python-specific regex features that ripgrep doesn't support
        pattern = pattern.replace('(?:', '(')  # Non-capturing groups
        pattern = pattern.replace('(?=', '(')  # Positive lookahead (not supported)
        pattern = pattern.replace('(?!', '(')  # Negative lookahead (not supported)
        
        return pattern
    
    def search_with_multiple_strategies(self, strategies: List[Dict[str, Any]], 
                                      max_results_per_strategy: int = 50) -> List[Dict[str, Any]]:
        """
        Execute multiple search strategies and combine results.
        
        Args:
            strategies: List of strategy dictionaries with query info
            max_results_per_strategy: Max results per individual strategy
            
        Returns:
            Combined list of all results
        """
        all_results = []
        
        for strategy in strategies:
            try:
                query = strategy.get('query', '')
                owner = strategy.get('owner')
                language = strategy.get('language')
                use_regex = strategy.get('use_regex', True)
                
                results = self.search_code(
                    query=query,
                    max_results=max_results_per_strategy,
                    owner=owner,
                    language=language,
                    use_regex=use_regex
                )
                
                # Add strategy metadata to results
                for result in results:
                    result['strategy'] = strategy.get('name', 'unknown')
                    result['strategy_score'] = strategy.get('likelihood_score', 0)
                
                all_results.extend(results)
                
            except Exception as e:
                logger.error(f"Strategy '{strategy.get('name')}' failed: {e}")
                continue
        
        # Remove duplicates based on repository + path
        seen = set()
        unique_results = []
        for result in all_results:
            key = f"{result.get('repository', '')}/{result.get('path', '')}"
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results
