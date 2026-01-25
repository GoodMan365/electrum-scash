"""Lightning address decoding stub for Scash (Lightning not supported)."""

class LnAddr:
    """Dummy Lightning address class."""
    def __init__(self, *args, **kwargs):
        self.amount = kwargs.get('amount', 0)
        self.paymenthash = kwargs.get('paymenthash', b'')
        self.timestamp = kwargs.get('timestamp', 0)
    
    def __str__(self):
        return "LnAddr(lightning not supported)"

class LnDecodeException(Exception):
    pass
    
class LnInvoiceException(Exception):
    pass


def lndecode(invoice: str, expected_hrp: str = None, verbose: bool = False) -> LnAddr:
    """Decode a lightning invoice (stub for Scash)."""
    # Check if this looks like a lightning invoice
    if invoice.startswith('ln') or invoice.startswith('LN'):
        raise LnDecodeException("Lightning Network is not supported for Scash. Cannot decode lightning invoices.")
    
    # Return a dummy object to avoid breaking existing code
    return LnAddr()

def lndecode_anything(invoice: str, verbose: bool = False):
    """More permissive version of lndecode."""
    return lndecode(invoice, verbose=verbose)

# Export the expected functions
__all__ = ['lndecode', 'lndecode_anything', 'LnAddr', 'LnDecodeException', 'LnInvoiceException']
