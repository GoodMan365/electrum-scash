# -*- coding: utf-8 -*-
#
# Electrum-Scash - lightweight Scash client Forked From Electrum
# Copyright (C) 2018 The Electrum developers
# Copyright (C) 2025 The Electrum-Scash Developers
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys
import time
import threading
import json
from typing import Sequence, Tuple, Mapping, Type, List, Optional
import asyncio
import aiohttp



## from .lntransport import LNPeerAddr  # Lightning not supported for Scash
class LNPeerAddr:
    def __init__(self, *args, **kwargs):
        pass
    @classmethod
    def from_str(cls, s):
        raise NotImplementedError("Lightning not supported for Scash")
from .util import inv_dict, all_subclasses, classproperty
from . import bitcoin

class LNPeerAddr:
    """Dummy class for Scash (Lightning not supported)."""
    def __init__(self, host=None, port=None, pubkey=None):
        self.host = host
        self.port = port
        self.pubkey = pubkey
    
    @classmethod
    def from_str(cls, s):
        raise NotImplementedError("Lightning Network is not supported for Scash")
    
    def __str__(self):
        return "LNPeerAddr(lightning not supported)"


def read_json(filename, default=None):
    path = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(path, 'r') as f:
            r = json.loads(f.read())
    except Exception:
        if default is None:
            # Sometimes it's better to hard-fail: the file might be missing
            # due to a packaging issue, which might otherwise go unnoticed.
            raise
        r = default
    return r


def create_fallback_node_list(fallback_nodes_dict: dict[str, dict]) -> List[LNPeerAddr]:
    """Take a json dict of fallback nodes like: k:node_id, v:{k:'host', k:'port'} and return LNPeerAddr list"""
    fallback_nodes = []
    for node_id, address in fallback_nodes_dict.items():
        fallback_nodes.append(
            LNPeerAddr(host=address['host'], port=int(address['port']), pubkey=bytes.fromhex(node_id)))
    return fallback_nodes


GIT_REPO_URL = "https://github.com/GoodMan365/electrum-scash"
GIT_REPO_ISSUES_URL = "https://github.com/GoodMan365/electrum-scash/issues"
BIP39_WALLET_FORMATS = read_json('bip39_wallet_formats.json')


class AbstractNet:

    NET_NAME: str
    TESTNET: bool
    WIF_PREFIX: int
    ADDRTYPE_P2PKH: int
    ADDRTYPE_P2SH: int
    SEGWIT_HRP: str
    BOLT11_HRP: str
    GENESIS: str
    BLOCK_HEIGHT_FIRST_LIGHTNING_CHANNELS: int = 0
    BIP44_COIN_TYPE: int
    LN_REALM_BYTE: int
    DEFAULT_PORTS: Mapping[str, str]
    LN_DNS_SEEDS: Sequence[str]
    XPRV_HEADERS: Mapping[str, int]
    XPRV_HEADERS_INV: Mapping[int, str]
    XPUB_HEADERS: Mapping[str, int]
    XPUB_HEADERS_INV: Mapping[int, str]

    @classmethod
    def max_checkpoint(cls) -> int:
        return (len(cls.CHECKPOINTS) - 1) * 2016
        #return max(0, len(cls.CHECKPOINTS) * 2016 - 1)

    @classmethod
    def rev_genesis_bytes(cls) -> bytes:
        return bytes.fromhex(cls.GENESIS)[::-1]

    @classmethod
    def set_as_network(cls) -> None:
        global net
        net = cls

    _cached_default_servers = None
    @classproperty
    def DEFAULT_SERVERS(cls) -> Mapping[str, Mapping[str, str]]:
        if cls._cached_default_servers is None:
            default_file = {} if cls.TESTNET else None  # for mainnet we hard-fail if the file is missing.
            cls._cached_default_servers = read_json(os.path.join('chains', cls.NET_NAME, 'servers.json'), default_file)
        return cls._cached_default_servers

    _cached_fallback_lnnodes = None
    @classproperty
    def FALLBACK_LN_NODES(cls) -> Sequence[LNPeerAddr]:
        if cls._cached_fallback_lnnodes is None:
            default_file = {} if cls.TESTNET else None  # for mainnet we hard-fail if the file is missing.
            d = read_json(os.path.join('chains', cls.NET_NAME, 'fallback_lnnodes.json'), default_file)
            cls._cached_fallback_lnnodes = create_fallback_node_list(d)
        return cls._cached_fallback_lnnodes

    _cached_checkpoints = None
    @classproperty
    def CHECKPOINTS(cls) -> Sequence[Tuple[str, int]]:
        if cls._cached_checkpoints is None:
            default_file = [] if cls.TESTNET else None  # for mainnet we hard-fail if the file is missing.
            cls._cached_checkpoints = read_json(os.path.join('chains', cls.NET_NAME, 'checkpoints.json'), default_file)
        return cls._cached_checkpoints

    @classmethod
    def datadir_subdir(cls) -> Optional[str]:
        """The name of the folder in the filesystem.
        None means top-level, used by mainnet.
        """
        return cls.NET_NAME

    @classmethod
    def cli_flag(cls) -> str:
        """as used in e.g. `$ run_electrum --testnet4`"""
        return cls.NET_NAME

    @classmethod
    def config_key(cls) -> str:
        """as used for SimpleConfig.get()"""
        return cls.NET_NAME


