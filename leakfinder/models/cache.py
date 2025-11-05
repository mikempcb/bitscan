"""
Cache models for storing search results.
"""
from datetime import datetime, timedelta
import hashlib
import json
import zlib
from . import db


class SearchCache(db.Model):
    """Cache for search query results."""
    
    __tablename__ = 'search_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    query_hash = db.Column(db.String(64), nullable=False, index=True)
    
    # Query parameters for cache key generation
    provider = db.Column(db.String(50), nullable=False)
    query = db.Column(db.Text, nullable=False)
    owner_filter = db.Column(db.String(255), nullable=True)
    language_filter = db.Column(db.String(50), nullable=True)
    pattern_kinds = db.Column(db.JSON, nullable=False)
    scan_depth = db.Column(db.String(20), default='medium', nullable=False)
    
    # Cached results (compressed JSON)
    results_data = db.Column(db.LargeBinary, nullable=False)
    results_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Cache metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    hit_count = db.Column(db.Integer, default=0, nullable=False)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<SearchCache {self.cache_key}: {self.provider} - {self.results_count} results>'
    
    @classmethod
    def generate_cache_key(cls, provider: str, query: str, owner_filter: str = None, 
                          language_filter: str = None, pattern_kinds: list = None, 
                          scan_depth: str = 'medium') -> str:
        """Generate a unique cache key for search parameters."""
        # Create a consistent string representation of parameters
        params = {
            'provider': provider,
            'query': query or '',
            'owner_filter': owner_filter or '',
            'language_filter': language_filter or '',
            'pattern_kinds': sorted(pattern_kinds or []),
            'scan_depth': scan_depth,
        }
        
        # Create JSON string and hash it
        params_json = json.dumps(params, sort_keys=True)
        cache_key = hashlib.sha256(params_json.encode()).hexdigest()
        
        return cache_key
    
    @classmethod
    def get_cached_results(cls, provider: str, query: str, owner_filter: str = None,
                          language_filter: str = None, pattern_kinds: list = None,
                          scan_depth: str = 'medium') -> tuple:
        """
        Get cached results for search parameters.
        
        Returns:
            tuple: (results_list, cache_hit) where cache_hit is boolean
        """
        cache_key = cls.generate_cache_key(provider, query, owner_filter, 
                                         language_filter, pattern_kinds, scan_depth)
        
        # Look for valid cache entry
        cache_entry = cls.query.filter_by(cache_key=cache_key).first()
        
        if cache_entry is None:
            return None, False
        
        # Check if cache is expired
        if datetime.utcnow() > cache_entry.expires_at:
            # Delete expired entry
            db.session.delete(cache_entry)
            db.session.commit()
            return None, False
        
        # Update access statistics
        cache_entry.hit_count += 1
        cache_entry.last_accessed = datetime.utcnow()
        db.session.commit()
        
        # Decompress and return results
        try:
            compressed_data = cache_entry.results_data
            decompressed_data = zlib.decompress(compressed_data)
            results = json.loads(decompressed_data.decode('utf-8'))
            return results, True
        except Exception as e:
            # If decompression fails, delete corrupted entry
            db.session.delete(cache_entry)
            db.session.commit()
            return None, False
    
    @classmethod
    def cache_results(cls, provider: str, query: str, results: list, 
                     owner_filter: str = None, language_filter: str = None,
                     pattern_kinds: list = None, scan_depth: str = 'medium',
                     cache_duration_hours: int = 24) -> bool:
        """
        Cache search results.
        
        Args:
            provider: Provider name
            query: Search query
            results: List of search results
            owner_filter: Owner filter
            language_filter: Language filter
            pattern_kinds: List of pattern kinds
            scan_depth: Scan depth level
            cache_duration_hours: How long to cache (default 24 hours)
            
        Returns:
            bool: True if cached successfully
        """
        try:
            cache_key = cls.generate_cache_key(provider, query, owner_filter,
                                             language_filter, pattern_kinds, scan_depth)
            
            # Check if entry already exists
            existing_entry = cls.query.filter_by(cache_key=cache_key).first()
            if existing_entry:
                # Update existing entry
                cache_entry = existing_entry
            else:
                # Create new entry
                cache_entry = cls(cache_key=cache_key)
                db.session.add(cache_entry)
            
            # Set cache parameters
            cache_entry.provider = provider
            cache_entry.query = query or ''
            cache_entry.owner_filter = owner_filter
            cache_entry.language_filter = language_filter
            cache_entry.pattern_kinds = pattern_kinds or []
            cache_entry.scan_depth = scan_depth
            cache_entry.results_count = len(results)
            
            # Compress and store results
            results_json = json.dumps(results)
            compressed_data = zlib.compress(results_json.encode('utf-8'))
            cache_entry.results_data = compressed_data
            
            # Set expiration
            cache_entry.expires_at = datetime.utcnow() + timedelta(hours=cache_duration_hours)
            cache_entry.created_at = datetime.utcnow()
            
            # Generate query hash for analytics
            query_params = f"{provider}:{query}:{owner_filter}:{language_filter}"
            cache_entry.query_hash = hashlib.md5(query_params.encode()).hexdigest()
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            return False
    
    @classmethod
    def cleanup_expired_cache(cls) -> int:
        """Remove expired cache entries. Returns number of entries removed."""
        expired_entries = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        count = len(expired_entries)
        
        for entry in expired_entries:
            db.session.delete(entry)
        
        db.session.commit()
        return count
    
    @classmethod
    def get_cache_stats(cls) -> dict:
        """Get cache statistics."""
        total_entries = cls.query.count()
        expired_entries = cls.query.filter(cls.expires_at < datetime.utcnow()).count()
        total_hits = db.session.query(db.func.sum(cls.hit_count)).scalar() or 0
        
        # Calculate cache size (approximate)
        total_size = db.session.query(db.func.sum(db.func.length(cls.results_data))).scalar() or 0
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'total_hits': total_hits,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
        }
    
    def to_dict(self):
        """Convert cache entry to dictionary."""
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'provider': self.provider,
            'query': self.query,
            'owner_filter': self.owner_filter,
            'language_filter': self.language_filter,
            'pattern_kinds': self.pattern_kinds,
            'scan_depth': self.scan_depth,
            'results_count': self.results_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'hit_count': self.hit_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
        }
