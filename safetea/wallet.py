from typing import List, Optional, Dict, Any
from eth_typing import ChecksumAddress
from web3 import Web3, Account
from web3.contract.contract import ContractFunction

from .utils import wallet_abi
from .exceptions import NotOwnerError

from .transaction_manager import TransactionManagerMixin
from .owner_manager import OwnerManagerMixin
from .info_manager import InfoManagerMixin


class SafeTeaWallet(TransactionManagerMixin, OwnerManagerMixin, InfoManagerMixin):
    def __init__(self, web3: Web3, wallet_address: str, account: Account) -> None:
        """Initialize the SafeTeaWallet instance.

        Args:
            web3 (Web3): An instance of Web3 connected to the desired Ethereum network.
            wallet_address (str): The checksum address of the wallet contract.
            account (Account): The Ethereum account to use for signing transactions.
        """

        self.web3 = web3
        self.wallet_address = self.web3.to_checksum_address(wallet_address)
        self.account = account

        self.wallet_contract = self.web3.eth.contract(
            address=self.wallet_address, abi=wallet_abi()
        )

    @property
    def address(self) -> ChecksumAddress:
        return self.account.address

    def _latest_timestamp(self) -> int:
        return self.web3.eth.get_block("latest")["timestamp"]

    def _is_owner(self) -> bool:
        return self.address in self.get_owners()

    def _require_owner(self) -> None:
        if not self._is_owner():
            raise NotOwnerError("Only wallet owners can perform this action")

    def _build_and_send(self, contract_fn: ContractFunction) -> str:
        self._require_owner()

        tx = contract_fn.build_transaction(
            {
                "from": self.address,
                "nonce": self.web3.eth.get_transaction_count(
                    self.address,
                    "pending",
                ),
                "gas": contract_fn.estimate_gas({"from": self.address}),
                "gasPrice": self.web3.eth.gas_price,
            }
        )

        signed_tx = self.account.sign_transaction(tx)

        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        return tx_hash.hex()
