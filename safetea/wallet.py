from typing import List, Optional, Dict, Any
from eth_typing import ChecksumAddress
from web3 import Web3, Account
from .utils import wallet_abi
from .models import WalletResult
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
        self.web3 = web3
        self.wallet_address = self.web3.to_checksum_address(wallet_address)
        self.account = account

        self.wallet_contract = self.web3.eth.contract(
            address=self.wallet_address, abi=wallet_abi()
        )

    # Transaction management functions
    def submit_transaction(
        self, to: ChecksumAddress, value: int = 0, data: bytes = b"", expiry: int = 3600
    ) -> str:
        """Submit a new transaction proposal."""
        owners = self.get_owners()
        if self.account.address not in owners:
            raise NotOwnerError("Only wallet owners can submit transactions")

        nonce = self.web3.eth.get_transaction_count(self.account.address)
        tx = self.wallet_contract.functions.submitTransaction(
            to, value, data, expiry
        ).build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "gas": 200000,
                "gasPrice": self.web3.eth.gas_price,
            }
        )
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        # Take the tx_index from TransactionSubmitted(txIndex, to, value) event
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        events = self.wallet_contract.events.TransactionSubmitted().process_receipt(
            receipt
        )
        if not events:
            raise SafeTeaError("TransactionSubmitted event not found in receipt")
        tx_index = events[0]["args"]["txIndex"]
        return tx_index

    def confirm_transaction(self): ...
    def execute_transaction(self): ...
    def reject_transaction(self): ...

    def get_info(self) -> WalletResult:
        """Get wallet information including owners and threshold."""
        info = self.wallet_contract.functions.getInfo().call()
        return WalletResult(
            address=self.wallet_address,
            owners=info[0],
            threshold=info[1],
        )

    def get_transaction(self): ...

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
