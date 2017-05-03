# Copyright 2017 Intel Corporation
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
import shutil
import tempfile

from unittest import TestCase
from unittest import mock

import sawtooth_signing as signing

from sawtooth_poet.poet_consensus.poet_block_publisher import PoetBlockPublisher

from sawtooth_poet_common.protobuf.validator_registry_pb2 \
    import ValidatorInfo
from sawtooth_poet_common.protobuf.validator_registry_pb2 \
    import SignUpInfo


@mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.BlockWrapper')
@mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.PoetConfigView')
class TestPoetBlockPublisher(TestCase):

    def setUp(self):
        self._temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._temp_dir)

    @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.'
                'SignupInfo')
    @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.'
                'PoetKeyStateStore')
    @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.'
                'ConsensusStateStore')
    @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.factory')
    @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.'
                'ConsensusState')
    @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.'
                'ValidatorRegistryView')
    @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.utils')
    def test_no_public_key(
            self,
            mock_utils,
            mock_validator_registry_view,
            mock_consensus_state,
            mock_poet_enclave_factory,
            mock_consensus_state_store,
            mock_poet_key_state_store,
            mock_signup_info,
            mock_poet_config_view,
            mock_block_wrapper):
        """ Test verifies that PoET Block Publisher fails if
        a validator's poet_public_key is not correct
        """

        # create a mock_validator_registry_view with no keys for the validator
        mock_validator_registry_view.return_value.get_validator_info. \
            return_value = None

        # create a mock_wait_certificate that does nothing in check_valid
        mock_wait_certificate = mock.Mock()
        mock_wait_certificate.check_valid.return_value = None

        mock_utils.deserialize_wait_certificate.return_value = \
            mock_wait_certificate

        # create a mock_consensus_state that returns a mock with
        # the following settings:
        mock_state = mock.Mock()
        mock_state.validator_signup_was_committed_too_late.return_value = False
        mock_state.validator_has_claimed_block_limit.return_value = False
        mock_state.validator_is_claiming_too_early.return_value = False
        mock_state.validator_is_claiming_too_frequently.return_value = False

        mock_consensus_state.consensus_state_for_block_id.return_value = \
            mock_state

        mock_consensus_state_store.return_value.__getitem__.return_value = \
            mock_consensus_state

        # create mock_signup_info
        mock_signup_info.create_signup_info.return_value = \
            mock.Mock(
                poet_public_key='poet public key',
                proof_data='proof data',
                anti_sybil_id='anti-sybil ID',
                sealed_signup_data='sealed signup data')

        mock_poet_enclave_module = mock.Mock()
        # mock_poet_enclave_module = \
        #     mock_poet_enclave_factory.return_value.get_poet_enclave_module.return_value

        # create mock_batch_publisher
        mock_batch_publisher = mock.Mock(
            identity_signing_key = signing.generate_privkey())

        mock_block_cache = mock.MagicMock()
        mock_state_view_factory = mock.Mock()

        # create mock_block_header with the following fields
        mock_block = mock.Mock(identifier='0123456789abcdefedcba9876543210')
        mock_block.header.signer_pubkey = '90834587139405781349807435098745'
        mock_block.header.previous_block_id = '2'
        mock_block.header.block_num = 1
        mock_block.header.state_root_hash = '6'
        mock_block.header.batch_ids = '4'
        # mock_block_header = mock_block.header

        # check test
        with mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.'
                        'LOGGER') as mock_logger:
            block_publisher = \
                PoetBlockPublisher(
                    block_cache=mock_block_cache,
                    state_view_factory=mock_state_view_factory,
                    batch_publisher=mock_batch_publisher,
                    data_dir=self._temp_dir,
                    validator_id='validator_deadbeef')

            self.assertFalse(
                block_publisher.initialize_block(
                    block_header= mock_block.header))

                # block_publisher._register_signup_information(
                #     block_header=mock_block.header,
                #     poet_enclave_module=mock_poet_enclave_module))


            # Could be a hack, but verify that the appropriate log message is
            # generated - so we at least have some faith that the failure was
            # because of what we are testing and not something else.  I know
            # that this is fragile if the log message is changed, so would
            # accept any suggestions on a better way to verify that the
            # function fails for the reason we expect.

            (message, *_), _ = mock_logger.debug.call_args
            self.assertTrue('No public key found, so going '
                            'to register new signup information' in message)





