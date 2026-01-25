# Electrum-Scash - lightweight Scash client Forked From Electrum
# Copyright (C) 2012 thomasv@ecdsa.org
# Copyright (C) 2025 The Electrum-Scash Developers

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os
import threading
import time
from typing import Optional, Dict, Mapping, Sequence, TYPE_CHECKING
import struct
from . import util
from .bitcoin import hash_encode
from .crypto import sha256d
from . import constants
from .util import bfh, with_lock
from .logging import get_logger, Logger
import hashlib
#from .randomx_commitment import compute_commitment, commitment_meets_target
#from . import blockchain

if TYPE_CHECKING:
    from .simple_config import SimpleConfig

_logger = get_logger(__name__)

HEADER_SIZE = 112  # bytes
CHUNK_SIZE = 2016  # num headers in a difficulty retarget period
ASERT_HALFLIFE = 2 * 24 * 3600  # 2 days in seconds
IDEAL_BLOCK_TIME = 600  # 10 minutes in seconds
ASERT_PRECISION_BITS = 16  # 65536 = 2^16 for fixed-point arithmetic
ASERT_PRECISION = 1 << ASERT_PRECISION_BITS  # 65536
POW_LIMIT = 0x00000fffff000000000000000000000000000000000000000000000000000000
# see https://github.com/bitcoin/bitcoin/blob/feedb9c84e72e4fff489810a2bbeec09bcda5763/src/chainparams.cpp#L76
MAX_TARGET = POW_LIMIT
#0x00000fffff000000000000000000000000000000000000000000000000000000  # compact: 0x1d00ffff


class MissingHeader(Exception):
    pass


class InvalidHeader(Exception):
    pass


# def serialize_header(header_dict: dict) -> bytes:
#     """Serialize SCASH 112-byte header."""
#     s = (
#         int.to_bytes(header_dict['version'], length=4, byteorder="little", signed=False)
#         + bfh(header_dict['prev_block_hash'])[::-1]
#         + bfh(header_dict['merkle_root'])[::-1]
#         + int.to_bytes(int(header_dict['timestamp']), length=4, byteorder="little", signed=False)
#         + int.to_bytes(int(header_dict['bits']), length=4, byteorder="little", signed=False)
#         + int.to_bytes(int(header_dict['nonce']), length=4, byteorder="little", signed=False)
#         + bfh(header_dict['hashRandomX'])[::-1]  # 32-byte RandomX hash
#     )
#     assert len(s) == HEADER_SIZE
#     return s


def serialize_header(header_dict: dict) -> bytes:
    """Serialize SCASH 112-byte header to STORAGE format."""
    
    # Helper: Convert to little-endian bytes
    def to_le_bytes(value):
        if isinstance(value, str):
            # Hex string like "20000000" -> int -> little-endian
            return int(value, 16).to_bytes(4, 'little')
        else:
            return value.to_bytes(4, 'little')
    
    # Version (4 bytes, little-endian)
    version_bytes = to_le_bytes(header_dict['version'])
    
    # Prev hash (32 bytes) - display → storage
    prev_hash_bytes = bytes.fromhex(header_dict['prev_block_hash'])[::-1]
    
    # Merkle root (32 bytes) - display → storage
    merkle_bytes = bytes.fromhex(header_dict['merkle_root'])[::-1]
    
    # Timestamp (4 bytes, little-endian)
    time_bytes = to_le_bytes(header_dict['timestamp'])
    
    # Bits (4 bytes, little-endian)
    bits_bytes = to_le_bytes(header_dict['bits'])
    
    # Nonce (4 bytes, little-endian)
    nonce_bytes = to_le_bytes(header_dict['nonce'])
    
    # hashRandomX (32 bytes) - display → storage
    rx_hex = header_dict.get('hashRandomX', '00' * 32)
    randomx_bytes = bytes.fromhex(rx_hex)[::-1]
    
    # Combine: 4 + 32 + 32 + 4 + 4 + 4 + 32 = 112 bytes
    result = (version_bytes + prev_hash_bytes + merkle_bytes + 
              time_bytes + bits_bytes + nonce_bytes + randomx_bytes)
    
    if len(result) != 112:
        raise ValueError(f"Serialized header is {len(result)} bytes, expected 112")
    
    return result
    
def deserialize_header(s: bytes, height: int) -> dict:
    """Deserialize SCASH 112-byte header from STORAGE format."""
    if len(s) != 112:  # Use constant HEADER_SIZE if defined
        raise InvalidHeader(f'Invalid header length: {len(s)} (expected 112)')
    
    # Unpack: version(4), prev_hash(32), merkle_root(32), timestamp(4), bits(4), nonce(4), hashRandomX(32)
    # '<I' = little-endian unsigned int (4 bytes)
    # '32s' = 32-byte string (raw bytes)
    version, prev_hash, merkle_root, timestamp, bits, nonce, hash_randomx = struct.unpack(
        '<I32s32sIII32s', s
    )
    
    # Convert to display format for dict
    return {
        'version': version,
        'prev_block_hash': prev_hash[::-1].hex(),  # storage → display
        'merkle_root': merkle_root[::-1].hex(),    # storage → display
        'timestamp': timestamp,
        'bits': bits,
        'nonce': nonce,
        'hashRandomX': hash_randomx[::-1].hex(),   # storage → display
        'block_height': height,
    }



def hash_header(header: dict) -> str:
    if header is None:
        return '0' * 64
    if header.get('prev_block_hash') is None:
        header['prev_block_hash'] = '00' * 32
    raw = serialize_header(header)
    h = hash_raw_header(raw)
    
    return h


def hash_raw_header(header: bytes) -> str:
    """Block hash = SHA256(SHA256(full 112-byte header))"""
    if len(header) != HEADER_SIZE:
        raise InvalidHeader(f'Cannot hash header of size {len(header)}')
    return hash_encode(sha256d(header))


