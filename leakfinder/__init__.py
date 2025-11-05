import os
from flask import Flask


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", os.urandom(24)),
        
        # Database
        DATABASE_PATH=os.environ.get("DATABASE_PATH", os.path.join(app.instance_path, "leakfinder.db")),
        SQL_ECHO=os.environ.get("SQL_ECHO", "0") == "1",
        
        # API Keys
        GITHUB_TOKEN=os.environ.get("GITHUB_TOKEN"),
        GITLAB_TOKEN=os.environ.get("GITLAB_TOKEN"),
        SHODAN_API_KEY=os.environ.get("SHODAN_API_KEY"),
        BITBUCKET_USERNAME=os.environ.get("BITBUCKET_USERNAME"),
        BITBUCKET_APP_PASSWORD=os.environ.get("BITBUCKET_APP_PASSWORD"),
        SOURCEGRAPH_TOKEN=os.environ.get("SOURCEGRAPH_TOKEN"),
        GOOGLE_CSE_API_KEY=os.environ.get("GOOGLE_CSE_API_KEY"),
        GOOGLE_CSE_ID=os.environ.get("GOOGLE_CSE_ID"),
        HIBP_API_KEY=os.environ.get("HIBP_API_KEY"),
        
        # App Settings
        RESULTS_REDACT=True,
        MAX_RESULTS_PER_PROVIDER=int(os.environ.get("MAX_RESULTS_PER_PROVIDER", "25")),
        USER_AGENT=os.environ.get("USER_AGENT", "LeakFinder/1.0 (+https://example.com)"),
        REQUEST_TIMEOUT=float(os.environ.get("REQUEST_TIMEOUT", "15")),
    )

    # Initialize database
    from .database import init_db
    init_db(app)

    # Blueprints
    from .views import bp as views_bp
    app.register_blueprint(views_bp)

    return app
