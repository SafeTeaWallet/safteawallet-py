from typing import List, Optional, Dict, Any
from eth_typing import ChecksumAddress
from web3 import Web3
from .utils import factory_abi


class SafeTeaFactory:
    def __init__(self, rpc_url: str, factory_address: str, private_key: Optional[str] = None) -> None:
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.factory_address = self.web3.to_checksum_address(factory_address)
        self.private_key = private_key

        self.factory_contract = self.web3.eth.contract(
            address=self.factory_address, abi=factory_abi
        )

    def create_wallet_tx(
        self, owners: List[ChecksumAddress], from_address: str
    ) -> Dict[str, Any]:
        """Build a transaction to create a new SafeTea wallet with the specified owners.
        Args:
            owners (List[ChecksumAddress]): A list of owner addresses for the new wallet.
            from_address (str): The address from which the transaction will be sent.
        Returns:
            Dict[str, Any]: A dictionary representing the transaction to create the wallet.
        """

        from_address = self.web3.to_checksum_address(from_address)

        return self.factory_contract.functions.createSafe(owners).build_transaction(
            {
                "from": from_address,
                "nonce": self.web3.eth.get_transaction_count(from_address),
                "gas": 2_000_000,
                "gasPrice": self.web3.eth.gas_price,
            }
        )

    def get_user_wallets(self, user_address: ChecksumAddress) -> List[ChecksumAddress]:
        """Get a list of SafeTea wallets owned by the specified user.

        Args:
            user_address (ChecksumAddress): The address of the user to query.

        Returns:
            List[ChecksumAddress]: A list of wallet addresses owned by the user.
        """
        return self.factory_contract.functions.getUserWallets(user_address).call()

    def send_and_get_wallet(self, signed_tx: Any) -> str:
        """Send a signed transaction to create a new SafeTea wallet and return the address of the created wallet.

        Args:
            signed_tx (Any): The signed transaction object to be sent.

        Raises:
            Exception: If the transaction fails.
            Exception: If the transaction succeeds but the WalletCreated event is not found in the transaction receipt.

        Returns:
            str: The address of the created wallet.
        """
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status != 1:
            raise Exception("Transaction failed")

        # Event filter
        event = self.factory_contract.events.WalletCreated().process_receipt(receipt)

        if not event:
            raise Exception("WalletCreated event not found")

        wallet_address = event[0]["args"]["wallet"]

        return wallet_address
