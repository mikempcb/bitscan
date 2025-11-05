"""
Strategy likelihood scoring system for search optimization.
"""
from typing import Dict, List, Tuple
from enum import Enum

class StrategyLikelihood(Enum):
    """Strategy likelihood levels."""
    VERY_HIGH = 10
    HIGH = 8
    MEDIUM_HIGH = 6
    MEDIUM = 5
    MEDIUM_LOW = 4
    LOW = 2
    VERY_LOW = 1

class StrategyScorer:
    """Scores and ranks search strategies by likelihood of finding results."""
    
    # Strategy likelihood scores for Shodan
    SHODAN_SCORES = {
        'wallet_search': StrategyLikelihood.VERY_HIGH,      # Direct wallet searches
        'ftp_leaks': StrategyLikelihood.HIGH,               # FTP often has backups
        'directory_listings': StrategyLikelihood.HIGH,      # Exposed directories common
        'backup_files': StrategyLikelihood.MEDIUM_HIGH,     # Backups often contain keys
        'database_dumps': StrategyLikelihood.MEDIUM_HIGH,   # DB dumps may have keys
        'config_files': StrategyLikelihood.MEDIUM,          # Config files sometimes have keys
        'git_exposure': StrategyLikelihood.MEDIUM,          # Git repos may have keys
        'elasticsearch': StrategyLikelihood.MEDIUM_LOW,     # Less common but possible
        'mongodb': StrategyLikelihood.MEDIUM_LOW,           # Less common but possible
        'redis': StrategyLikelihood.LOW,                    # Rarely contains keys directly
        'docker_registries': StrategyLikelihood.LOW,        # Less likely to have keys
        'jupyter': StrategyLikelihood.LOW,                  # Notebooks rarely have keys
        'jenkins': StrategyLikelihood.LOW,                  # CI/CD less likely
        's3_buckets': StrategyLikelihood.VERY_LOW,          # Hard to find via Shodan
    }
    
    # Strategy likelihood scores for GitHub
    GITHUB_SCORES = {
        'wallet_files': StrategyLikelihood.VERY_HIGH,       # Direct wallet file searches
        'private_keys': StrategyLikelihood.HIGH,            # Private key searches
        'config_files': StrategyLikelihood.MEDIUM_HIGH,     # Config files common
        'env_files': StrategyLikelihood.MEDIUM,             # Environment files
        'json_keys': StrategyLikelihood.MEDIUM,             # JSON with keys
        'code_constants': StrategyLikelihood.MEDIUM_LOW,    # Hardcoded keys
        'comments': StrategyLikelihood.LOW,                 # Keys in comments
        'test_files': StrategyLikelihood.LOW,               # Test keys usually fake
    }
    
    # Strategy likelihood scores for Google CSE
    GOOGLE_CSE_SCORES = {
        'wallet_files': StrategyLikelihood.HIGH,            # Direct file searches
        'directory_listings': StrategyLikelihood.MEDIUM_HIGH, # Directory listings
        'paste_sites': StrategyLikelihood.MEDIUM,           # Paste sites
        'forums': StrategyLikelihood.MEDIUM_LOW,            # Forum posts
        'documentation': StrategyLikelihood.LOW,            # Docs rarely have real keys
        'tutorials': StrategyLikelihood.VERY_LOW,           # Tutorial keys usually fake
    }
    
    # Strategy likelihood scores for other providers
    PASTEBIN_SCORES = {
        'direct_search': StrategyLikelihood.HIGH,           # Direct paste searches
        'recent_pastes': StrategyLikelihood.MEDIUM,         # Recent activity
        'user_pastes': StrategyLikelihood.MEDIUM_LOW,       # User-specific searches
    }
    
    @classmethod
    def get_provider_scores(cls, provider_name: str) -> Dict[str, StrategyLikelihood]:
        """Get likelihood scores for a provider's strategies."""
        score_map = {
            'shodan': cls.SHODAN_SCORES,
            'github': cls.GITHUB_SCORES,
            'google_cse': cls.GOOGLE_CSE_SCORES,
            'pastebin': cls.PASTEBIN_SCORES,
        }
        return score_map.get(provider_name, {})
    
    @classmethod
    def score_strategy(cls, provider_name: str, strategy_name: str) -> int:
        """Get likelihood score for a specific strategy."""
        scores = cls.get_provider_scores(provider_name)
        likelihood = scores.get(strategy_name, StrategyLikelihood.MEDIUM)
        return likelihood.value
    
    @classmethod
    def rank_strategies(cls, provider_name: str, strategies: List[str]) -> List[Tuple[str, int]]:
        """Rank strategies by likelihood score (highest first)."""
        scored_strategies = [
            (strategy, cls.score_strategy(provider_name, strategy))
            for strategy in strategies
        ]
        return sorted(scored_strategies, key=lambda x: x[1], reverse=True)
    
    @classmethod
    def filter_by_scan_depth(cls, ranked_strategies: List[Tuple[str, int]], scan_depth: str) -> List[str]:
        """Filter strategies based on scan depth level."""
        depth_limits = {
            'low': 3,      # Top 3 strategies
            'medium': 7,   # Top 7 strategies  
            'high': None,  # All strategies
        }
        
        limit = depth_limits.get(scan_depth.lower(), None)
        if limit is None:
            return [strategy for strategy, _ in ranked_strategies]
        
        return [strategy for strategy, _ in ranked_strategies[:limit]]
    
    @classmethod
    def get_strategy_metadata(cls, provider_name: str, strategy_name: str) -> Dict:
        """Get metadata about a strategy including score and description."""
        score = cls.score_strategy(provider_name, strategy_name)
        
        # Strategy descriptions for UI
        descriptions = {
            'shodan': {
                'wallet_search': 'Direct searches for wallet files and keys',
                'ftp_leaks': 'FTP servers with exposed wallet files',
                'directory_listings': 'Web servers with directory listings',
                'backup_files': 'Backup files that may contain keys',
                'database_dumps': 'Database dumps with potential keys',
                'config_files': 'Configuration files with embedded keys',
                'git_exposure': 'Exposed Git repositories',
                'elasticsearch': 'Elasticsearch instances with data',
                'mongodb': 'MongoDB databases',
                'redis': 'Redis instances',
                'docker_registries': 'Docker registries',
                'jupyter': 'Jupyter notebook servers',
                'jenkins': 'Jenkins CI/CD servers',
                's3_buckets': 'S3 bucket searches',
            },
            'github': {
                'wallet_files': 'Direct wallet file searches',
                'private_keys': 'Private key pattern searches',
                'config_files': 'Configuration file searches',
                'env_files': 'Environment file searches',
                'json_keys': 'JSON files with key patterns',
                'code_constants': 'Hardcoded keys in source code',
                'comments': 'Keys in code comments',
                'test_files': 'Test files (often fake keys)',
            }
        }
        
        provider_descriptions = descriptions.get(provider_name, {})
        description = provider_descriptions.get(strategy_name, f'{strategy_name} search strategy')
        
        return {
            'name': strategy_name,
            'score': score,
            'likelihood': StrategyLikelihood(score).name,
            'description': description,
        }
