"""Lightning messages stub for Scash."""

class OnionWireSerializer:
    def __init__(self, *args, **kwargs):
        pass

class FailedToParseMsg(Exception):
    pass

def decode_msg(*args, **kwargs):
    raise FailedToParseMsg("Lightning not supported")

__all__ = ['OnionWireSerializer', 'FailedToParseMsg', 'decode_msg']
