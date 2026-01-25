"""Lightning transport stub for Scash."""

class LNPeerAddr:
    def __init__(self, host=None, port=None, pubkey=None):
        self.host = host
        self.port = port
        self.pubkey = pubkey
    
    @classmethod
    def from_str(cls, s):
        raise NotImplementedError("Lightning Network is not supported for Scash")
    
    def __str__(self):
        return f"LNPeerAddr({self.host}:{self.port})" if self.host else "LNPeerAddr()"

class LNTransport:
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

class ConnStringFormatError(Exception):
    pass

def extract_nodeid(conn_str: str) -> bytes:
    """Extract node ID from connection string (stub)."""
    # This might be called from wallet.py or GUI
    # Return dummy bytes
    return b'\x00' * 33

def split_host_port(s: str):
    """Split host and port (stub)."""
    if ':' in s:
        host, port = s.split(':')
        return host, int(port)
    return s, 9735  # Default lightning port

# Minimal exports
__all__ = ['LNPeerAddr', 'LNTransport', 'ConnStringFormatError', 'extract_nodeid', 'split_host_port']
