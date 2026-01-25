"""Complete Lightning stub module for Scash."""

# Define all Lightning classes that might be imported
class LNPeerAddr:
    pass

class LNTransport:
    pass

class LNWallet:
    pass

class LNWorker:
    pass

class LNRater:
    pass

class LNPathFinder:
    pass

class ChannelDB:
    pass

class LNGossip:
    pass

class LNSwapManager:
    pass

# Stub functions
def dummy(*args, **kwargs):
    return None

def raise_not_implemented(*args, **kwargs):
    raise NotImplementedError("Lightning Network is not supported for Scash")

# Export everything
__all__ = [
    'LNPeerAddr', 'LNTransport', 'LNWallet', 'LNWorker',
    'LNRater', 'LNPathFinder', 'ChannelDB', 'LNGossip',
    'LNSwapManager', 'dummy', 'raise_not_implemented'
]
