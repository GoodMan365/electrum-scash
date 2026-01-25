"""Lightning verifier stub for Scash."""

class LNChannelVerifier:
    def __init__(self, *args, **kwargs):
        pass

def verify_sig_for_channel_update(*args, **kwargs):
    return False

__all__ = ['LNChannelVerifier', 'verify_sig_for_channel_update']
