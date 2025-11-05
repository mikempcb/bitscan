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
from .utils.scan_depth import ScanDepthManager
from .services.cache_service import CacheService

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
        # Get scan depth options for the form
        scan_depths = ScanDepthManager.get_available_depths()
        return render_template('scan.html', scan_depths=scan_depths)

    # POST: run scan
    kinds = request.form.getlist('kinds')
    search_query = request.form.get('query', '').strip()
    owner_filter = request.form.get('owner', '').strip()
    language_filter = request.form.get('language', '').strip()
    max_results = int(request.form.get('max_results') or 50)  # Increased default
    scan_depth = request.form.get('scan_depth', 'medium').strip()

    selected_providers = request.form.getlist('providers')

    results = []
    patterns = LeakPatterns.build(kinds)
    cache_service = CacheService()
    
    # Track cache statistics
    cache_hits = 0
    total_searches = 0

    for prov in _providers(current_app):
        if prov.name not in selected_providers:
            continue
        
        total_searches += 1
        
        try:
            # Use cache service for search
            prov_results, cache_hit = cache_service.search_with_cache(
                provider_search_func=prov.search,
                provider=prov.name,
                query=search_query,
                owner_filter=owner_filter,
                language_filter=language_filter,
                pattern_kinds=kinds,
                scan_depth=scan_depth,
                patterns=patterns,
                max_results=max_results
            )
            
            if cache_hit:
                cache_hits += 1
            
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
                'cached': False,
                'cache_hit': False,
            })

    # Sort by provider then source
    results.sort(key=lambda x: (x['provider'], x.get('source') or ''))
    
    # Add scan metadata
    scan_metadata = {
        'total_results': len(results),
        'cache_hits': cache_hits,
        'total_searches': total_searches,
        'cache_hit_rate': round((cache_hits / max(1, total_searches)) * 100, 1),
        'scan_depth': scan_depth,
        'scan_depth_info': ScanDepthManager.get_depth_info(scan_depth),
    }
    
    return render_template('results.html', results=results, scan_metadata=scan_metadata)


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