class ScashMainnet(AbstractNet):

    NET_NAME = "scash"
    TESTNET = False
    WIF_PREFIX = 0x80
    ADDRTYPE_P2PKH = 0
    ADDRTYPE_P2SH = 5
    SEGWIT_HRP = "scash"
    BOLT11_HRP = SEGWIT_HRP
    GENESIS = "e3bf1597a568216022dbda6a0945f09b005d19f041e7158c3cbca9d4029ee82d"
    GENESIS_RANDOMX_HASH = "018d93624bd03d15f6dc3d4b54a1442318f94c46018b94a8e3262815e050c433"
    DEFAULT_PORTS = {'t': '50001', 's': '50002'}
    BLOCK_HEIGHT_FIRST_LIGHTNING_CHANNELS = 0  # Scash may not have Lightning

    XPRV_HEADERS = {
        'standard':    0x0488ade4,  # xprv
        'p2wpkh-p2sh': 0x049d7878,  # yprv
        'p2wsh-p2sh':  0x0295b005,  # Yprv
        'p2wpkh':      0x04b2430c,  # zprv
        'p2wsh':       0x02aa7a99,  # Zprv
    }
    XPRV_HEADERS_INV = inv_dict(XPRV_HEADERS)
    XPUB_HEADERS = {
        'standard':    0x0488b21e,  # xpub
        'p2wpkh-p2sh': 0x049d7cb2,  # ypub
        'p2wsh-p2sh':  0x0295b43f,  # Ypub
        'p2wpkh':      0x04b24746,  # zpub
        'p2wsh':       0x02aa7ed3,  # Zpub
    }
    XPUB_HEADERS_INV = inv_dict(XPUB_HEADERS)
    BIP44_COIN_TYPE = 805  # You may need to check if Scash has a different BIP44 coin type
    LN_REALM_BYTE = 0
    LN_DNS_SEEDS = []  # Scash doesn't have Lightning Network
    # URL for fetching updated server list (set this for SCASH)
    SERVERS_UPDATE_URL = "https://raw.githubusercontent.com/GoodMan365/electrum-scash/master/electrum/chains/scash/servers.json"
    SERVERS_CACHE_FILE = "servers_cache.json"
    SERVERS_CACHE_DURATION = 86400  # 24 hours in seconds
    
    # ASERT_ANCHOR_BITS
    ASERT_ACTIVATION_HEIGHT = 21000
    ASERT_HALFLIFE = 2 * 24 * 3600  # 2 days in seconds
    IDEAL_BLOCK_TIME = 600          # 10 minutes in seconds
    
    # Anchor Block Parameters (CRITICAL: Uses parent block 18143 timestamp!)
    ASERT_ANCHOR_HEIGHT = 18144
    ASERT_ANCHOR_HASH = "6ac8d61f06bc046d45fa9e29cd9d22cd40d26f415944d13eba37a2a0b91a51ad"
    ASERT_ANCHOR_BITS = 0x1c7b9d90
    ASERT_ANCHOR_PARENT_TIME = 1712987784  # Block 18143 timestamp
    ASERT_ANCHOR_PARENT_HASH = "7961a78acc6cde369b78c856190ff9950e166d396ca5cb984879a813172ad19c"
    
    # Scash PoW Limit (from genesis block)
    SCASH_POW_LIMIT = 0x00000fffff000000000000000000000000000000000000000000000000000000
    ASERT_TARGET_TOLERANCE = 0.003
    ASERT_MAX_ALLOWED_RATIO = 1 + ASERT_TARGET_TOLERANCE
    ASERT_MIN_ALLOWED_RATIO = 1 - ASERT_TARGET_TOLERANCE
    
    
    @classmethod
    def get_asert_anchor_params(cls):
        """Return ASERT anchor parameters for calculations."""
        return {
            'height': cls.ASERT_ANCHOR_HEIGHT,
            'bits': cls.ASERT_ANCHOR_BITS,
            'parent_time': cls.ASERT_ANCHOR_PARENT_TIME,
            'parent_hash': cls.ASERT_ANCHOR_PARENT_HASH
        }

    @classmethod
    def get_asert_tolerance(cls):
        """Return tolerance parameters."""
        return {
            'max_ratio': cls.ASERT_MAX_ALLOWED_RATIO,
            'min_ratio': cls.ASERT_MIN_ALLOWED_RATIO,
            'tolerance': cls.ASERT_TARGET_TOLERANCE
        }
        
   
    @classproperty
    def DEFAULT_SERVERS(cls):
        """Load servers with fallback: URL → Cache → Bundled → Hardcoded"""
        servers = None
        
        # 1. Try to fetch from URL (with caching)
        servers = cls._get_servers_from_url_with_cache()
        
        # 2. Fallback to bundled file
        if not servers:
            servers = cls._get_servers_from_bundled()
        
        # 3. Final fallback to hardcoded defaults
        if not servers:
            servers = cls._get_hardcoded_servers()
            
        return servers
    
    @classmethod
    def _get_servers_from_url_with_cache(cls):
        """Fetch servers from URL with local caching."""
        try:
            cache_dir = cls._get_cache_directory()
            cache_file = os.path.join(cache_dir, cls.SERVERS_CACHE_FILE)
            
            # Check cache freshness
            if os.path.exists(cache_file):
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cls.SERVERS_CACHE_DURATION:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            # Start background fetch if not already running
            # if not hasattr(cls, '_server_fetch_thread'):
                # cls._start_server_fetch_thread(cache_file)
            if not getattr(cls, '_server_fetch_thread', None):
                cls._start_server_fetch_thread(cache_file)
                # cls._server_fetch_thread = threading.Thread(...)
                # cls._server_fetch_thread.start()
            
            # Use stale cache if available while fetching fresh in background
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
        except Exception as e:
            print(f"URL server fetch failed: {e}")
        
        return None
    
    # @classmethod
    # def _start_server_fetch_thread(cls, cache_file):
        # """Start a background thread with its own asyncio loop to fetch servers."""
        # def run_async():
            # # Create a new event loop for this thread
            # loop = asyncio.new_event_loop()
            # asyncio.set_event_loop(loop)
            # try:
                # loop.run_until_complete(cls._fetch_servers_async(cache_file))
            # finally:
                # loop.close()

        # cls._server_fetch_thread = threading.Thread(group=None, target=run_async, daemon=True)
        # cls._server_fetch_thread.start()
        
    @classmethod
    def _start_server_fetch_thread(cls, cache_file):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(cls._fetch_servers_async(cache_file))
        except RuntimeError:
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(cls._fetch_servers_async(cache_file))
                finally:
                    loop.close()
            thread = threading.Thread(group=None, target=run_async, daemon=True)
            thread.start()
            cls._server_fetch_thread = thread

    @classmethod
    async def _fetch_servers_async(cls, cache_file):
        """Async coroutine to fetch and cache servers."""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            headers = {'User-Agent': 'Electrum-Scash/1.0'}
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(cls.SERVERS_UPDATE_URL, headers=headers) as response:  # ✅ headers passed
                    response.raise_for_status()
                    text = await response.text()
                    servers = json.loads(text)  #json.loads text/plain not json
                    #servers = await response.json()

                    # if isinstance(servers, dict):
                        # if servers and all(isinstance(v, dict) and ('t' in v or 's' in v) for v in servers.values()):
                            # os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                            # with open(cache_file, 'w', encoding='utf-8') as f:
                                # json.dump(servers, f, indent=2)
                                
                    if isinstance(servers, dict):
                        # Save to cache
                        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(servers, f, indent=2)
                        
        except Exception as e:
            print(f"Background server update failed: {e}")
    
    @classmethod
    def _get_servers_from_bundled(cls):
        """Load servers from bundled JSON file."""
        try:
            servers_file = cls._find_bundled_file('servers.json')
            with open(servers_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return None
    
    @classmethod
    def _get_cache_directory(cls):
        # Android: detected via environment variable set by p4a
        if 'ANDROID_DATA' in os.environ:
            from .util import scash_android_data_dir
            return os.path.join(scash_android_data_dir(), 'cache')
        
        # Windows
        if sys.platform == 'win32':
            appdata = os.environ.get('APPDATA')
            if appdata:
                return os.path.join(appdata, 'Electrum-Scash', 'cache')
            # Fallback if APPDATA missing
            return os.path.expanduser('~\\AppData\\Roaming\\Electrum-Scash\\cache')
        
        # macOS
        if sys.platform == 'darwin':
            return os.path.expanduser('~/Library/Application Support/Electrum-Scash/cache')
            # Note: On macOS, caches often go in Application Support for user-visible data
        
        # Linux 
        return os.path.expanduser('~/.electrum-scash/cache')
    # def _get_cache_directory(cls):
        # """Get platform-specific cache directory."""
        # if sys.platform == 'win32':
            # return os.path.join(os.environ.get('APPDATA', ''), 'Electrum-SCASH', 'cache')
        # else:
            # return os.path.expanduser('~/.electrum-scash/cache')
    
    @classmethod
    def _find_bundled_file(cls, filename):
        """Find bundled data files."""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            return os.path.join(base_path, 'electrum', 'chains', 'scash', filename)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(current_dir, 'chains', 'scash', filename)
    
    @classmethod
    def _get_hardcoded_servers(cls):
        """Hardcoded fallback servers."""
        return {
            "154.138.87.132": {"s": "50002"},
            "localhost": {"t": "50001", "s": "50002"}
        }
        
    @classmethod
    def datadir_subdir(cls):
        return cls.NET_NAME
    
    @classmethod
    def max_checkpoint(cls) -> int:
        """Return the height of the highest checkpoint."""
        if not cls.CHECKPOINTS:
            return 0
        # checkpoints.json loads as list
        if isinstance(cls.CHECKPOINTS, (list, tuple)):
            # Each checkpoint represents 2016 blocks
            return (len(cls.CHECKPOINTS) - 1) * 2016
        # Hardcoded checkpoints in constants are dict
        elif isinstance(cls.CHECKPOINTS, dict):
            return max(cls.CHECKPOINTS.keys())
        return 0


    
NETS_LIST = tuple(all_subclasses(AbstractNet))  # type: Sequence[Type[AbstractNet]]
NETS_LIST = tuple(sorted(NETS_LIST, key=lambda x: x.NET_NAME))

assert len(NETS_LIST) == len(set([chain.NET_NAME for chain in NETS_LIST])), "NET_NAME must be unique for each concrete AbstractNet"
assert len(NETS_LIST) == len(set([chain.datadir_subdir() for chain in NETS_LIST])), "datadir must be unique for each concrete AbstractNet"
assert len(NETS_LIST) == len(set([chain.cli_flag() for chain in NETS_LIST])), "cli_flag must be unique for each concrete AbstractNet"
assert len(NETS_LIST) == len(set([chain.config_key() for chain in NETS_LIST])), "config_key must be unique for each concrete AbstractNet"

# don't import net directly, import the module instead (so that net is singleton)
net = ScashMainnet  # type: Type[AbstractNet]
