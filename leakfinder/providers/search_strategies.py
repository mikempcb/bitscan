"""
Advanced search strategies and DORK operators for each provider.
"""
from typing import List, Dict, Any
from ..utils.strategy_scorer import StrategyScorer


class ShodanStrategies:
    """
    Creative Shodan search strategies for finding cryptocurrency leaks.
    Shodan indexes banners from services, FTP listings, HTTP responses, etc.
    """
    
    # FTP servers with directory listings
    FTP_LEAKS = [
        'port:21 "wallet"',
        'port:21 "keystore"',
        'port:21 "230 Login successful" wallet.dat',
        'port:21 ".dat" directory',
        'port:21 "private" "key"',
    ]
    
    # HTTP directory listings (misconfigured web servers)
    DIRECTORY_LISTINGS = [
        'http.title:"Index of" wallet',
        'http.title:"Directory Listing" keystore',
        'http.html:"Parent Directory" wallet.dat',
        'http.html:"<title>Index of" private',
        '"Index of /backup" wallet',
        '"Index of" "wallet.json"',
    ]
    
    # Docker registries (exposed private registries)
    DOCKER_REGISTRIES = [
        'http.component:"Docker Registry"',
        'port:5000 "Docker-Distribution-Api-Version"',
        'docker registry wallet',
        '"Docker-Distribution-Api-Version: registry" crypto',
    ]
    
    # Git repositories exposed via HTTP
    GIT_EXPOSURE = [
        'http.html:".git/config"',
        'http.title:"Index of /.git"',
        '".git" wallet',
        'http.html:"[core]" bare',
    ]
    
    # Elasticsearch instances (no auth)
    ELASTICSEARCH = [
        'port:9200 "You Know, for Search"',
        'port:9200 wallet',
        'port:9200 keystore',
        'product:"Elastic" wallet',
    ]
    
    # MongoDB databases
    MONGODB = [
        'product:"MongoDB" port:27017',
        '"MongoDB server information" wallet',
        'port:27017 "authentication"',
    ]
    
    # Redis instances
    REDIS = [
        'product:"Redis" port:6379',
        'port:6379 -authentication wallet',
    ]
    
    # S3 buckets (via SSL certs)
    S3_BUCKETS = [
        'ssl.cert.subject.CN:*.s3.amazonaws.com',
        'org:"Amazon" has_screenshot:true wallet',
        'asn:AS16509 backup',  # Amazon ASN
    ]
    
    # Backup files exposed
    BACKUP_FILES = [
        'http.html:".sql" "backup"',
        'http.html:".dump" wallet',
        'http.title:"backup"',
        '"backup.zip" OR "backup.tar"',
    ]
    
    # Database dumps
    DATABASE_DUMPS = [
        'http.html:"CREATE TABLE" wallet',
        'http.html:"INSERT INTO" private',
        '".sql" wallet',
    ]
    
    # Config files exposed
    CONFIG_FILES = [
        'http.html:".env" OR http.html:"config.php"',
        'http.html:"PRIVATE_KEY"',
        'http.title:"phpinfo()"',
    ]
    
    # Jupyter notebooks (sometimes contain keys)
    JUPYTER = [
        'http.title:"Jupyter Notebook" port:8888',
        '"Jupyter" wallet OR "Jupyter" private',
    ]
    
    # Jenkins exposed
    JENKINS = [
        'http.title:"Dashboard [Jenkins]"',
        'product:"Jenkins" wallet',
    ]
    
    # Comprehensive wallet search
    WALLET_SEARCH = [
        'wallet.dat',
        '"wallet.json" OR "keystore"',
        '"private key" OR "mnemonic"',
        '"xprv" OR "xpub"',
        '"BEGIN PRIVATE KEY"',
    ]
    
    @classmethod
    def build_query(cls, strategy_name: str, custom_term: str = None) -> str:
        """
        Build a Shodan query for the specified strategy.
        
        Args:
            strategy_name: Name of the strategy (e.g., 'ftp_leaks', 'directory_listings')
            custom_term: Optional additional search term
            
        Returns:
            Shodan query string
        """
        strategy_map = {
            'ftp_leaks': cls.FTP_LEAKS,
            'directory_listings': cls.DIRECTORY_LISTINGS,
            'docker_registries': cls.DOCKER_REGISTRIES,
            'git_exposure': cls.GIT_EXPOSURE,
            'elasticsearch': cls.ELASTICSEARCH,
            'mongodb': cls.MONGODB,
            'redis': cls.REDIS,
            's3_buckets': cls.S3_BUCKETS,
            'backup_files': cls.BACKUP_FILES,
            'database_dumps': cls.DATABASE_DUMPS,
            'config_files': cls.CONFIG_FILES,
            'jupyter': cls.JUPYTER,
            'jenkins': cls.JENKINS,
            'wallet_search': cls.WALLET_SEARCH,
        }
        
        queries = strategy_map.get(strategy_name, cls.WALLET_SEARCH)
        
        # For now, return the first query in the list
        # In a more advanced implementation, could rotate through them
        base_query = queries[0] if queries else ''
        
        if custom_term:
            return f'{base_query} {custom_term}'
        
        return base_query
    
    @classmethod
    def get_all_strategies(cls) -> List[Dict[str, Any]]:
        """Get all available Shodan search strategies ordered by likelihood."""
        strategies = [
            {'name': 'wallet_search', 'display': 'General Wallet Search', 'queries': cls.WALLET_SEARCH},
            {'name': 'ftp_leaks', 'display': 'FTP Server Leaks', 'queries': cls.FTP_LEAKS},
            {'name': 'directory_listings', 'display': 'HTTP Directory Listings', 'queries': cls.DIRECTORY_LISTINGS},
            {'name': 'backup_files', 'display': 'Backup Files', 'queries': cls.BACKUP_FILES},
            {'name': 'database_dumps', 'display': 'Database Dumps', 'queries': cls.DATABASE_DUMPS},
            {'name': 'config_files', 'display': 'Config Files', 'queries': cls.CONFIG_FILES},
            {'name': 'git_exposure', 'display': 'Exposed Git Repositories', 'queries': cls.GIT_EXPOSURE},
            {'name': 'elasticsearch', 'display': 'Elasticsearch Instances', 'queries': cls.ELASTICSEARCH},
            {'name': 'mongodb', 'display': 'MongoDB Databases', 'queries': cls.MONGODB},
            {'name': 'redis', 'display': 'Redis Instances', 'queries': cls.REDIS},
            {'name': 'docker_registries', 'display': 'Exposed Docker Registries', 'queries': cls.DOCKER_REGISTRIES},
            {'name': 'jupyter', 'display': 'Jupyter Notebooks', 'queries': cls.JUPYTER},
            {'name': 'jenkins', 'display': 'Jenkins Servers', 'queries': cls.JENKINS},
            {'name': 's3_buckets', 'display': 'S3 Buckets', 'queries': cls.S3_BUCKETS},
        ]
        
        # Add likelihood scores to each strategy
        for strategy in strategies:
            score = StrategyScorer.score_strategy('shodan', strategy['name'])
            strategy['likelihood_score'] = score
            strategy['likelihood'] = StrategyScorer.get_strategy_metadata('shodan', strategy['name'])['likelihood']
        
        # Sort by likelihood score (highest first)
        strategies.sort(key=lambda x: x['likelihood_score'], reverse=True)
        return strategies


