"""
Database initialization and configuration.
"""
from flask import Flask
from .models import db


def init_db(app: Flask):
    """Initialize database with Flask app."""
    # Database configuration
    db_path = app.config.get('DATABASE_PATH', 'instance/leakfinder.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = app.config.get('SQL_ECHO', False)
    
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

