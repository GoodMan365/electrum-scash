"""Lightning worker stub for Scash."""

class LNWallet:
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return None

class LNGossip:
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return None

def hardcoded_trampoline_nodes():
    return []

__all__ = ['LNWallet', 'LNGossip', 'hardcoded_trampoline_nodes']
