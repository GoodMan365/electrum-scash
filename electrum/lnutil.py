"""Lightning utilities stub for Scash."""

import hashlib

# Define constants that other files might expect
MIN_FINAL_CLTV_DELTA_ACCEPTED = 200
NBLOCK_CLTV_DELTA_TOO_FAR_INTO_FUTURE = 1008
LN_MAX_FUNDING_SAT_LEGACY = 16777215
LN_P2P_NETWORK_TIMEOUT = 15

# Funding constants
MIN_FUNDING_SAT = 10000  # Minimum funding amount
MAX_FUNDING_SAT = 16777215  # Maximum funding amount (legacy)
MAX_FUNDING_SAT_NON_LEGACY = 100000000  # 1 BTC
MAX_HTLC_VALUE_MSAT = 100000000000  # 1 BTC in msat
REDEEM_AFTER_DOUBLE_SPENT_DELAY = 144  # blocks

# Direction constants
LOCAL = 0
REMOTE = 1
SENT = 0
RECEIVED = 1

# Enums and constants
class LnFeatures:
    OPTION_STATIC_REMOTEKEY = 1
    OPTION_ANCHOR_OUTPUTS = 2
    OPTION_ZEROCONF = 4

class HTLCOwner:
    LOCAL = 0
    REMOTE = 1

class ChannelType:
    CHANNEL_TYPE_OPTION_STATIC_REMOTEKEY = 0
    CHANNEL_TYPE_OPTION_ANCHOR_OUTPUTS = 1

class RecvMPPResolution:
    NORMAL = 0
    TIMEOUT = 1

class PaymentDirection:
    SENT = 0
    RECEIVED = 1

# HTLC classes
class UpdateAddHtlc:
    def __init__(self, *args, **kwargs):
        self.amount_msat = kwargs.get('amount_msat', 0)
        self.payment_hash = kwargs.get('payment_hash', b'')
        self.cltv_expiry = kwargs.get('cltv_expiry', 0)
        self.channel_id = kwargs.get('channel_id', b'')

class HtlcLog:
    def __init__(self, *args, **kwargs):
        pass

class Direction:
    SENT = 0
    RECEIVED = 1

# Error classes
class IncompatibleOrInsaneFeatures(Exception):
    pass

class FeeBudgetExceeded(Exception):
    pass

class NoPathFound(Exception):
    pass

class InvalidGossipMsg(Exception):
    pass

class GossipForwardingMessage:
    def __init__(self, *args, **kwargs):
        pass

class GossipTimestampFilter:
    def __init__(self, *args, **kwargs):
        pass

class Keypair:
    def __init__(self, *args, **kwargs):
        self.pubkey = kwargs.get('pubkey', b'')
        self.privkey = kwargs.get('privkey', b'')

# Utility functions
def hex_to_bytes(hex_string: str) -> bytes:
    """Convert hex string to bytes."""
    if not hex_string:
        return b''
    return bytes.fromhex(hex_string)

def bytes_to_hex(byte_string: bytes) -> str:
    """Convert bytes to hex string."""
    return byte_string.hex()

def derive_payment_secret_from_payment_preimage(preimage: bytes) -> bytes:
    """Stub for payment secret derivation."""
    return preimage[:32] if preimage else b'\x00' * 32

def get_ecdh(priv: bytes, pub: bytes) -> bytes:
    """Stub for ECDH computation."""
    return hashlib.sha256(priv + pub).digest()

def channel_id_from_funding_tx(txid, index):
    """Return a dummy channel ID."""
    h = hashlib.sha256(f"{txid}:{index}".encode()).digest()
    return h, 0

def format_short_channel_id(scid):
    if hasattr(scid, 'block_height'):
        return f"{scid.block_height}x{scid.tx_index}x{scid.output_index}"
    return "0x0x0"

def generate_random_keypair():
    """Generate a random keypair (stub)."""
    return Keypair(pubkey=b'\x00' * 33, privkey=b'\x00' * 32)

def validate_features(features, *args, **kwargs):
    """Validate features (stub)."""
    return True

class ShortChannelID:
    def __init__(self, block_height, tx_index, output_index):
        self.block_height = block_height
        self.tx_index = tx_index
        self.output_index = output_index
    
    @classmethod
    def from_str(cls, s):
        parts = s.split('x')
        return cls(int(parts[0]), int(parts[1]), int(parts[2]))
    
    def __str__(self):
        return f"{self.block_height}x{self.tx_index}x{self.output_index}"

class PaymentFeeBudget:
    def __init__(self, fee_msat=None, fee_percent=None):
        self.fee_msat = fee_msat
        self.fee_percent = fee_percent

# Export everything
__all__ = [
    'MIN_FINAL_CLTV_DELTA_ACCEPTED',
    'NBLOCK_CLTV_DELTA_TOO_FAR_INTO_FUTURE',
    'LN_MAX_FUNDING_SAT_LEGACY',
    'LN_P2P_NETWORK_TIMEOUT',
    'MIN_FUNDING_SAT',
    'MAX_FUNDING_SAT',
    'MAX_FUNDING_SAT_NON_LEGACY',
    'MAX_HTLC_VALUE_MSAT',
    'REDEEM_AFTER_DOUBLE_SPENT_DELAY',
    'LOCAL',
    'REMOTE',
    'SENT',
    'RECEIVED',
    'LnFeatures',
    'HTLCOwner',
    'ChannelType',
    'RecvMPPResolution',
    'PaymentDirection',
    'UpdateAddHtlc',
    'HtlcLog',
    'Direction',
    'IncompatibleOrInsaneFeatures',
    'FeeBudgetExceeded',
    'NoPathFound',
    'InvalidGossipMsg',
    'GossipForwardingMessage',
    'GossipTimestampFilter',
    'Keypair',
    'hex_to_bytes',
    'bytes_to_hex',
    'derive_payment_secret_from_payment_preimage',
    'get_ecdh',
    'channel_id_from_funding_tx',
    'format_short_channel_id',
    'generate_random_keypair',
    'validate_features',
    'ShortChannelID',
    'PaymentFeeBudget',
]