# def compute_commitment(header_dict: dict) -> str:
    # """
    # Compute Scash RandomX commitment for block validation.
    
    # Args:
        # header_dict: Dictionary with header fields:
            # - version: int
            # - prev_block_hash: str (hex, display format)
            # - merkle_root: str (hex, display format) 
            # - timestamp: int
            # - bits: int
            # - nonce: int
            # - hashRandomX: str (hex, display format from RPC)
    
    # Returns:
        # Commitment hash as hex string in DISPLAY format
    # """
    # import hashlib
    
    # # 1. Convert hashRandomX from DISPLAY to STORAGE format
    # rx_display = header_dict['hashRandomX']
    # rx_storage = bytes.fromhex(rx_display)[::-1]
    
    # # 2. Serialize header with zeroed hashRandomX
    # header_zeroed = {
        # 'version': header_dict['version'],
        # 'prev_block_hash': header_dict['prev_block_hash'],
        # 'merkle_root': header_dict['merkle_root'],
        # 'timestamp': header_dict['timestamp'],
        # 'bits': header_dict['bits'],
        # 'nonce': header_dict['nonce'],
        # 'hashRandomX': '00' * 32,  # Zeroed
    # }
    
    # header_bytes = serialize_header(header_zeroed)
    
    # # 3. Compute Blake2b-256(header_zeroed || rx_storage)
    # blake = hashlib.blake2b(digest_size=32)
    # blake.update(header_bytes)
    # blake.update(rx_storage)
    
    # # 4. Convert result to DISPLAY format
    # commitment_storage = blake.digest()
    # commitment_display = commitment_storage[::-1].hex()
    
    # return commitment_display
def compute_commitment(header_dict: dict) -> bytes:
    """Correct Scash RandomX commitment."""
    # 1. Get hashRandomX in STORAGE format
    rx_display = header_dict['hashRandomX']
    rx_storage = bytes.fromhex(rx_display)[::-1]  # Display → Storage
    
    # 2. Serialize header with zeroed hashRandomX
    header_zeroed = header_dict.copy()
    header_zeroed['hashRandomX'] = '00' * 32
    header_bytes_zeroed = serialize_header(header_zeroed)
    
    # 3. Compute Blake2b-256(header_zeroed || rx_storage)
    blake = hashlib.blake2b(digest_size=32)
    blake.update(header_bytes_zeroed)
    blake.update(rx_storage)
    
    # 4. Return in DISPLAY format
    return blake.digest()[::-1]
    
def commitment_meets_target(commitment: bytes, target: int) -> bool:
    """Check if commitment meets target."""
    # Commitment is in DISPLAY format from compute_commitment
    cm_int = int.from_bytes(commitment, byteorder='big')
    return cm_int <= target
    
# def commitment_meets_target(commitment_hex: str, target: int) -> bool:
    # """Check if commitment meets target."""
    # # Commitment hex is in DISPLAY format
    # cm_int = int(commitment_hex, 16)
    # return cm_int <= target
    

pow_hash_header = hash_header


# key: blockhash hex at forkpoint
# the chain at some key is the best chain that includes the given hash
blockchains = {}  # type: Dict[str, Blockchain]
blockchains_lock = threading.RLock()  # lock order: take this last; so after Blockchain.lock


def read_blockchains(config: 'SimpleConfig'):
    best_chain = Blockchain(config=config,
                            forkpoint=0,
                            parent=None,
                            forkpoint_hash=constants.net.GENESIS,
                            prev_hash=None)
    blockchains[constants.net.GENESIS] = best_chain
    # consistency checks
    # consistency checks - MODIFIED to preserve headers beyond checkpoints
    max_cp = constants.net.max_checkpoint()
    chain_height = best_chain.height()
    
    if chain_height > max_cp:
        _logger.info((f"[blockchain] Chain extends beyond checkpoints: height={chain_height}, max_checkpoint={max_cp}"))
        
        # Don't delete the file, just verify checkpoint if possible
        header_at_cp = best_chain.read_header(max_cp)
        if header_at_cp:
            # Optional: verify checkpoint hash
            pass
    # forks
    fdir = os.path.join(util.get_headers_dir(config), 'forks')
    util.make_dir(fdir)
    # files are named as: fork2_{forkpoint}_{prev_hash}_{first_hash}
    l = filter(lambda x: x.startswith('fork2_') and '.' not in x, os.listdir(fdir))
    l = sorted(l, key=lambda x: int(x.split('_')[1]))  # sort by forkpoint

    def delete_chain(filename, reason):
        _logger.info(f"[blockchain] deleting chain {filename}: {reason}")
        os.unlink(os.path.join(fdir, filename))

    def instantiate_chain(filename):
        __, forkpoint, prev_hash, first_hash = filename.split('_')
        forkpoint = int(forkpoint)
        prev_hash = (64-len(prev_hash)) * "0" + prev_hash  # left-pad with zeroes
        first_hash = (64-len(first_hash)) * "0" + first_hash
        # forks below the max checkpoint are not allowed
        if forkpoint <= constants.net.max_checkpoint():
            delete_chain(filename, "deleting fork below max checkpoint")
            return
        # find parent (sorting by forkpoint guarantees it's already instantiated)
        for parent in blockchains.values():
            if parent.check_hash(forkpoint - 1, prev_hash):
                break
        else:
            delete_chain(filename, "cannot find parent for chain")
            return
        b = Blockchain(config=config,
                       forkpoint=forkpoint,
                       parent=parent,
                       forkpoint_hash=first_hash,
                       prev_hash=prev_hash)
        # consistency checks
        h = b.read_header(b.forkpoint)
        if first_hash != hash_header(h):
            delete_chain(filename, "incorrect first hash for chain")
            return
        if not b.parent.can_connect(h, check_height=False):
            delete_chain(filename, "cannot connect chain to parent")
            return
        chain_id = b.get_id()
        assert first_hash == chain_id, (first_hash, chain_id)
        blockchains[chain_id] = b

    for filename in l:
        instantiate_chain(filename)


def get_best_chain() -> 'Blockchain':
    return blockchains[constants.net.GENESIS]


# block hash -> chain work; up to and including that block
_CHAINWORK_CACHE = {
    "0000000000000000000000000000000000000000000000000000000000000000": 0,  # virtual block at height -1
}  # type: Dict[str, int]



def init_headers_file_for_best_chain():
    
    b = get_best_chain()
    filename = b.path()
    
    # If file exists, preserve it
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        current_size = os.path.getsize(filename)
        headers_count = current_size // HEADER_SIZE
        with b.lock:
            b.update_size()
        return
    
    # File doesn't exist - create empty file
    open(filename, 'wb').close()
    
    with b.lock:
        b.update_size()
    
    # Optional: Pre-allocate space for checkpoints for faster sync
    if constants.net.CHECKPOINTS:
        checkpoint_len = len(constants.net.CHECKPOINTS)
        checkpoint_headers = (checkpoint_len-1) * 2016
        checkpoint_size = checkpoint_headers * HEADER_SIZE
        # Extend file to checkpoint size (makes sync faster)
        with open(filename, 'rb+') as f:
            f.seek(checkpoint_size - 1)
            f.write(b'\x00')
        
