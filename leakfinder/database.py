"""
Database initialization and configuration.
"""
import os
from flask import Flask
from .models import db


def init_db(app: Flask):
    """Initialize database with Flask app."""
    # Database configuration - use absolute path for Windows compatibility
    default_db_path = os.path.join(app.instance_path, 'leakfinder.db')
    db_path = app.config.get('DATABASE_PATH', default_db_path)
    
    # Convert to absolute path if it's relative
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)
    
    # Ensure the directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # Use proper URI format for Windows (forward slashes work on Windows too)
    db_path_uri = db_path.replace('\\', '/')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path_uri}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = app.config.get('SQL_ECHO', False)
    
    # Debug logging for troubleshooting
    print(f"Database path: {db_path}")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Database directory exists: {os.path.exists(db_dir)}")
    print(f"Database file exists: {os.path.exists(db_path)}")
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Initialize default providers
        _init_default_providers()


def _init_default_providers():
    """Create default provider configurations if they don't exist."""
    from .models import Provider, ProviderSettings
    
    default_providers = [
        {
            'name': 'shodan',
            'display_name': 'Shodan',
            'rate_limit_per_second': 1.0,  # Free tier: 1 req/sec
            'rate_limit_per_day': 100,     # Free tier: 100 queries/month (approximated)
            'timeout_seconds': 30,
        },
        {
            'name': 'github',
            'display_name': 'GitHub',
            'rate_limit_per_minute': 30,   # Authenticated: 30 req/min
            'timeout_seconds': 15,
        },
        {
            'name': 'gitlab',
            'display_name': 'GitLab',
            'rate_limit_per_minute': 30,
            'timeout_seconds': 15,
        },
        {
            'name': 'google_cse',
            'display_name': 'Google Custom Search',
            'rate_limit_per_day': 100,     # Free tier: 100 queries/day
            'timeout_seconds': 15,
        },
        {
            'name': 'bitbucket',
            'display_name': 'Bitbucket',
            'rate_limit_per_minute': 60,
            'timeout_seconds': 15,
        },
        {
            'name': 'sourcegraph',
            'display_name': 'Sourcegraph',
            'rate_limit_per_minute': 20,
            'timeout_seconds': 15,
        },
        {
            'name': 'pastebin',
            'display_name': 'Pastebin',
            'rate_limit_per_minute': 10,
            'timeout_seconds': 15,
        },
        {
            'name': 'wayback',
            'display_name': 'Wayback Machine',
            'rate_limit_per_second': 1.0,
            'timeout_seconds': 30,
        },
        {
            'name': 'hibp_pastes',
            'display_name': 'Have I Been Pwned (Pastes)',
            'rate_limit_per_minute': 10,
            'timeout_seconds': 15,
        },
    ]
    
    for prov_data in default_providers:
        existing = Provider.query.filter_by(name=prov_data['name']).first()
        
        if not existing:
            provider = Provider(**prov_data)
            db.session.add(provider)
            db.session.flush()  # Get the ID
            
            # Create default settings
            settings = ProviderSettings(
                provider_id=provider.id,
                enabled_patterns=['eth_priv', 'btc_wif', 'xprv', 'mnemonic', 'keystore'],
                context_window_chars=120,
                max_content_size_kb=1024,
                fetch_full_content=True,
                auto_derive_addresses=True,
                max_addresses_per_key=10,
            )
            db.session.add(settings)
    
    db.session.commit()
