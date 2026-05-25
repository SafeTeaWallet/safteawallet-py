from typing import List
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from eth_account.signers.local import LocalAccount
from ..exceptions import SafeTeaError
from ..models import WalletCreationResult
from ..utils import factory_abi


class AsyncSafeTeaFactory:
    def __init__(self, web3: AsyncWeb3, factory_address: str, account: LocalAccount) -> None:
        self.web3 = web3
        self.factory_address = self.web3.to_checksum_address(factory_address)
        self.account = account

        self.factory_contract = self.web3.eth.contract(
            address=self.factory_address, abi=factory_abi()
        )

    async def create_wallet(self, owners: List[ChecksumAddress]) -> WalletCreationResult:
        """
        Create a new SafeTea wallet with the specified owners asynchronously.
        Args:
            owners: A list of wallet owner addresses.
        Returns:
            A dictionary containing the wallet address, transaction hash, and receipt.
        Raises:
            Exception: If the account is not set or if the transaction fails.
        """
        if len(owners) < 2:
            raise ValueError("At least 2 owners are required to create a wallet")

        if not self.account:
            raise Exception("Account is required to create a wallet")
            
        contract_func = self.factory_contract.functions.createWallet(owners)

        nonce = await self.web3.eth.get_transaction_count(self.account.address)
        gas = await contract_func.estimate_gas({"from": self.account.address})
        gas_price = await self.web3.eth.gas_price

        tx = await contract_func.build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "gas": gas,
                "gasPrice": gas_price,
            }
        )
        signed_tx = self.web3.eth.account.sign_transaction(
            tx, private_key=self.account.key
        )
        # Send the transaction and wait for the receipt
        tx_hash = await self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise Exception("Transaction failed: " + str("0x" + tx_hash.hex()))
        # Event filter
        event = self.factory_contract.events.WalletCreated().process_receipt(receipt)
        if not event:
            raise Exception("WalletCreated event not found")
        wallet_address = event[0]["args"]["wallet"]
        return WalletCreationResult(
            wallet_address=wallet_address,
            transaction_hash=tx_hash.hex(),
        )

    async def get_user_wallets(self, user_address: ChecksumAddress) -> List[ChecksumAddress]:
        """Get a list of SafeTea wallets owned by the specified user asynchronously."""
        try:
            return await self.factory_contract.functions.getUserWallets(user_address).call()
        except Exception as e:
            raise SafeTeaError(f"Error getting user wallets: {e}")
