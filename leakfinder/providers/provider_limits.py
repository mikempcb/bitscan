"""
Provider API limits and maximum result configurations.
"""

# Maximum results per query for each provider
PROVIDER_MAX_RESULTS = {
    'github': 1000,  # GitHub Code Search API limit
    'gitlab': 100,   # GitLab API default max per_page
    'shodan': 100,   # Shodan free tier limit per query
    'bitbucket': 50, # Bitbucket API limit
    'sourcegraph': 500, # Sourcegraph public instance limit
    'google_cse': 100,  # Google Custom Search daily limit (but 10 per query)
    'pastebin': 50,  # Pastebin scraping reasonable limit
    'wayback': 100,  # Internet Archive reasonable limit
    'hibp_pastes': 100, # HIBP API limit
}

# Rate limits per hour for each provider
PROVIDER_RATE_LIMITS = {
    'github': 5000,  # With token, 60 without
    'gitlab': 2000,  # Authenticated requests
    'shodan': 100,   # Free tier monthly limit
    'bitbucket': 1000, # With app password
    'sourcegraph': 500, # Public instance
    'google_cse': 100,  # Daily limit
    'pastebin': 100,    # Estimated scraping limit
    'wayback': 1000,    # Estimated limit
    'hibp_pastes': 100, # Paid service limit
}

# Providers that support regex in queries
REGEX_CAPABLE_PROVIDERS = {
    'github',      # Via gh-search CLI
    'sourcegraph', # Native regex support
    'wayback',     # Limited regex support
}

# Providers that support advanced search operators
ADVANCED_SEARCH_PROVIDERS = {
    'github': ['filename:', 'extension:', 'path:', 'language:', 'size:', 'user:', 'org:', 'repo:'],
    'gitlab': ['filename:', 'extension:', 'path:', 'language:'],
    'google_cse': ['site:', 'filetype:', 'inurl:', 'intitle:', 'intext:', '-site:'],
    'shodan': ['port:', 'product:', 'org:', 'asn:', 'country:', 'city:', 'has_screenshot:', 'ssl.cert.subject.CN:'],
    'sourcegraph': ['file:', 'lang:', 'repo:', 'type:'],
}

def get_max_results(provider_name: str) -> int:
    """Get maximum results for a provider."""
    return PROVIDER_MAX_RESULTS.get(provider_name, 50)

def get_rate_limit(provider_name: str) -> int:
    """Get rate limit for a provider."""
    return PROVIDER_RATE_LIMITS.get(provider_name, 100)

def supports_regex(provider_name: str) -> bool:
    """Check if provider supports regex queries."""
    return provider_name in REGEX_CAPABLE_PROVIDERS

def get_search_operators(provider_name: str) -> list:
    """Get supported search operators for a provider."""
    return ADVANCED_SEARCH_PROVIDERS.get(provider_name, [])
