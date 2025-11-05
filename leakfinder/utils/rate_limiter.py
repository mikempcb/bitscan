"""
Rate limiting utility for API providers with token bucket algorithm.
"""
import time
from datetime import datetime
from typing import Optional
from ..models import db, Provider
# TODO: Create RateLimit model when needed
# from ..models import RateLimit


class RateLimiter:
    """
    Token bucket rate limiter for API providers.
    Supports per-second, per-minute, per-hour, and per-day limits.
    """
    
    def __init__(self, provider: Provider):
        self.provider = provider
        self.provider_id = provider.id
    
    def can_make_request(self) -> tuple[bool, Optional[str]]:
        """
        Check if a request can be made without exceeding rate limits.
        
        Returns:
            (can_proceed, reason_if_not)
        """
        # Check all configured rate limit windows
        checks = []
        
        if self.provider.rate_limit_per_second:
            checks.append(('second', self.provider.rate_limit_per_second))
        
        if self.provider.rate_limit_per_minute:
            checks.append(('minute', self.provider.rate_limit_per_minute))
        
        if self.provider.rate_limit_per_day:
            checks.append(('day', self.provider.rate_limit_per_day))
        
        # If no rate limits configured, allow the request
        if not checks:
            return True, None
        
        # Check each rate limit window
        for window_type, limit in checks:
            rate_limit = RateLimit.get_or_create_window(
                self.provider_id,
                window_type,
                int(limit)
            )
            
            if not rate_limit.can_make_request():
                time_until_reset = rate_limit.time_until_reset()
                return False, f'Rate limit exceeded for {window_type} window. Resets in {time_until_reset:.1f}s'
        
        return True, None
    
    def record_request(self):
        """
        Record that a request was made, incrementing all rate limit counters.
        """
        checks = []
        
        if self.provider.rate_limit_per_second:
            checks.append(('second', self.provider.rate_limit_per_second))
        
        if self.provider.rate_limit_per_minute:
            checks.append(('minute', self.provider.rate_limit_per_minute))
        
        if self.provider.rate_limit_per_day:
            checks.append(('day', self.provider.rate_limit_per_day))
        
        for window_type, limit in checks:
            rate_limit = RateLimit.get_or_create_window(
                self.provider_id,
                window_type,
                int(limit)
            )
            rate_limit.increment()
        
        db.session.commit()
    
    def wait_if_needed(self, max_wait_seconds: float = 60.0) -> bool:
        """
        Wait if rate limit is exceeded (up to max_wait_seconds).
        
        Returns:
            True if we can proceed (either immediately or after waiting)
            False if we'd need to wait longer than max_wait_seconds
        """
        can_proceed, reason = self.can_make_request()
        
        if can_proceed:
            return True
        
        # Extract wait time from reason
        # Reason format: "Rate limit exceeded for X window. Resets in Y.Zs"
        try:
            wait_time = float(reason.split('Resets in ')[1].rstrip('s'))
        except (IndexError, ValueError):
            wait_time = 1.0  # Default fallback
        
        if wait_time > max_wait_seconds:
            return False
        
        # Wait and try again
        time.sleep(wait_time + 0.1)  # Add small buffer
        return self.can_make_request()[0]
    
    def get_status(self) -> dict:
        """Get current rate limit status for all windows."""
        status = {
            'provider': self.provider.name,
            'limits': [],
        }
        
        checks = []
        if self.provider.rate_limit_per_second:
            checks.append(('second', self.provider.rate_limit_per_second))
        if self.provider.rate_limit_per_minute:
            checks.append(('minute', self.provider.rate_limit_per_minute))
        if self.provider.rate_limit_per_day:
            checks.append(('day', self.provider.rate_limit_per_day))
        
        for window_type, limit in checks:
            rate_limit = RateLimit.get_or_create_window(
                self.provider_id,
                window_type,
                int(limit)
            )
            
            status['limits'].append({
                'window': window_type,
                'limit': rate_limit.requests_allowed,
                'used': rate_limit.requests_made,
                'remaining': rate_limit.remaining_requests(),
                'resets_in': rate_limit.time_until_reset(),
                'is_exhausted': rate_limit.is_exhausted,
            })
        
        return status
    
    def reset_all(self):
        """Reset all rate limit counters for this provider (admin function)."""
        RateLimit.query.filter_by(provider_id=self.provider_id).delete()
        db.session.commit()


class RateLimitMiddleware:
    """
    Middleware wrapper for provider search methods to enforce rate limiting.
    """
    
    @staticmethod
    def wrap(provider_instance, search_method):
        """
        Wrap a provider's search method with rate limiting.
        
        Usage:
            provider = ShodanProvider(app)
            rate_limited_search = RateLimitMiddleware.wrap(provider, provider.search)
            results = rate_limited_search(query, owner, language, patterns, max_results)
        """
        def rate_limited_search(*args, **kwargs):
            # Get provider from database
            db_provider = Provider.query.filter_by(name=provider_instance.name).first()
            
            if not db_provider:
                # Provider not in database, allow request
                return search_method(*args, **kwargs)
            
            # Check rate limits
            limiter = RateLimiter(db_provider)
            can_proceed, reason = limiter.can_make_request()
            
            if not can_proceed:
                # Rate limit exceeded, return error result
                return [{
                    'provider': provider_instance.name,
                    'source': 'N/A',
                    'artifact': None,
                    'preview': f'Rate limit exceeded: {reason}',
                    'addresses': [],
                    'links': [],
                    'error': True,
                }]
            
            # Record the request
            limiter.record_request()
            
            # Execute the actual search
            return search_method(*args, **kwargs)
        
        return rate_limited_search


def get_rate_limit_status_all() -> list:
    """Get rate limit status for all providers."""
    providers = Provider.query.all()
    status_list = []
    
    for provider in providers:
        if not provider.enabled:
            continue
        
        limiter = RateLimiter(provider)
        status_list.append(limiter.get_status())
    
    return status_list