class GitHubStrategies:
    """GitHub code search qualifiers and strategies."""
    
    @staticmethod
    def build_query(base_term: str = None, **qualifiers) -> str:
        """
        Build a GitHub code search query with qualifiers.
        
        Args:
            base_term: Main search term
            qualifiers: GitHub search qualifiers (filename, extension, path, language, size, etc.)
            
        Returns:
            GitHub search query string
            
        Examples:
            >>> build_query('wallet.dat', filename='wallet.dat')
            'wallet.dat filename:wallet.dat'
            
            >>> build_query('PRIVATE_KEY', extension='env', language='Text')
            'PRIVATE_KEY extension:env language:Text'
        """
        query_parts = []
        
        if base_term:
            query_parts.append(base_term)
        
        # Add qualifiers
        for key, value in qualifiers.items():
            if value:
                query_parts.append(f'{key}:{value}')
        
        return ' '.join(query_parts)
    
    @staticmethod
    def wallet_file_queries() -> List[str]:
        """Queries for finding wallet files."""
        return [
            'filename:wallet.dat',
            'filename:wallet.json',
            'filename:keystore extension:json',
            'filename:UTC-- extension:json',
            '"wallet.dat" OR "keystore"',
        ]
    
    @staticmethod
    def private_key_queries() -> List[str]:
        """Queries for finding private keys in code."""
        return [
            'PRIVATE_KEY extension:env',
            '"private_key" extension:json',
            'privateKey language:JavaScript',
            '"BEGIN PRIVATE KEY" extension:pem',
            'xprv extension:txt',
        ]
    
    @staticmethod
    def config_file_queries() -> List[str]:
        """Queries for finding keys in config files."""
        return [
            'path:.env PRIVATE_KEY',
            'path:config private_key',
            'filename:.env.production',
            'extension:yaml secret',
        ]


