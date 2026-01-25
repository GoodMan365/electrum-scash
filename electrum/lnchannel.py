"""Lightning channel stub for Scash."""

class AbstractChannel:
    def __init__(self, *args, **kwargs):
        pass

class Channel(AbstractChannel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_id = kwargs.get('channel_id', b'')
        self.funding_outpoint = kwargs.get('funding_outpoint', None)
        self.short_channel_id = kwargs.get('short_channel_id', None)

class ChannelBackup:
    def __init__(self, *args, **kwargs):
        pass

class ChannelState:
    PREOPENING      = 0  # Initial negotiation. Channel will not be reestablished
    OPENING         = 1  # Channel will be reestablished. (per BOLT2)
                         #  - Funding node: has received funding_signed (can broadcast the funding tx)
                         #  - Non-funding node: has sent the funding_signed message.
    FUNDED          = 2  # Funding tx was mined (requires min_depth and tx verification)
    OPEN            = 3  # both parties have sent funding_locked
    SHUTDOWN        = 4  # shutdown has been sent.
    CLOSING         = 5  # closing negotiation done. we have a fully signed tx.
    FORCE_CLOSING   = 6  # *we* force-closed, and closing tx is unconfirmed. Note that if the
                         # remote force-closes then we remain OPEN until it gets mined -
                         # the server could be lying to us with a fake tx.
    REQUESTED_FCLOSE = 7   # Chan is open, but we have tried to request the *remote* to force-close
    WE_ARE_TOXIC     = 8   # Chan is open, but we have lost state and the remote proved this.
                           # The remote must force-close, it is *not* safe for us to do so.
    CLOSED           = 9   # closing tx has been mined
    REDEEMED         = 10  # we can stop watching

class HTLCWithStatus:
    def __init__(self, *args, **kwargs):
        pass

class ChanCloseOption:
    COOPERATIVE = 1
    LOCAL_FORCE = 2
    REMOTE_FORCE = 3

def htlcsum(*args, **kwargs):
    return 0

__all__ = [
    'AbstractChannel', 'Channel', 'ChannelBackup', 'ChannelState',
    'HTLCWithStatus', 'ChanCloseOption', 'htlcsum'
]

