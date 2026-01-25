"""Lightning URL stub for Scash."""

class LNURLError(Exception):
    pass

class LNURLData:
    def __init__(self, *args, **kwargs):
        pass

class LNURL3Data:
    def __init__(self, *args, **kwargs):
        pass

class LNURL6Data:
    def __init__(self, *args, **kwargs):
        pass

def decode_lnurl(*args, **kwargs):
    raise LNURLError("Lightning not supported for Scash")

def request_lnurl(*args, **kwargs):
    raise LNURLError("Lightning not supported for Scash")

def callback_lnurl(*args, **kwargs):
    raise LNURLError("Lightning not supported for Scash")

def try_resolve_lnurlpay(*args, **kwargs):
    raise LNURLError("Lightning not supported for Scash")

def lightning_address_to_url(*args, **kwargs):
    raise LNURLError("Lightning not supported for Scash")

def request_lnurl_withdraw_callback(*args, **kwargs):
    raise LNURLError("Lightning not supported for Scash")

__all__ = [
    'LNURLError', 'LNURLData', 'LNURL3Data', 'LNURL6Data',
    'decode_lnurl', 'request_lnurl', 'callback_lnurl',
    'try_resolve_lnurlpay', 'lightning_address_to_url',
    'request_lnurl_withdraw_callback'
]
