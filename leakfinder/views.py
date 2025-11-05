from flask import Blueprint, render_template, request, current_app
from .providers.github import GitHubProvider
from .providers.gitlab import GitLabProvider
from .providers.shodanp import ShodanProvider
from .providers.bitbucket import BitbucketProvider
from .providers.sourcegraph import SourcegraphProvider
from .providers.google_cse import GoogleCSEProvider
from .providers.pastebin import PastebinProvider
from .providers.wayback import WaybackProvider
from .providers.hibp_pastes import HIBPPastesProvider
from .utils.patterns import LeakPatterns
from .utils.crypto import AddressUtils

bp = Blueprint('views', __name__)


def _providers(app):
    return [
        GitHubProvider(app),
        GitLabProvider(app),
        ShodanProvider(app),
        BitbucketProvider(app),
        SourcegraphProvider(app),
        GoogleCSEProvider(app),
        PastebinProvider(app),
        WaybackProvider(app),
        HIBPPastesProvider(app),
    ]


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/scan', methods=['GET', 'POST'])
def scan():
    if request.method == 'GET':
        return render_template('scan.html')

    # POST: run scan
    kinds = request.form.getlist('kinds')
    search_query = request.form.get('query', '').strip()
    owner_filter = request.form.get('owner', '').strip()
    language_filter = request.form.get('language', '').strip()
    max_results = int(request.form.get('max_results') or 20)

    selected_providers = request.form.getlist('providers')

    results = []
    patterns = LeakPatterns.build(kinds)

    for prov in _providers(current_app):
        if prov.name not in selected_providers:
            continue
        try:
            prov_results = prov.search(
                query=search_query,
                owner=owner_filter,
                language=language_filter,
                patterns=patterns,
                max_results=max_results,
            )
            for r in prov_results:
                # Compute address previews if applicable
                addresses = AddressUtils.derive_addresses_from_artifact(r.get('artifact'), r.get('chain_hint'))
                r['addresses'] = addresses
            results.extend(prov_results)
        except Exception as e:  # noqa: BLE001
            results.append({
                'provider': prov.name,
                'source': 'N/A',
                'artifact': None,
                'preview': f'Error: {type(e).__name__}: {e}',
                'addresses': [],
                'links': [],
            })

    # Sort by provider then source
    results.sort(key=lambda x: (x['provider'], x.get('source') or ''))
    return render_template('results.html', results=results)


@bp.app_template_filter('redact')
def redact_filter(value: str):
    if not value:
        return value
    # Redact long secrets but keep small context
    if len(value) > 12:
        return value[:6] + '...' + value[-4:]
    return value


@bp.app_context_processor
def inject_helpers():
    return {
        'explorer_links': AddressUtils.explorer_links,
    }
