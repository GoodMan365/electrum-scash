"""Lightning onion stub for Scash."""

PER_HOP_HMAC_SIZE = 32
TRAMPOLINE_HOPS_DATA_SIZE = 400

class OnionHopsDataSingle:
    def __init__(self, *args, **kwargs):
        pass

class OnionPacket:
    def __init__(self, *args, **kwargs):
        pass

class OnionFailureCode:
    TEMPORARY_NODE_FAILURE = 2
    TEMPORARY_CHANNEL_FAILURE = 3

class OnionRoutingFailure(Exception):
    pass

def get_bolt04_onion_key(*args, **kwargs):
    return b'\x00' * 32

def get_shared_secrets_along_route(*args, **kwargs):
    return []

def encrypt_hops_recipient_data(*args, **kwargs):
    return b''

def decrypt_onionmsg_data_tlv(*args, **kwargs):
    return {}

def encrypt_onionmsg_data_tlv(*args, **kwargs):
    return b''

def new_onion_packet(*args, **kwargs):
    return OnionPacket()

def process_onion_packet(*args, **kwargs):
    return []

def calc_hops_data_for_payment(*args, **kwargs):
    return b''

__all__ = [
    'PER_HOP_HMAC_SIZE', 'TRAMPOLINE_HOPS_DATA_SIZE',
    'OnionHopsDataSingle', 'OnionPacket', 'OnionFailureCode',
    'OnionRoutingFailure', 'get_bolt04_onion_key',
    'get_shared_secrets_along_route', 'encrypt_hops_recipient_data',
    'decrypt_onionmsg_data_tlv', 'encrypt_onionmsg_data_tlv',
    'new_onion_packet', 'process_onion_packet', 'calc_hops_data_for_payment'
]
