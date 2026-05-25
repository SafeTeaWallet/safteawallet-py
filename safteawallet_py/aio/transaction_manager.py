from eth_typing import ChecksumAddress
from ..models import Transaction
from ..exceptions import SafeTeaError, AlreadyVotedError, TransactionExpiredError

class AsyncTransactionManagerMixin:
    async def _validate_transaction_state(self, transaction: Transaction) -> None:
        if transaction.is_executed:
            raise SafeTeaError("Transaction has already been executed")

        if transaction.is_canceled:
            raise SafeTeaError("Transaction has been canceled")

        if self.address in transaction.confirmations:
            raise AlreadyVotedError("You have already confirmed this transaction")

        if self.address in transaction.rejections:
            raise AlreadyVotedError("You have already rejected this transaction")

        latest_timestamp = await self._latest_timestamp()
        if transaction.expiry < latest_timestamp:
            raise TransactionExpiredError("Transaction proposal has expired")

    async def submit_transaction(
        self, to: ChecksumAddress, value: int = 0, data: bytes = b"", expiry: int = 3600
    ) -> int:
        """Submit a new transaction proposal asynchronously."""
        try:
            tx_hash = await self._build_and_send(
                self.wallet_contract.functions.submitTransaction(
                    to, value, data, expiry
                )
            )
            # Take the tx_index from TransactionSubmitted(txIndex, to, value) event
            receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)
            events = self.wallet_contract.events.TransactionSubmitted().process_receipt(
                receipt
            )
            if not events:
                raise SafeTeaError("TransactionSubmitted event not found in receipt")
            tx_index = events[0]["args"]["txIndex"]
            return tx_index

        except Exception as e:
            raise SafeTeaError(f"Error occurred while submitting transaction: {e}")

    async def confirm_transaction(self, tx_index: int):
        """Confirm a transaction proposal asynchronously."""
        try:
            transaction = await self.get_transaction(tx_index)
            await self._validate_transaction_state(transaction)

            tx_hash = await self._build_and_send(
                self.wallet_contract.functions.confirmTransaction(tx_index)
            )
            return tx_hash
        except Exception as e:
            raise SafeTeaError(f"Error occurred while confirming transaction: {e}")

    async def reject_transaction(self, tx_index: int):
        """Reject a transaction proposal asynchronously."""
        try:
            transaction = await self.get_transaction(tx_index)
            await self._validate_transaction_state(transaction)

            tx_hash = await self._build_and_send(
                self.wallet_contract.functions.rejectTransaction(tx_index)
            )
            return tx_hash
        except Exception as e:
            raise SafeTeaError(f"Error occurred while rejecting transaction: {e}")

    async def get_transaction_count(self) -> int:
        """Get the total number of transaction proposals asynchronously."""
        try:
            return await self.wallet_contract.functions.getTransactionCount().call()
        except Exception as e:
            raise SafeTeaError(f"Error getting transaction count: {e}")

    async def get_transaction(self, tx_index: int) -> Transaction:
        """Get a specific transaction proposal by index asynchronously."""
        try:
            tx_tuple = await self.wallet_contract.functions.getTransaction(tx_index).call()
            return Transaction.from_tuple(tx_tuple)
        except Exception as e:
            raise SafeTeaError(f"Error getting transaction: {e}")
