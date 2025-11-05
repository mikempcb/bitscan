"""
Scan depth management for controlling search strategy selection.
"""
from typing import List, Dict, Any
from .strategy_scorer import StrategyScorer

class ScanDepthManager:
    """Manages scan depth levels and strategy filtering."""
    
    DEPTH_LEVELS = {
        'low': {
            'name': 'Low',
            'description': 'Quick scan using top 3 most likely strategies per provider',
            'strategy_limit': 3,
            'queries_per_strategy': 1,
            'estimated_time': '1-2 minutes',
        },
        'medium': {
            'name': 'Medium', 
            'description': 'Balanced scan using top 7 strategies per provider',
            'strategy_limit': 7,
            'queries_per_strategy': 2,
            'estimated_time': '3-5 minutes',
        },
        'high': {
            'name': 'High',
            'description': 'Comprehensive scan using all available strategies',
            'strategy_limit': None,  # No limit
            'queries_per_strategy': 3,
            'estimated_time': '5-10 minutes',
        }
    }
    
    @classmethod
    def get_depth_info(cls, depth_level: str) -> Dict[str, Any]:
        """Get information about a scan depth level."""
        return cls.DEPTH_LEVELS.get(depth_level.lower(), cls.DEPTH_LEVELS['medium'])
    
    @classmethod
    def get_available_depths(cls) -> List[Dict[str, Any]]:
        """Get all available scan depth levels."""
        return [
            {
                'value': key,
                'name': info['name'],
                'description': info['description'],
                'estimated_time': info['estimated_time'],
            }
            for key, info in cls.DEPTH_LEVELS.items()
        ]
    
    @classmethod
    def filter_strategies_by_depth(cls, provider_name: str, all_strategies: List[Dict[str, Any]], 
                                 depth_level: str) -> List[Dict[str, Any]]:
        """Filter strategies based on scan depth level."""
        depth_info = cls.get_depth_info(depth_level)
        strategy_limit = depth_info['strategy_limit']
        
        if strategy_limit is None:
            return all_strategies
        
        # Ensure strategies have likelihood scores
        for strategy in all_strategies:
            if 'likelihood_score' not in strategy:
                score = StrategyScorer.score_strategy(provider_name, strategy['name'])
                strategy['likelihood_score'] = score
        
        # Sort by likelihood score and take top N
        sorted_strategies = sorted(all_strategies, key=lambda x: x.get('likelihood_score', 0), reverse=True)
        return sorted_strategies[:strategy_limit]
    
    @classmethod
    def get_queries_per_strategy(cls, depth_level: str) -> int:
        """Get number of queries to execute per strategy."""
        depth_info = cls.get_depth_info(depth_level)
        return depth_info['queries_per_strategy']
    
    @classmethod
    def estimate_total_queries(cls, providers: List[str], depth_level: str) -> int:
        """Estimate total number of queries for a scan."""
        depth_info = cls.get_depth_info(depth_level)
        strategy_limit = depth_info['strategy_limit'] or 10  # Assume average of 10 strategies
        queries_per_strategy = depth_info['queries_per_strategy']
        
        return len(providers) * strategy_limit * queries_per_strategy
    
    @classmethod
    def get_provider_strategy_count(cls, provider_name: str, depth_level: str) -> int:
        """Get expected number of strategies for a provider at given depth."""
        depth_info = cls.get_depth_info(depth_level)
        strategy_limit = depth_info['strategy_limit']
        
        # Provider-specific strategy counts (approximate)
        provider_strategy_counts = {
            'shodan': 14,
            'github': 8,
            'google_cse': 6,
            'pastebin': 3,
            'gitlab': 5,
            'bitbucket': 4,
            'sourcegraph': 5,
            'wayback': 4,
            'hibp_pastes': 3,
        }
        
        total_strategies = provider_strategy_counts.get(provider_name, 5)
        
        if strategy_limit is None:
            return total_strategies
        
        return min(strategy_limit, total_strategies)