def _init_headers_file(self):
    """Initialize the headers file with the genesis header."""
    # Check if we already have the genesis header
    existing = self.read_header(0)
    if existing is not None:
        return
    
    # Create the genesis header for Scash
    genesis = {
        'version': 1,
        'prev_block_hash': '0' * 64,
        'merkle_root': 'c62664cb430ef1061c9d1d8f607ca312fefc9996d413d273ee4782fdfa907b2f',
        'timestamp': 1454124731,  # 0xd8efd765
        'bits': 0xffff0f1e,
        'nonce': 0x3f593201,
        'hashRandomX': constants.net.GENESIS_RANDOMX_HASH,
        'block_height': 0,
    }
    
    # Verify the genesis hash matches
    genesis_hash = hash_header(genesis)
    if genesis_hash != constants.net.GENESIS:
        self.logger.error(f"Generated genesis hash {genesis_hash} doesn't match expected {constants.net.GENESIS}")
        raise Exception("Genesis hash mismatch")
    
    # Write genesis header
    #data = bfh(serialize_header(genesis))
    data = serialize_header(genesis)
    self.write(data, 0) 
    self._size = 1
    self._prev_hash = genesis_hash


class Blockchain(Logger):
    """
    Manages blockchain headers and their verification
    """

    def __init__(self, config: 'SimpleConfig', forkpoint: int, parent: Optional['Blockchain'],
                 forkpoint_hash: str, prev_hash: Optional[str]):
        assert isinstance(forkpoint_hash, str) and len(forkpoint_hash) == 64, forkpoint_hash
        assert (prev_hash is None) or (isinstance(prev_hash, str) and len(prev_hash) == 64), prev_hash
        # assert (parent is None) == (forkpoint == 0)
        if 0 < forkpoint <= constants.net.max_checkpoint():
            raise Exception(f"cannot fork below max checkpoint. forkpoint: {forkpoint}")
        Logger.__init__(self)
        self.config = config
        self.forkpoint = forkpoint  # height of first header
        self.parent = parent
        self._forkpoint_hash = forkpoint_hash  # blockhash at forkpoint. "first hash"
        self._prev_hash = prev_hash  # blockhash immediately before forkpoint
        self.lock = threading.RLock()
        self.update_size()

        if self.checkpoints and len(self.checkpoints) > 0:
            # Show first and last checkpoints
            
            # Calculate what height the last checkpoint represents
            last_checkpoint_height = (len(self.checkpoints) - 1) * 2016
            
            # Verify genesis
            if isinstance(self.checkpoints[0], (list, tuple)) and len(self.checkpoints[0]) > 0:
                checkpoint_genesis = self.checkpoints[0][0]
        
        # Convert checkpoints list to dict for easier access
        self.checkpoint_dict = {}
        for i, (hash_val, chainwork) in enumerate(self.checkpoints):
            height = i * 2016
            self.checkpoint_dict[height] = (hash_val, chainwork)
        
        if 0 in self.checkpoint_dict:
            genesis_hash, _ = self.checkpoint_dict[0]
        
        # Calculate expected tip from checkpoints
        max_checkpoint_height = (len(self.checkpoints) - 1) * 2016

        #self.analyze_sync_strategy()

    @property
    def checkpoints(self):
        return constants.net.CHECKPOINTS

    def get_max_child(self) -> Optional[int]:
        children = self.get_direct_children()
        return max([x.forkpoint for x in children]) if children else None

    def get_max_forkpoint(self) -> int:
        """Returns the max height where there is a fork
        related to this chain.
        """
        mc = self.get_max_child()
        return mc if mc is not None else self.forkpoint

    def get_direct_children(self) -> Sequence['Blockchain']:
        with blockchains_lock:
            return list(filter(lambda y: y.parent==self, blockchains.values()))

    def get_parent_heights(self) -> Mapping['Blockchain', int]:
        """Returns map: (parent chain -> height of last common block)"""
        with self.lock, blockchains_lock:
            result = {self: self.height()}
            chain = self
            while True:
                parent = chain.parent
                if parent is None: break
                result[parent] = chain.forkpoint - 1
                chain = parent
            return result

    def get_height_of_last_common_block_with_chain(self, other_chain: 'Blockchain') -> int:
        last_common_block_height = 0
        our_parents = self.get_parent_heights()
        their_parents = other_chain.get_parent_heights()
        for chain in our_parents:
            if chain in their_parents:
                h = min(our_parents[chain], their_parents[chain])
                last_common_block_height = max(last_common_block_height, h)
        return last_common_block_height

    @with_lock
    def get_branch_size(self) -> int:
        return self.height() - self.get_max_forkpoint() + 1

    def get_name(self) -> str:
        return self.get_hash(self.get_max_forkpoint()).lstrip('0')[0:10]

    def check_header(self, header: dict) -> bool:
        header_hash = hash_header(header)
        height = header.get('block_height')
        return self.check_hash(height, header_hash)

    def check_hash(self, height: int, header_hash: str) -> bool:
        """Returns whether the hash of the block at given height
        is the given hash.
        """
        assert isinstance(header_hash, str) and len(header_hash) == 64, header_hash  # hex
        try:
            return header_hash == self.get_hash(height)
        except Exception:
            return False

    # def fork(parent, header: dict) -> 'Blockchain':
    #     if not parent.can_connect(header, check_height=False):
    #         raise Exception("forking header does not connect to parent chain")
    #     forkpoint = header.get('block_height')
    #     self = Blockchain(config=parent.config,
    #                       forkpoint=forkpoint,
    #                       parent=parent,
    #                       forkpoint_hash=hash_header(header),
    #                       prev_hash=parent.get_hash(forkpoint-1))
    #     self.assert_headers_file_available(parent.path())
    #     open(self.path(), 'w+').close()
    #     self.save_header(header)
    #     # put into global dict. note that in some cases
    #     # save_header might have already put it there but that's OK
    #     chain_id = self.get_id()
    #     with blockchains_lock:
    #         blockchains[chain_id] = self
    #     return self

    def fork(parent, header: dict) -> 'Blockchain':
        """Create a new blockchain that forks from parent at header."""
        height = header.get('block_height')
        header_hash = hash_header(header)
        
        
        # Check if this is a checkpoint height
        if height % 2016 == 0:
            checkpoint_index = height // 2016
            if checkpoint_index < len(parent.checkpoints):
                checkpoint_data = parent.checkpoints[checkpoint_index]
                if isinstance(checkpoint_data, (list, tuple)) and len(checkpoint_data) >= 1:
                    expected_hash = checkpoint_data[0]
                    if expected_hash and expected_hash != "":
                        if expected_hash != header_hash:
                            raise Exception(f"Cannot fork at checkpoint height {height}: hash mismatch")
        
        if not parent.can_connect(header, check_height=False):
            raise Exception("forking header does not connect to parent chain")
        
        forkpoint = height
        self = Blockchain(config=parent.config,
                        forkpoint=forkpoint,
                        parent=parent,
                        forkpoint_hash=header_hash,
                        prev_hash=parent.get_hash(forkpoint-1))
        self.assert_headers_file_available(parent.path())
        open(self.path(), 'w+').close()
        self.save_header(header)
        
        # put into global dict
        chain_id = self.get_id()
        with blockchains_lock:
            blockchains[chain_id] = self
        
        return self

    def get_checkpoint_at_height(self, height: int):
        """Get checkpoint data for a given height."""
        if height % 2016 != 0:
            return None
        
        checkpoint_index = height // 2016
        if checkpoint_index < len(self.checkpoints):
            return self.checkpoints[checkpoint_index]
        return None
        
    def verify_checkpoint(self, height: int, header_hash: str) -> bool:
        """Verify a header against checkpoints."""
        checkpoint_data = self.get_checkpoint_at_height(height)
        if not checkpoint_data:
            return True  # No checkpoint for this height
            
        expected_hash = checkpoint_data[0]
        if not expected_hash or expected_hash == "":
            return True  # Empty checkpoint
            
        if expected_hash == header_hash:
            self.logger.debug(f"[OK] Checkpoint verified at height {height}")
            return True
        else:
            self.logger.error(f"[FAIL] Checkpoint mismatch at height {height}")
            self.logger.error(f"  Expected: {expected_hash}")
            self.logger.error(f"  Got:      {header_hash}")
            return False
        

    def analyze_sync_strategy(self):
        """Analyze how Electrum should sync with checkpoints."""
        self.logger.info("\n" + "="*70)
        self.logger.info("SYNC STRATEGY ANALYSIS")
        self.logger.info("="*70)
        
        # 1. Current local state
        local_height = self.height() if self.height() is not None else -1
        self.logger.info(f"1. Local chain:")
        self.logger.info(f"   Height: {local_height}")
        self.logger.info(f"   Forkpoint: {self.forkpoint}")
        
        # 2. Checkpoints
        self.logger.info(f"\n2. Checkpoints:")
        self.logger.info(f"   Number of checkpoints: {len(self.checkpoints)}")
        
        if self.checkpoints:
            last_checkpoint_index = len(self.checkpoints) - 1
            last_checkpoint_height = last_checkpoint_index * 2016
            last_checkpoint_hash = self.checkpoints[last_checkpoint_index][0][:16] + "..."
            
            self.logger.info(f"   Last checkpoint: height={last_checkpoint_height}, hash={last_checkpoint_hash}")
            
            # 3. Determine sync strategy
            self.logger.info(f"\n3. Recommended sync strategy:")
            
            if local_height < 0:
                self.logger.info(f"   --> No local chain, start from genesis")
            elif local_height < last_checkpoint_height:
                self.logger.info(f"   --> Local chain ({local_height}) behind last checkpoint ({last_checkpoint_height})")
                self.logger.info(f"   --> Should sync FROM checkpoint {last_checkpoint_height}")
            elif local_height == last_checkpoint_height:
                self.logger.info(f"   --> At checkpoint {last_checkpoint_height}, sync forward")
            else:
                self.logger.info(f"   --> Ahead of checkpoints, sync normally")
        
        self.logger.info("="*70 + "\n")
        
    @with_lock
    def height(self) -> int:
        return self.forkpoint + self.size() - 1

    @with_lock
    def size(self) -> int:
        return self._size

    
    @with_lock
    def update_size(self) -> None:
        with self.lock:
            p = self.path()
            if not os.path.exists(p):
                self._size = 0
                return
                
            # SIMPLE: I am using file size
            file_size = os.path.getsize(p)
            headers_count = file_size // HEADER_SIZE
            
            self._size = headers_count  



    @classmethod
    def genesis(cls):
        if constants.net.NET_NAME == "scash":
            return {
                'version': 1,
                'prev_block_hash': '0' * 64,
                'merkle_root': 'c62664cb430ef1061c9d1d8f607ca312fefc9996d413d273ee4782fdfa907b2f',
                'timestamp': 1454124731,  # 0xd8efd765
                'bits': 0xffff0f1e,
                'nonce': 0x3f593201,
                'hashRandomX': constants.net.GENESIS_RANDOMX_HASH,
                'block_height': 0,
            }
        else:
            return {
                'version': 1,
                'prev_block_hash': '0000000000000000000000000000000000000000000000000000000000000000',
                'merkle_root': '4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b',
                'timestamp': 1231006505,
                'bits': 0x1d00ffff,
                'nonce': 2083236893,
                'block_height': 0,
            }
        

    @classmethod
    def _verify_header(cls, header: dict, prev_hash: str, target: int, expected_header_hash: str = None) -> None:
        height = header.get('block_height', 0)

        # 1. Verify block hash and prev_hash
        _hash = hash_header(header)
        if expected_header_hash and expected_header_hash != _hash:
            raise InvalidHeader("hash mismatch")
            
        # 2. Skip prev_hash check if None (checkpoint sync case)
        if prev_hash is not None and prev_hash != header.get('prev_block_hash'):
            raise InvalidHeader("prev hash mismatch")

        if height % 2016 == 0:
            checkpoint_index = height // 2016
            # Access checkpoints through the class
            if checkpoint_index < len(constants.net.CHECKPOINTS):
                checkpoint_data = constants.net.CHECKPOINTS[checkpoint_index]
                if isinstance(checkpoint_data, (list, tuple)) and len(checkpoint_data) > 0:
                    expected_hash = checkpoint_data[0]
                    if expected_hash and expected_hash != "" and expected_hash != _hash:
                        raise InvalidHeader(f"checkpoint mismatch at height {height}")
        
        try:
            cm = compute_commitment(header)
            cm_int = int.from_bytes(cm, byteorder='big')
            
            if not commitment_meets_target(cm, target):
                raise InvalidHeader("commitment does not meet target")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise InvalidHeader(f"commitment validation failed: {e}")

        # 4. Optionally verify bits field todo
        expected_bits = cls.target_to_bits(target)
        if header.get('bits') != expected_bits:
            # Optional warning todo
            pass

            
    
    def verify_chunk(self, index: int, data: bytes) -> None:
        num = len(data) // HEADER_SIZE
        start_height = index * CHUNK_SIZE
        
        # Get target for this chunk
        target = self.get_target(index-1)  # Target from PREVIOUS chunk
        
        try:
            # Special handling for first chunk after checkpoint
            if start_height % 2016 == 0 and start_height > 0:
                # We may not have previous header if syncing from checkpoint
                try:
                    prev_hash = self.get_hash(start_height - 1)
                except MissingHeader:
                    prev_hash = None
            else:
                # Normal case
                prev_hash = self.get_hash(start_height - 1)
            
            # Verify each header
            for i in range(num):
                height = start_height + i
                
                raw_header = data[i*HEADER_SIZE:(i+1)*HEADER_SIZE]
                header = deserialize_header(raw_header, height)
                
                # Skip prev_hash check for first header in checkpoint sync
                if i == 0 and prev_hash is None:
                    self.verify_header(header, None, target, None)
                else:
                    self.verify_header(header, prev_hash, target, None)
                
                # Check if header already exists (checkpoint case)
                existing_header = self.read_header(height)
                if existing_header:
                    existing_hash = hash_header(existing_header)
                    new_hash = hash_header(header)
                    if existing_hash == new_hash:
                        self.logger.debug(f"  [OK] Header already saved (checkpoint)")
                    else:
                        self.logger.info(f"  [ERROR] Header mismatch at height {height}!")
                        self.logger.info(f"    Existing: {existing_hash[:16]}...")
                        self.logger.info(f"    New:      {new_hash[:16]}...")
                        raise InvalidHeader(f"Header mismatch at height {height}")
                else:
                    # Save the header (pass the dict, not raw bytes!)
                    self.save_header(header)  # Pass header dict, not raw_header bytes!
                prev_hash = hash_header(header)
            
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
    
    @with_lock
    def path(self):
        d = util.get_headers_dir(self.config)
        if self.parent is None:
            filename = 'blockchain_headers'
        else:
            assert self.forkpoint > 0, self.forkpoint
            prev_hash = self._prev_hash.lstrip('0')
            first_hash = self._forkpoint_hash.lstrip('0')
            basename = f'fork2_{self.forkpoint}_{prev_hash}_{first_hash}'
            filename = os.path.join('forks', basename)
        return os.path.join(d, filename)

    @with_lock
    def save_chunk(self, index: int, chunk: bytes):
        assert index >= 0, index
        chunk_within_checkpoint_region = index < len(constants.net.CHECKPOINTS)
        
        # chunks in checkpoint region are the responsibility of the 'main chain'
        if chunk_within_checkpoint_region and self.parent is not None:
            main_chain = get_best_chain()
            main_chain.save_chunk(index, chunk)
            return

        delta_height = (index * CHUNK_SIZE - self.forkpoint)
        delta_bytes = delta_height * HEADER_SIZE
        
        if delta_bytes < 0:
            chunk = chunk[-delta_bytes:]
            delta_bytes = 0
        
        # MODIFIED: Never truncate when saving chunks
        # This prevents losing headers beyond checkpoints
        truncate = False
        
        self.write(chunk, delta_bytes, truncate)
        self.swap_with_parent()
    

    def swap_with_parent(self) -> None:
        with self.lock, blockchains_lock:
            # do the swap; possibly multiple ones
            cnt = 0
            while True:
                old_parent = self.parent
                if not self._swap_with_parent():
                    break
                # make sure we are making progress
                cnt += 1
                if cnt > len(blockchains):
                    raise Exception(f'swapping fork with parent too many times: {cnt}')
                # we might have become the parent of some of our former siblings
                for old_sibling in old_parent.get_direct_children():
                    if self.check_hash(old_sibling.forkpoint - 1, old_sibling._prev_hash):
                        old_sibling.parent = self

    def _swap_with_parent(self) -> bool:
        """Check if this chain became stronger than its parent, and swap
        the underlying files if so. The Blockchain instances will keep
        'containing' the same headers, but their ids change and so
        they will be stored in different files."""
        if self.parent is None:
            return False
        if self.parent.get_chainwork() >= self.get_chainwork():
            return False
        self.logger.info(f"swapping {self.forkpoint} {self.parent.forkpoint}")
        parent_branch_size = self.parent.height() - self.forkpoint + 1
        forkpoint = self.forkpoint  # type: Optional[int]
        parent = self.parent  # type: Optional[Blockchain]
        child_old_id = self.get_id()
        parent_old_id = parent.get_id()
        # swap files
        # child takes parent's name
        # parent's new name will be something new (not child's old name)
        self.assert_headers_file_available(self.path())
        child_old_name = self.path()
        with open(self.path(), 'rb') as f:
            my_data = f.read()
        self.assert_headers_file_available(parent.path())
        assert forkpoint > parent.forkpoint, (f"forkpoint of parent chain ({parent.forkpoint}) "
                                              f"should be at lower height than children's ({forkpoint})")
        with open(parent.path(), 'rb') as f:
            f.seek((forkpoint - parent.forkpoint)*HEADER_SIZE)
            parent_data = f.read(parent_branch_size*HEADER_SIZE)
        self.write(parent_data, 0)
        parent.write(my_data, (forkpoint - parent.forkpoint)*HEADER_SIZE)
        # swap parameters
        self.parent, parent.parent = parent.parent, self  # type: Optional[Blockchain], Optional[Blockchain]
        self.forkpoint, parent.forkpoint = parent.forkpoint, self.forkpoint
        self._forkpoint_hash, parent._forkpoint_hash = parent._forkpoint_hash, hash_raw_header(parent_data[:HEADER_SIZE])
        self._prev_hash, parent._prev_hash = parent._prev_hash, self._prev_hash
        # parent's new name
        os.replace(child_old_name, parent.path())
        self.update_size()
        parent.update_size()
        # update pointers
        blockchains.pop(child_old_id, None)
        blockchains.pop(parent_old_id, None)
        blockchains[self.get_id()] = self
        blockchains[parent.get_id()] = parent
        return True

    def get_id(self) -> str:
        return self._forkpoint_hash

    def assert_headers_file_available(self, path):
        if os.path.exists(path):
            return
        elif not os.path.exists(util.get_headers_dir(self.config)):
            raise FileNotFoundError('Electrum headers_dir does not exist. Was it deleted while running?')
        else:
            raise FileNotFoundError('Cannot find headers file but headers_dir is there. Should be at {}'.format(path))


    @with_lock
    def write(self, data: bytes, pos: int, truncate=True) -> None:
        """Write header data at position pos (header index, not bytes)."""
        # DEBUG: Verify expected data size
        # if len(data) % HEADER_SIZE == 0:
            # headers_in_data = len(data) // HEADER_SIZE
        
        # Convert header index to byte position
        byte_pos = pos  # Just rename for clarity
        needed_size = byte_pos + len(data)  # This is in BYTES, not headers
        
        filepath = self.path()
        
        # Make sure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'rb+') as f:
            # Check current file size
            f.seek(0, 2)  # Seek to end
            current_size = f.tell()
            
            
            if current_size < needed_size:
                f.truncate(needed_size)
            elif truncate and current_size > needed_size:
                # Don't truncate to preserve data
                pass
            
            # Write at the correct byte position
            f.seek(byte_pos)
            bytes_written = f.write(data)
        
    @with_lock
    def save_header(self, header: dict) -> None:
        """Save a block header."""
        if header is None:
            return
        
        header_hash = hash_header(header)
        height = header['block_height']
        
        with self.lock:
            
            # Calculate where this header should go in our chain
            if height < self.forkpoint:
                return
            
            pos = height - self.forkpoint
            
            if pos < self._size:
                existing_header = self.read_header(height)
                if existing_header:
                    existing_hash = hash_header(existing_header)
                    if existing_hash == header_hash:
                        return
            
            data = serialize_header(header)  # NO bfh() here!
            if len(data) != HEADER_SIZE:
                return
                
            byte_pos = pos * HEADER_SIZE
            self.write(data, byte_pos, truncate=False)
            

            if pos >= self._size:
                self._size = pos + 1
            
            if pos == self._size - 1:  # This is the new tip
                self._prev_hash = header_hash

    @with_lock
    def read_header(self, height: int) -> Optional[dict]:
        if height < 0:
            return
        if height < self.forkpoint:
            return self.parent.read_header(height)
        if height > self.height():
            return
        delta = height - self.forkpoint
        name = self.path()
        self.assert_headers_file_available(name)
        with open(name, 'rb') as f:
            f.seek(delta * HEADER_SIZE)
            h = f.read(HEADER_SIZE)
            if len(h) < HEADER_SIZE:
                raise Exception('Expected to read a full header. This was only {} bytes'.format(len(h)))
        if h == bytes([0])*HEADER_SIZE:
            return None
        return deserialize_header(h, height)

    def header_at_tip(self) -> Optional[dict]:
        """Return latest header."""
        height = self.height()
        return self.read_header(height)

    def is_tip_stale(self) -> bool:
        STALE_DELAY = 8 * 60 * 60  # in seconds
        header = self.header_at_tip()
        if not header:
            return True
        # note: We check the timestamp only in the latest header.
        #       The Bitcoin consensus has a lot of leeway here:
        #       - needs to be greater than the median of the timestamps of the past 11 blocks, and
        #       - up to at most 2 hours into the future compared to local clock
        #       so there is ~2 hours of leeway in either direction
        if header['timestamp'] + STALE_DELAY < time.time():
            return True
        return False

    def get_hash(self, height: int) -> str:
        def is_height_checkpoint():
            within_cp_range = height <= constants.net.max_checkpoint()
            at_chunk_boundary = (height) % CHUNK_SIZE == 0
            return within_cp_range and at_chunk_boundary

        if height == -1:
            return '0000000000000000000000000000000000000000000000000000000000000000'
        elif height == 0:
            return constants.net.GENESIS
        elif is_height_checkpoint():
            index = height // CHUNK_SIZE
            h, t = self.checkpoints[index]
            return h
        else:
            header = self.read_header(height)
            if header is None:
                raise MissingHeader(height)
            return hash_header(header)

    def get_asert_anchor_header(self) -> dict:
        """Return the static ASERT anchor header from constants."""
        return constants.net.ASERT_ANCHOR_HEADER
    
    def calculate_asert_target(self, prev_header: dict, anchor_header: dict) -> int:
        try:
            anchor_height = anchor_header['block_height']
            anchor_bits = anchor_header['bits']
            anchor_time = anchor_header['timestamp']
            
            prev_height = prev_header['block_height']
            prev_time = prev_header['timestamp']
            
            height_diff = prev_height - anchor_height
            time_diff = prev_time - anchor_time
            
            expected_time_diff = IDEAL_BLOCK_TIME * height_diff
            
            numerator = (time_diff - expected_time_diff) * ASERT_PRECISION
            exponent = numerator // ASERT_HALFLIFE
            
            target = self.bits_to_target(anchor_bits)
            
            if exponent >= 0:
                target = (target << exponent) // ASERT_PRECISION
            else:
                target = (target >> (-exponent)) // ASERT_PRECISION
            
            if target > POW_LIMIT:
                target = POW_LIMIT
            
            if target == 0:
                target = 1
            
            return self.target_to_bits(target)
            
        except Exception as e:
            raise InvalidHeader(f"ASERT calculation failed: {e}")
    
    
    #@classmethod
    def verify_header(self, header: dict, prev_hash: str, target: int, expected_header_hash: str = None) -> None:
        """Enhanced verification with ASERT support."""
        height = header.get('block_height', 0)
        _hash = hash_header(header)
        if expected_header_hash and expected_header_hash != _hash:
            raise InvalidHeader("block hash mismatch")
        
        if prev_hash is not None and prev_hash != header.get('prev_block_hash'):
            raise InvalidHeader("prev hash mismatch")
        
        is_after_checkpoint = (height % 2016 == 0)
        
        if height >= constants.net.ASERT_ACTIVATION_HEIGHT:
            if height == 0:
                raise InvalidHeader("Genesis block cannot use ASERT")
            
            prev_header = self.read_header(height - 1)
            
            if not prev_header and is_after_checkpoint:
                expected_target = target
                cm = compute_commitment(header)
                if not commitment_meets_target(cm, expected_target):
                    actual_target = self.bits_to_target(header['bits'])
                    ratio = expected_target / actual_target if actual_target != 0 else float('inf')
                    raise InvalidHeader(
                        f"commitment does not meet checkpoint target at height {height}\n"
                        f"  Expected target: 0x{expected_target:064x}\n"
                        f"  Actual target:   0x{actual_target:064x}\n"
                        f"  Header bits:     0x{header['bits']:08x}"
                    )
                return

            elif not prev_header:
                raise InvalidHeader(f"Cannot get previous block {height-1} for ASERT")
            
            
            anchor_params = constants.net.get_asert_anchor_params()
            expected_bits = self.calculate_next_asert_target(prev_header, anchor_params)
            expected_target = self.bits_to_target(expected_bits)
            actual_target = self.bits_to_target(header['bits'])
            
            
            # Verify with tolerance
            if not self.verify_asert_target(expected_target, actual_target, height):
                ratio = expected_target / actual_target if actual_target != 0 else float('inf')
                raise InvalidHeader(
                    f"ASERT target mismatch at height {height}\n"
                    f"  Expected: 0x{expected_target:064x} (bits: 0x{expected_bits:08x})\n"
                    f"  Actual:   0x{actual_target:064x} (bits: 0x{header['bits']:08x})\n"
                    f"  Ratio: {ratio:.6f}"
                )
            else:
                ratio = expected_target / actual_target if actual_target != 0 else float('inf')
                return  # ASERT verification passed
            
        else:
            expected_target = target
        
        cm = compute_commitment(header)
        if not commitment_meets_target(cm, expected_target):
            actual_target = self.bits_to_target(header['bits'])
            ratio = expected_target / actual_target if actual_target != 0 else float('inf')
            raise InvalidHeader(
                f"commitment does not meet target at height {height}\n"
                f"  Expected target: 0x{expected_target:064x}\n"
                f"  Actual target:   0x{actual_target:064x}\n"
                f"  Header bits:     0x{header['bits']:08x}"
            )

    def calculate_next_asert_target(self, prev_header: dict, anchor_params: dict = None) -> int:
        if anchor_params is None:
            anchor_params = constants.net.get_asert_anchor_params()
        
        HALFLIFE = constants.net.ASERT_HALFLIFE
        IDEAL_BLOCK_TIME = constants.net.IDEAL_BLOCK_TIME
        POW_LIMIT = constants.net.SCASH_POW_LIMIT
        PRECISION = 65536  # 2^16 for fixed-point
        
        anchor_height = anchor_params['height']
        anchor_bits = anchor_params['bits']
        anchor_parent_time = anchor_params['parent_time']
        
        prev_height = prev_header['block_height']
        prev_time = prev_header['timestamp']
        
        nHeightDiff = prev_height - anchor_height
        nTimeDiff = prev_time - anchor_parent_time
        
        
        expected_time = IDEAL_BLOCK_TIME * (nHeightDiff + 1)
        time_error = nTimeDiff - expected_time
        exponent_numer = time_error * PRECISION
        exponent = exponent_numer // HALFLIFE  # Integer division
        
        ref_target = self.bits_to_target(anchor_bits)
        
        shifts = exponent >> 16      # Integer part
        frac = exponent & 0xFFFF     # Fractional part (0-65535)
        frac_64 = int(frac)
        
        term1 = 195766423245049 * frac_64
        term2 = 971821376 * frac_64 * frac_64
        term3 = 5127 * frac_64 * frac_64 * frac_64
        
        numerator = term1 + term2 + term3 + (1 << 47)
        factor = 65536 + (numerator >> 48)
        
        next_target = ref_target * factor
        
        shifts -= 16
        
        
        if shifts < 0:
            next_target >>= -shifts
        else:
            shifted = next_target << shifts
            if (shifted >> shifts) != next_target:
                next_target = POW_LIMIT
            else:
                next_target = shifted
        
        if next_target > POW_LIMIT:
            next_target = POW_LIMIT
        
        if next_target == 0:
            next_target = 1
        
        result = self.target_to_bits(next_target)
        
        return result

    def verify_asert_target(self, calculated_target: int, actual_target: int, height: int) -> bool:
        if actual_target == 0:
            return False
        
        ratio = calculated_target / actual_target
        tolerance = constants.net.get_asert_tolerance()
        
        min_ratio = tolerance['min_ratio']
        max_ratio = tolerance['max_ratio']
        
        is_within_tolerance = min_ratio <= ratio <= max_ratio
        
        status = "PASS" if is_within_tolerance else "FAIL"
        
        return is_within_tolerance
        
        
    def get_target(self, index: int) -> int:
        if constants.net.TESTNET:
            return 0
        
        chunk_start_height = index * CHUNK_SIZE
        chunk_end_height = (index + 1) * CHUNK_SIZE - 1
        
        if chunk_end_height < constants.net.ASERT_ACTIVATION_HEIGHT:
            return self._get_target(index)
        
        
        try:
            last_header = self.read_header(chunk_end_height)
            if last_header:
                if last_header['block_height'] >= constants.net.ASERT_ACTIVATION_HEIGHT:
                    prev_header = self.read_header(chunk_end_height - 1)
                    if prev_header:
                        anchor_params = constants.net.get_asert_anchor_params()
                        expected_bits = self.calculate_next_asert_target(prev_header, anchor_params)
                        expected_target = self.bits_to_target(expected_bits)
                        
                        actual_target = self.bits_to_target(last_header['bits'])
                        ratio = expected_target / actual_target if actual_target != 0 else float('inf')
                        
                        if abs(ratio - 1) <= 0.003:  # 0.3% tolerance for chunk verification
                            return expected_target
        except Exception as e:
            import traceback
            traceback.print_exc()
        
        return self._get_target(index)
        
    def _get_target(self, index: int) -> int:
        
        if constants.net.TESTNET:
            return 0
        
        if index < 0:
            genesis_bits = getattr(constants.net, 'GENESIS_BITS', 0x1e0fffff)
            target = self.bits_to_target(genesis_bits)
            return target
        
        if index < len(self.checkpoints):
            checkpoint_data = self.checkpoints[index]
            if isinstance(checkpoint_data, (list, tuple)) and len(checkpoint_data) >= 2:
                _, bits = checkpoint_data[:2]
                target = self.bits_to_target(bits)
                return target
        try:
            # Read the last header in the previous chunk
            last_header_height = (index + 1) * CHUNK_SIZE - 1
            
            header = self.read_header(last_header_height)
            if header:
                bits = header['bits']
                target = self.bits_to_target(bits)
                return target
        except Exception as e:
            self.logger.info(f"  Could not read header: {e}")
        
        return MAX_TARGET

    @classmethod
    def bits_to_target(cls, bits: int) -> int:
        # arith_uint256::SetCompact in Bitcoin Core
        if not (0 <= bits < (1 << 32)):
            raise InvalidHeader(f"bits should be uint32. got {bits!r}")
        bitsN = (bits >> 24) & 0xff
        bitsBase = bits & 0x7fffff
        if bitsN <= 3:
            target = bitsBase >> (8 * (3-bitsN))
        else:
            target = bitsBase << (8 * (bitsN-3))
        if target != 0 and bits & 0x800000 != 0:
            # Bit number 24 (0x800000) represents the sign of N
            raise InvalidHeader("target cannot be negative")
        if (target != 0 and
                (bitsN > 34 or
                 (bitsN > 33 and bitsBase > 0xff) or
                 (bitsN > 32 and bitsBase > 0xffff))):
            raise InvalidHeader("target has overflown")
        return target

    @classmethod
    def target_to_bits(cls, target: int) -> int:
        # arith_uint256::GetCompact in Bitcoin Core
        # see https://github.com/bitcoin/bitcoin/blob/7fcf53f7b4524572d1d0c9a5fdc388e87eb02416/src/arith_uint256.cpp#L223
        c = target.to_bytes(length=32, byteorder='big')
        bitsN = len(c)
        while bitsN > 0 and c[0] == 0:
            c = c[1:]
            bitsN -= 1
            if len(c) < 3:
                c += b'\x00'
        bitsBase = int.from_bytes(c[:3], byteorder='big')
        if bitsBase >= 0x800000:
            bitsN += 1
            bitsBase >>= 8
        return bitsN << 24 | bitsBase

    def chainwork_of_header_at_height(self, height: int) -> int:
        """work done by single header at given height"""
        chunk_idx = height // CHUNK_SIZE - 1
        target = self.get_target(chunk_idx)
        work = ((2 ** 256 - target - 1) // (target + 1)) + 1
        return work

    @with_lock
    def get_chainwork(self, height=None) -> int:
        if height is None:
            height = max(0, self.height())
        if constants.net.TESTNET:
            return height
        last_retarget = height // CHUNK_SIZE * CHUNK_SIZE - 1
        cached_height = last_retarget
        while _CHAINWORK_CACHE.get(self.get_hash(cached_height)) is None:
            if cached_height <= -1:
                break
            cached_height -= CHUNK_SIZE
        assert cached_height >= -1, cached_height
        running_total = _CHAINWORK_CACHE[self.get_hash(cached_height)]
        while cached_height < last_retarget:
            cached_height += CHUNK_SIZE
            work_in_single_header = self.chainwork_of_header_at_height(cached_height)
            work_in_chunk = CHUNK_SIZE * work_in_single_header
            running_total += work_in_chunk
            _CHAINWORK_CACHE[self.get_hash(cached_height)] = running_total
        cached_height += CHUNK_SIZE
        work_in_single_header = self.chainwork_of_header_at_height(cached_height)
        work_in_last_partial_chunk = (height % CHUNK_SIZE + 1) * work_in_single_header
        return running_total + work_in_last_partial_chunk


    def can_connect(self, header: dict, *, check_height: bool = True) -> bool:
        if header is None:
            return False
        
        height = header['block_height']
        header_hash = hash_header(header)
        
        
        # 1. Check for genesis block
        if height == 0:
            if header_hash != constants.net.GENESIS:
                return False
            return True
        
        # 2. CRITICAL: Always check checkpoints at checkpoint heights
        if height % 2016 == 0:
            checkpoint_index = height // 2016
            
            if checkpoint_index < len(self.checkpoints):
                checkpoint_data = self.checkpoints[checkpoint_index]
                
                if isinstance(checkpoint_data, (list, tuple)) and len(checkpoint_data) >= 1:
                    expected_hash = checkpoint_data[0]
                    
                    if expected_hash and expected_hash != "":
                        
                        if expected_hash != header_hash:
                            return False
                        else:
                            return True
        
        # 3. For non-checkpoint headers, check continuity with previous block
        if height > 0:
            expected_prev_hash = None
            
            if height == 1:
                # Block 1 connects to genesis
                expected_prev_hash = constants.net.GENESIS
            else:
                # Get previous block's hash from our chain
                try:
                    current_height = self.height()
                    if current_height is not None and current_height >= height - 1:
                        expected_prev_hash = self.get_hash(height - 1)
                    else:
                        if height % 2016 == 1:
                            return True
                        else:
                            return False
                except Exception as e:
                    return False
            
            if expected_prev_hash:
                actual_prev_hash = header.get('prev_block_hash')
                
                if actual_prev_hash != expected_prev_hash:
                    return False
        
        return True

    def connect_chunk(self, idx: int, data: bytes) -> bool:
        assert idx >= 0, idx
        try:
            self.verify_chunk(idx, data)
            self.save_chunk(idx, data)
            return True
        except BaseException as e:
            return False

    def get_checkpoints(self):
        # for each chunk, store the hash of the last block and the target after the chunk
        cp = []
        n = self.height() // CHUNK_SIZE
        for index in range(n):
            h = self.get_hash((index+1) * CHUNK_SIZE -1)
            target = self.get_target(index)
            cp.append((h, target))
        return cp


def check_header(header: dict) -> Optional[Blockchain]:
    """Returns any Blockchain that contains header, or None."""
    if type(header) is not dict:
        return None
    with blockchains_lock: chains = list(blockchains.values())
    for b in chains:
        if b.check_header(header):
            return b
    return None


def can_connect(header: dict) -> Optional[Blockchain]:
    """Returns the Blockchain that has a tip that directly links up
    with header, or None.
    """
    with blockchains_lock: chains = list(blockchains.values())
    for b in chains:
        if b.can_connect(header):
            return b
    return None


def get_chains_that_contain_header(height: int, header_hash: str) -> Sequence[Blockchain]:
    """Returns a list of Blockchains that contain header, best chain first."""
    with blockchains_lock: chains = list(blockchains.values())
    chains = [chain for chain in chains
              if chain.check_hash(height=height, header_hash=header_hash)]
    chains = sorted(chains, key=lambda x: x.get_chainwork(), reverse=True)
    return chains