#
#
# import shutil
# import tempfile
#
# from unittest import TestCase
# from unittest import mock
#
# import sawtooth_signing as signing
#
# from sawtooth_poet.poet_consensus.poet_block_publisher import PoetBlockPublisher
#
# from sawtooth_poet_common.protobuf.validator_registry_pb2 \
#     import ValidatorInfo
# from sawtooth_poet_common.protobuf.validator_registry_pb2 \
#     import SignUpInfo
#
#
# @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.BlockWrapper')
# @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.PoetConfigView')
# class TestPoetBlockPublisher(TestCase):
#
#     def setUp(self):
#         self._temp_dir = tempfile.mkdtemp()
#
#     def tearDown(self):
#         shutil.rmtree(self._temp_dir)
#
#
#     @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.'
#                 'ConsensusStateStore')
#     @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.factory')
#     @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.'
#                 'ConsensusState')
#     @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.'
#                 'ValidatorRegistryView')
#     @mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.utils')
#     def test_no_public_key(
#             self,
#             mock_utils,
#             mock_validator_registry_view,
#             mock_consensus_state,
#             mock_poet_enclave_factory,
#             mock_poet_config_view,
#             mock_block_wrapper,
#             mock_consensus_state_store):
#         """ Test verifies that PoET Block Publisher fails if
#         a validator's poet_public_key is not correct
#         """
#
#         # create a mock_validator_registry_view
#         mock_validator_registry_view.return_value.get_validator_info. \
#             return_value = \
#             ValidatorInfo(
#                 name='validator_001',
#                 id='validator_deadbeef',
#                 signup_info=SignUpInfo(
#                     poet_public_key='00112233445566778899aabbccddeeff'))
#
#         # create a mock_wait_certificate that does nothing in check_valid
#         mock_wait_certificate = mock.Mock()
#         mock_wait_certificate.check_valid.return_value = None
#
#         mock_utils.deserialize_wait_certificate.return_value = \
#             mock_wait_certificate
#
#         # create a mock_consensus_state that returns a mock with
#         # the following settings:
#         mock_state = mock.Mock()
#         mock_state.validator_signup_was_committed_too_late.return_value = False
#         mock_state.validator_has_claimed_block_limit.return_value = False
#         mock_state.validator_is_claiming_too_early.return_value = False
#         mock_state.validator_is_claiming_too_frequently.return_value = False
#
#         mock_consensus_state.consensus_state_for_block_id.return_value = \
#             mock_state
#
#         mock_state_store = mock.MagicMock()
#         mock_consensus_state_store.return_value.__getitem__ = mock_state_store
#
#         mock_poet_enclave_module = mock.Mock
#
#         # mock_poet_enclave_module = \
#         #     mock_poet_enclave_factory.return_value.get_poet_enclave_module.return_value
#
#         mock_batch_publisher = mock.Mock()
#         mock_block_cache = mock.MagicMock()
#         mock_state_view_factory = mock.Mock()
#
#         # create mock_block_header with the following fields
#         mock_block = mock.Mock(identifier='0123456789abcdefedcba9876543210')
#         mock_block.header.signer_pubkey = '90834587139405781349807435098745'
#         mock_block.header.previous_block_id = '2'
#         mock_block.header.block_num = 1
#         mock_block.header.state_root_hash = '6'
#         mock_block.header.batch_ids = '4'
#         # mock_block_header = mock_block.header
#
#         # check test
#         with mock.patch('sawtooth_poet.poet_consensus.poet_block_publisher.'
#                         'LOGGER') as mock_logger:
#             block_publisher = \
#                 PoetBlockPublisher(
#                     block_cache=mock_block_cache,
#                     state_view_factory=mock_state_view_factory,
#                     batch_publisher=mock_batch_publisher,
#                     data_dir=self._temp_dir,
#                     validator_id='validator_deadbeef')
#
#             self.assertFalse(
#                 block_publisher.initialize_block(
#                     block_header= mock_block.header))
#
#                 # block_publisher._register_signup_information(
#                 #     block_header=mock_block.header,
#                 #     poet_enclave_module=mock_poet_enclave_module))
#
#
#             # Could be a hack, but verify that the appropriate log message is
#             # generated - so we at least have some faith that the failure was
#             # because of what we are testing and not something else.  I know
#             # that this is fragile if the log message is changed, so would
#             # accept any suggestions on a better way to verify that the
#             # function fails for the reason we expect.
#
#             (message, *_), _ = mock_logger.debug.call_args
#             self.assertTrue('No public key found, so going '
#                             'to register new signup information' in message)
