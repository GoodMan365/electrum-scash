"""Stub module for Lightning (not supported in Scash)."""

class LNWorker:
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return None

class LNWallet:
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return None

# Stub functions
def dummy(*args, **kwargs):
    return None

# Export stubs
__all__ = ['LNWorker', 'LNWallet']

