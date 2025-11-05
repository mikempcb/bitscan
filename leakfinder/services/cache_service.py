"""
Cache service for managing search result caching.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from ..models.cache import SearchCache

logger = logging.getLogger(__name__)

class CacheService:
    """Service for managing search result caching."""
    
    def __init__(self, cache_duration_hours: int = 24):
        """
        Initialize cache service.
        
        Args:
            cache_duration_hours: Default cache duration in hours
        """
        self.cache_duration_hours = cache_duration_hours
    
    def get_cached_results(self, provider: str, query: str, owner_filter: str = None,
                          language_filter: str = None, pattern_kinds: List[str] = None,
                          scan_depth: str = 'medium') -> Tuple[Optional[List[Dict[str, Any]]], bool]:
        """
        Get cached results for search parameters.
        
        Returns:
            tuple: (results_list, cache_hit) where cache_hit is boolean
        """
        try:
            results, cache_hit = SearchCache.get_cached_results(
                provider=provider,
                query=query,
                owner_filter=owner_filter,
                language_filter=language_filter,
                pattern_kinds=pattern_kinds or [],
                scan_depth=scan_depth
            )
            
            if cache_hit:
                logger.info(f"Cache HIT for {provider} query: {query[:50]}...")
            else:
                logger.info(f"Cache MISS for {provider} query: {query[:50]}...")
            
            return results, cache_hit
            
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None, False
    
    def cache_results(self, provider: str, query: str, results: List[Dict[str, Any]],
                     owner_filter: str = None, language_filter: str = None,
                     pattern_kinds: List[str] = None, scan_depth: str = 'medium') -> bool:
        """
        Cache search results.
        
        Returns:
            bool: True if cached successfully
        """
        try:
            success = SearchCache.cache_results(
                provider=provider,
                query=query,
                results=results,
                owner_filter=owner_filter,
                language_filter=language_filter,
                pattern_kinds=pattern_kinds or [],
                scan_depth=scan_depth,
                cache_duration_hours=self.cache_duration_hours
            )
            
            if success:
                logger.info(f"Cached {len(results)} results for {provider} query: {query[:50]}...")
            else:
                logger.warning(f"Failed to cache results for {provider} query: {query[:50]}...")
            
            return success
            
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
            return False
    
    def search_with_cache(self, provider_search_func, provider: str, query: str,
                         owner_filter: str = None, language_filter: str = None,
                         pattern_kinds: List[str] = None, scan_depth: str = 'medium',
                         **search_kwargs) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Execute search with caching - check cache first, then search if needed.
        
        Args:
            provider_search_func: Function to call for actual search
            provider: Provider name
            query: Search query
            owner_filter: Owner filter
            language_filter: Language filter
            pattern_kinds: List of pattern kinds
            scan_depth: Scan depth level
            **search_kwargs: Additional arguments to pass to search function
            
        Returns:
            tuple: (results_list, cache_hit)
        """
        # Try to get cached results first
        cached_results, cache_hit = self.get_cached_results(
            provider=provider,
            query=query,
            owner_filter=owner_filter,
            language_filter=language_filter,
            pattern_kinds=pattern_kinds,
            scan_depth=scan_depth
        )
        
        if cache_hit and cached_results is not None:
            # Add cache metadata to results
            for result in cached_results:
                result['cached'] = True
                result['cache_hit'] = True
            return cached_results, True
        
        # Cache miss - execute actual search
        try:
            results = provider_search_func(
                query=query,
                owner=owner_filter,
                language=language_filter,
                scan_depth=scan_depth,
                **search_kwargs
            )
            
            # Cache the results
            self.cache_results(
                provider=provider,
                query=query,
                results=results,
                owner_filter=owner_filter,
                language_filter=language_filter,
                pattern_kinds=pattern_kinds,
                scan_depth=scan_depth
            )
            
            # Add cache metadata to results
            for result in results:
                result['cached'] = False
                result['cache_hit'] = False
            
            return results, False
            
        except Exception as e:
            logger.error(f"Search execution failed for {provider}: {e}")
            return [], False
    
    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries."""
        try:
            count = SearchCache.cleanup_expired_cache()
            logger.info(f"Cleaned up {count} expired cache entries")
            return count
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            stats = SearchCache.get_cache_stats()
            return stats
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                'total_entries': 0,
                'active_entries': 0,
                'expired_entries': 0,
                'total_hits': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0,
            }
    
    def invalidate_cache(self, provider: str = None, query_pattern: str = None) -> int:
        """
        Invalidate cache entries matching criteria.
        
        Args:
            provider: Provider name to filter by
            query_pattern: Query pattern to match (partial match)
            
        Returns:
            int: Number of entries invalidated
        """
        try:
            query_filter = SearchCache.query
            
            if provider:
                query_filter = query_filter.filter(SearchCache.provider == provider)
            
            if query_pattern:
                query_filter = query_filter.filter(SearchCache.query.contains(query_pattern))
            
            entries = query_filter.all()
            count = len(entries)
            
            for entry in entries:
                SearchCache.db.session.delete(entry)
            
            SearchCache.db.session.commit()
            logger.info(f"Invalidated {count} cache entries")
            return count
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            SearchCache.db.session.rollback()
            return 0
    
    def get_cache_key(self, provider: str, query: str, owner_filter: str = None,
                     language_filter: str = None, pattern_kinds: List[str] = None,
                     scan_depth: str = 'medium') -> str:
        """Generate cache key for given parameters."""
        return SearchCache.generate_cache_key(
            provider=provider,
            query=query,
            owner_filter=owner_filter,
            language_filter=language_filter,
            pattern_kinds=pattern_kinds or [],
            scan_depth=scan_depth
        )