class GoogleCSEStrategies:
    """Google Custom Search Engine operators."""
    
    @staticmethod
    def build_query(term: str, **operators) -> str:
        """
        Build a Google search query with operators.
        
        Args:
            term: Main search term
            operators: Google operators (site, filetype, inurl, intitle, intext)
            
        Returns:
            Google search query string
        """
        query_parts = [term]
        
        for key, value in operators.items():
            if value:
                if isinstance(value, list):
                    # Multiple values (e.g., multiple sites)
                    for v in value:
                        query_parts.append(f'{key}:{v}')
                else:
                    query_parts.append(f'{key}:{value}')
        
        return ' '.join(query_parts)
    
    @staticmethod
    def code_hosting_sites() -> List[str]:
        """Common code hosting sites to search."""
        return [
            'github.com',
            'gitlab.com',
            'bitbucket.org',
            'gist.github.com',
            'pastebin.com',
            'paste.ee',
            'hastebin.com',
            'ghostbin.com',
            'codeberg.org',
        ]
    
    @staticmethod
    def storage_sites() -> List[str]:
        """Cloud storage sites that might have leaks."""
        return [
            's3.amazonaws.com',
            'storage.googleapis.com',
            'blob.core.windows.net',
            'digitaloceanspaces.com',
        ]
    
    @staticmethod
    def wallet_queries() -> List[str]:
        """Google queries for finding wallets."""
        sites = ' OR '.join([f'site:{s}' for s in GoogleCSEStrategies.code_hosting_sites()])
        
        return [
            f'wallet.dat ({sites})',
            f'keystore filetype:json ({sites})',
            f'"private key" ({sites})',
            f'xprv ({sites})',
            f'"mnemonic phrase" ({sites})',
        ]
    
    @staticmethod
    def directory_listing_queries() -> List[str]:
        """Queries for finding directory listings with wallet files."""
        return [
            'intitle:"index of" wallet',
            'intitle:"directory listing" keystore',
            'inurl:backup wallet.dat',
            '"parent directory" "wallet.json"',
        ]


class PastebinStrategies:
    """Strategies for searching paste sites."""
    
    @staticmethod
    def common_searches() -> List[str]:
        """Common search terms for paste sites."""
        return [
            'wallet.dat',
            'private key',
            'mnemonic seed',
            'xprv',
            'keystore',
            'BEGIN PRIVATE KEY',
            'ethereum private key',
            'bitcoin wallet',
        ]


def get_provider_strategies(provider_name: str) -> Any:
    """Get the strategy class for a provider."""
    strategy_map = {
        'shodan': ShodanStrategies,
        'github': GitHubStrategies,
        'google_cse': GoogleCSEStrategies,
        'pastebin': PastebinStrategies,
    }
    
    return strategy_map.get(provider_name)
