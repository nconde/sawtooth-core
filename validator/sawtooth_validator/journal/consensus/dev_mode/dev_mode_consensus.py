# Copyright 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import time
import random
import hashlib

from sawtooth_validator.journal.consensus.consensus\
    import BlockPublisherInterface
from sawtooth_validator.journal.consensus.consensus\
    import BlockVerifierInterface
from sawtooth_validator.journal.consensus.consensus\
    import ForkResolverInterface

from sawtooth_validator.state.config_view import ConfigView


class BlockPublisher(BlockPublisherInterface):
    """Consensus objects provide the following services to the Journal:
    1) Build candidate blocks ( this temporary until the block types are
    combined into a single block type)
    2) Check if it is time to claim the current candidate blocks.
    3) Provide the data a signatures required for a block to be validated by
    other consensus algorithms

    """
    def __init__(self, block_cache, state_view):
        super().__init__(block_cache, state_view)

        self._block_cache = block_cache
        self._state_view = state_view

        self._start_time = 0
        self._wait_time = 0
        config_view = ConfigView(self._state_view)
        self._min_wait_time = config_view.get_setting(
            "sawtooth.consensus.MinWaitTime", 0, int)
        self._max_wait_time = config_view.get_setting(
            "sawtooth.consensus.MaxWaitTime", 0, int)
        self._num_batches = config_view.get_setting(
            "sawtooth.consensus.num_batches", 0, int)
        self._valid_block_publishers = config_view.get_setting(
            "sawtooth.consensus.ValidBlockPublishers", 0, int)

    def initialize_block(self, block):
        """Do initialization necessary for the consensus to claim a block,
        this may include initiating voting activates, starting proof of work
        hash generation, or create a PoET wait timer.

        Args:
            journal (Journal): the current journal object
            block (TransactionBlock): the block to initialize.
        Returns:
            none
        """
        block.block_header.consensus = b"Devmode"
        self._start_time = time.time()
        self._wait_time = random.uniform(
            self._min_wait_time, self._max_wait_time)

    def check_publish_block(self, block):
        """Check if a candidate block is ready to be claimed.

        Args:
            journal (Journal): the current journal object
            block: the block to be checked if it should be claimed
            now: the current time
        Returns:
            Boolean: True if the candidate block should be claimed.
        """
        if self._valid_block_publishers\
                and block.block_header.signer_pubkey not \
                        in self._valid_block_publishers:
            return False
        elif self._min_wait_time == 0:
            return True
        elif self._min_wait_time > 0 and self._max_wait_time <= 0:
            if self._start_time + self._min_wait_time <= time.time():
                return True
        elif self._min_wait_time > 0 \
                and self._max_wait_time > self._min_wait_time:
            if self._start_time + self._wait_time <= time.time():
                return True
        else:
            return False

    def finalize_block(self, block):
        """Finalize a block to be claimed. Provide any signatures and
        data updates that need to be applied to the block before it is
        signed and broadcast to the network.

        Args:
            journal (Journal): the current journal object
            block: The candidate block that
        Returns:
            None
        """
        pass


class TimedBlockPublisher(BlockPublisherInterface):
    """Provides a timed block claim mechanism based on
    the number of seconds since that validator last claimed
    a block"""

    def __init__(self, wait_time=20):
        super().__init__(block_cache=None, state_view=None)

        self._wait_time = wait_time
        self._last_block_time = time.time()

    def initialize_block(self, block):
        block.block_header.consensus = b"TimedDevmode"

    def check_publish_block(self, block):
        if time.time() - self._last_block_time > self._wait_time:
            self._last_block_time = time.time()
            return True
        return False

    def finalize_block(self, block):
        pass


class BlockVerifier(BlockVerifierInterface):
    def __init__(self, block_cache, state_view):
        super().__init__(block_cache, state_view)

        self._block_cache = block_cache
        self._state_view = state_view

    def verify_block(self, block_state):
        return True

    def compute_block_weight(self, block_state):
        # longest chain wins
        return block_state.block_num


class ForkResolver(ForkResolverInterface):
    # Provides the fork resolution interface for the BlockValidator to use
    # when deciding between 2 forks.
    def __init__(self, block_cache):
        super().__init__(block_cache)

        self._block_cache = block_cache

    def compare_forks(self, cur_fork_head, new_fork_head):
        """

        Args:
            cur_fork_head: The current head of the block chain.
            new_fork_head: The head of the fork that is being evaluated.
        Returns:
            bool: True if the new chain should replace the current chain.
            False if the new chain should be discarded.
        """
        # Add round robin style fork resolution where the signer_pubkey
        # is hashed with the header_signature and the lowest result value
        # is the winning block.

        cur_fork_hash = hash_signer_pubkey(
            self.cur_fork_head.block_header.signer_pubkey,
            self.cur_fork_head.block_header.header_signature)
        new_fork_hash = hash_signer_pubkey(
            self.new_fork_head.block_header.signer_pubkey,
            self.new_fork_head.block_header.header_signature)

        return new_fork_hash > cur_fork_hash


def hash_signer_pubkey(signer_pubkey, header_signature):
    m = hashlib.md5()
    m.update(signer_pubkey)
    m.update(header_signature)
    digest = m.hexdigest()
    number = int(digest, 16)
    return number
