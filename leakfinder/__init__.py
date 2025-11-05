import os
from flask import Flask


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", os.urandom(24)),
        GITHUB_TOKEN=os.environ.get("GITHUB_TOKEN"),
        GITLAB_TOKEN=os.environ.get("GITLAB_TOKEN"),
        SHODAN_API_KEY=os.environ.get("SHODAN_API_KEY"),
        RESULTS_REDACT=True,
        MAX_RESULTS_PER_PROVIDER=int(os.environ.get("MAX_RESULTS_PER_PROVIDER", "25")),
        USER_AGENT=os.environ.get("USER_AGENT", "LeakFinder/1.0 (+https://example.com)"),
        REQUEST_TIMEOUT=float(os.environ.get("REQUEST_TIMEOUT", "15")),
    )

    # Blueprints
    from .views import bp as views_bp
    app.register_blueprint(views_bp)

    return app

