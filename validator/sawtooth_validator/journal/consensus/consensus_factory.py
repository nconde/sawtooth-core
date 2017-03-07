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
import importlib

from sawtooth_validator.exceptions import UnknownConsensusModuleError
from sawtooth_validator.state.config_view import ConfigView


class ConsensusFactory(object):
    """ConsensusFactory returns consensus modules by short name.
    """

    @staticmethod
    def get_consensus_module(module_name):
        """Returns a consensus module by name.

        Args:
            module_name (str): The name of the module to load.

        Returns:
            module: The consensus module.

        Raises:
            UnknownConsensusModuleError: Raised if the given module_name does
                not correspond to a consensus implementation.
        """
        module_package = module_name
        if module_name == 'devmode':
            module_package = \
                'sawtooth_validator.journal.consensus.dev_mode.'\
                'dev_mode_consensus'
        elif module_name == 'poet':
            module_package = \
                'sawtooth_validator.journal.consensus.poet1.poet_consensus'

        try:
            return importlib.import_module(module_package)
        except ImportError:
            raise UnknownConsensusModuleError(
                'Consensus module "{}" does not exist.'.format(module_name))

    @staticmethod
    def get_configured_consensus_module(state_view):
        """Returns the consensus_module based on the consensus module set by the
        "sawtooth_config" transaction family.

        Args:
            state_view_factory (:obj:`StateViewFactory`): The state view
                factory for reading the configuration
            state_hash (str): The current state root hash for reading settings.

        Raises:
            UnknownConsensusModuleError: Thrown when an invalid consensus
                module has been configured.
        """
        config_view = ConfigView(state_view)

        consensus_module_name = config_view.get_setting(
            'sawtooth.consensus.algorithm', default_value='devmode')
        return ConsensusFactory.get_consensus_module(
            consensus_module_name)
