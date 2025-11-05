"""
SQLAlchemy database models for BitScan (LeakFinder).
"""
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Import all models
from .search import Search
from .provider import Provider, ProviderSettings
from .cache import SearchCache

# TODO: Create these models when needed
# from .result import Result
# from .key import ExtractedKey
# from .address import WalletAddress
# from .content import ContentSnapshot, MatchContext
# from .rate_limit import RateLimit

__all__ = [
    'db',
    'Search',
    'Provider',
    'ProviderSettings',
    'SearchCache',
    # TODO: Add these when models are created
    # 'Result',
    # 'ExtractedKey',
    # 'WalletAddress',
    # 'ContentSnapshot',
    # 'MatchContext',
    # 'RateLimit',
]
