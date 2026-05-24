from typing import List, Optional, Dict, Any
from eth_typing import ChecksumAddress
from web3 import Web3, Account
from .utils import wallet_abi
from .models import WalletResult, Transaction
from .exceptions import (
    SafeTeaError,
    NotOwnerError,
    AlreadyVotedError,
    TransactionExpiredError,
    InsufficientConfirmationsError,
    ProposalNotFoundError,
)


class SafeTeaWallet:
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

    def _is_owner(self) -> bool:
        owners = self.get_owners()
        return self.account.address in owners

    def _build_and_send(self, contract_fn) -> str:
        if not self._is_owner():
            raise NotOwnerError("Only wallet owners can perform this action")

        nonce = self.web3.eth.get_transaction_count(self.account.address)
        tx = contract_fn.build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "gas": contract_fn.estimate_gas({"from": self.account.address}),
                "gasPrice": self.web3.eth.gas_price,
            }
        )
        signed = self.account.sign_transaction(tx)
        return self.web3.eth.send_raw_transaction(signed.raw_transaction).hex()

    # Transaction management functions
    def submit_transaction(
        self, to: ChecksumAddress, value: int = 0, data: bytes = b"", expiry: int = 3600
    ) -> str:
        """Submit a new transaction proposal."""
        try:
            tx_hash = self._build_and_send(
                self.wallet_contract.functions.submitTransaction(
                    to, value, data, expiry
                )
            )
            # Take the tx_index from TransactionSubmitted(txIndex, to, value) event
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            events = self.wallet_contract.events.TransactionSubmitted().process_receipt(
                receipt
            )
            if not events:
                raise SafeTeaError("TransactionSubmitted event not found in receipt")
            tx_index = events[0]["args"]["txIndex"]
            return tx_index

        except Exception as e:
            raise SafeTeaError(f"Error occurred while submitting transaction: {e}")

    def confirm_transaction(self, tx_index: int):
        """Confirm a transaction proposal."""
        try:
            tx_hash = self._build_and_send(
                self.wallet_contract.functions.confirmTransaction(tx_index)
            )
            return tx_hash
        except Exception as e:
            raise SafeTeaError(f"Error occurred while confirming transaction: {e}")

    def reject_transaction(self, tx_index: int):
        """Reject a transaction proposal."""
        try:
            tx_hash = self._build_and_send(
                self.wallet_contract.functions.rejectTransaction(tx_index)
            )
            return tx_hash
        except Exception as e:
            raise SafeTeaError(f"Error occurred while rejecting transaction: {e}")

    def get_info(self) -> WalletResult:
        """Get wallet information including owners and threshold."""
        info = self.wallet_contract.functions.getInfo().call()
        return WalletResult(
            address=self.wallet_address,
            owners=info[0],
            threshold=info[1],
        )

    def get_transaction_count(self) -> int:
        """Get the total number of transaction proposals."""
        return self.wallet_contract.functions.getTransactionCount().call()

    def get_transaction(self, tx_index: int) -> Transaction:
        """Get a specific transaction proposal by index."""
        tx_tuple = self.wallet_contract.functions.getTransaction(tx_index).call()
        return Transaction.from_tuple(tx_tuple)

    # Owner management functions
    def propose_add_owner(self): ...
    def propose_remove_owner(self): ...
    def confirm_owner_proposal(self): ...
    def execute_owner_proposal(self): ...
    def reject_owner_proposal(self): ...

    def get_owner_proposal(self, index: int):
        """Get a specific owner proposal by index."""
        return self.wallet_contract.functions.getOwnerProposal(index).call()

    def get_owners(self) -> List[ChecksumAddress]:
        """Get the list of wallet owners."""
        return self.wallet_contract.functions.getOwners().call()

    def get_threshold(self) -> int:
        """Get the current threshold for transaction execution."""
        return self.wallet_contract.functions.getThreshold().call()
