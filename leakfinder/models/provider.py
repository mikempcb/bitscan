"""
Provider models for managing search provider configurations.
"""
from datetime import datetime
from . import db


class Provider(db.Model):
    """Provider configuration model."""
    
    __tablename__ = 'providers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    
    # Rate limiting configuration
    rate_limit_per_second = db.Column(db.Float, nullable=True)
    rate_limit_per_minute = db.Column(db.Integer, nullable=True)
    rate_limit_per_day = db.Column(db.Integer, nullable=True)
    
    # Request configuration
    timeout_seconds = db.Column(db.Integer, default=30, nullable=False)
    
    # Provider status
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    last_used = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    settings = db.relationship('ProviderSettings', backref='provider', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Provider {self.name}: {self.display_name}>'
    
    def to_dict(self):
        """Convert provider to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'rate_limit_per_second': self.rate_limit_per_second,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'rate_limit_per_day': self.rate_limit_per_day,
            'timeout_seconds': self.timeout_seconds,
            'enabled': self.enabled,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ProviderSettings(db.Model):
    """Provider-specific settings and configurations."""
    
    __tablename__ = 'provider_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False, index=True)
    
    # Pattern configuration
    enabled_patterns = db.Column(db.JSON, nullable=False, default=list)
    
    # Content processing settings
    context_window_chars = db.Column(db.Integer, default=120, nullable=False)
    max_content_size_kb = db.Column(db.Integer, default=1024, nullable=False)
    fetch_full_content = db.Column(db.Boolean, default=True, nullable=False)
    
    # Address derivation settings
    auto_derive_addresses = db.Column(db.Boolean, default=True, nullable=False)
    max_addresses_per_key = db.Column(db.Integer, default=10, nullable=False)
    
    # Search strategy settings
    preferred_strategies = db.Column(db.JSON, nullable=True)
    max_results_per_query = db.Column(db.Integer, default=100, nullable=False)
    
    # Advanced settings
    custom_headers = db.Column(db.JSON, nullable=True)
    custom_params = db.Column(db.JSON, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<ProviderSettings for provider_id={self.provider_id}>'
    
    def to_dict(self):
        """Convert provider settings to dictionary."""
        return {
            'id': self.id,
            'provider_id': self.provider_id,
            'enabled_patterns': self.enabled_patterns,
            'context_window_chars': self.context_window_chars,
            'max_content_size_kb': self.max_content_size_kb,
            'fetch_full_content': self.fetch_full_content,
            'auto_derive_addresses': self.auto_derive_addresses,
            'max_addresses_per_key': self.max_addresses_per_key,
            'preferred_strategies': self.preferred_strategies,
            'max_results_per_query': self.max_results_per_query,
            'custom_headers': self.custom_headers,
            'custom_params': self.custom_params,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
