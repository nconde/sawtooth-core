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

import hashlib

from sawtooth_sdk.processor.state import StateEntry
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader

LOGGER = logging.getLogger(__name__)


class BattleshipHandler(object):
    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return 'battleship'

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def encodings(self):
        return ['csv-utf8']

    @property
    def namespaces(self):
        return [self._namespace_prefix]


    def apply(self, transaction, state_store):

        # 1. Deserialize the transaction and verify it is valid
        header = TransactionHeader()
        header.ParseFromString(transaction.header)

        # The transaction signer is the player
        player = header.signer_pubkey

        try:
            # The payload is csv utf-8 encoded string
            name, action, space = transaction.payload.decode().split(",")
        except:
            raise InvalidTransaction("Invalid payload serialization")

        if name == "":
            raise InvalidTransaction("Name is required")

        if action == "":
            raise InvalidTransaction("Action is required")

        elif action == "fire":
            try:
                space = int(space)
            except:
                raise InvalidTransaction(
                    "Space could not be converted as an integer."
                )

            # if space < 1 or space > 9:
            #     raise InvalidTransaction("Invalid space {}".format(space))

        if action not in ("fire", "join", "create"):
            raise InvalidTransaction("Invalid Action : '{}'".format(action))


        # 2. Retrieve the game data from state storage

        # Use the namespace prefix + the has of the game name to create the
        # storage address
        game_address = self._namespace_prefix \
                       + hashlib.sha512(name.encode("utf-8")).hexdigest()

        # Get data from address
        state_entries = state_store.get([game_address])

        # state_store.get() returns a list. If no data has been stored yet
        # at the given address, it will be empty.
        if len(state_entries) != 0:
            try:
                board, state, player1, player2, stored_name = \
                    state_entries[0].data.decode().split(",")
            except:
                raise InternalError("Failed to deserialize game data.")

            # NOTE: Since the game data is stored in a Merkle tree, there is a
            # small chance of collision. A more correct usage would be to store
            # a dictionary of games so that multiple games could be store at
            # the same location. See the python intkey handler for an example
            # of this.
            if stored_name != name:
                raise InternalError("Hash collision")

        else:
            board = state = player1 = player2 = None


        # 3. Validate the game data

        if action == "create" and board is not None:
            raise InvalidTransaction("Invalid Action: Game already exists.")
            # state_store[self._name] = {'State': 'NEW', 'Ships': self._ships}
        elif action == 'join':
            if board is None:
                raise InvalidTransaction(
                    "Invalid Action: Join requires an existing game."
                )
            else:
                if state in ("P1-WIN", "P2-WIN", "TIE"):
                    raise InvalidTransaction(
                        "Invalid Action: Game has ended."
                    )
                elif state not in ("P1-NEXT", "P2-NEXT"):
                    raise InternalError(
                        "Game has reached an invalid state: {}".format(state))

        elif action == 'fire':
            if board is None:
                raise InvalidTransaction(
                    "Invalid Action: Fire requires an existing game."
                )
            else:
                if state in ("P1-WIN", "P2-WIN", "TIE"):
                    raise InvalidTransaction(
                        "Invalid Action: Game has ended."
                    )
                elif state not in ("P1-NEXT", "P2-NEXT"):
                    raise InternalError(
                        "Game has reached an invalid state: {}".format(state))

        # 4. Apply the transaction
        if action == "create":
            board = "---------"
            state = "P1-NEXT"
            player1 = ""
            player2 = ""

            # game = state_store[self._name].copy()
        elif action == "join":
            # Assign players if new game
            if player1 == "":
                player1 = player

            elif player2 == "":
                player2 = player

            # Verify player identity and take space
            lboard = list(board)

            size = len(board)
            target_board = [['?'] * size for _ in range(size)]


            if state == "P1-NEXT" and player == player1:
                lboard[space - 1] = "X"
                state = "P2-NEXT"
                target_board = "TargetBoard2"


            elif state == "P2-NEXT" and player == player2:
                lboard[space - 1] = "O"
                state = "P1-NEXT"
                target_board = "TargetBoard1"

            else:
                raise InvalidTransaction(
                    "Not this player's turn: {}".format(player[:6])
                )
            board = "".join(lboard)




# def _is_win(board, letter):


# def _game_data_to_str(board, state, player1, player2, name):



# def _display(msg):

