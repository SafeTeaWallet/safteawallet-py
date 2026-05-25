from typing import List, Optional, Dict, Any
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from eth_account.signers.local import LocalAccount
from web3.contract.async_contract import AsyncContractFunction

from ..utils import wallet_abi
from ..exceptions import NotOwnerError

from .transaction_manager import AsyncTransactionManagerMixin
from .owner_manager import AsyncOwnerManagerMixin
from .info_manager import AsyncInfoManagerMixin


class AsyncSafeTeaWallet(AsyncTransactionManagerMixin, AsyncOwnerManagerMixin, AsyncInfoManagerMixin):
    def __init__(self, web3: AsyncWeb3, wallet_address: str, account: LocalAccount) -> None:
        """Initialize the AsyncSafeTeaWallet instance.

        Args:
            web3 (AsyncWeb3): An instance of AsyncWeb3 connected to the desired Ethereum network.
            wallet_address (str): The checksum address of the wallet contract.
            account (LocalAccount): The Ethereum account to use for signing transactions.
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

    async def _latest_timestamp(self) -> int:
        block = await self.web3.eth.get_block("latest")
        return block["timestamp"]

    async def _is_owner(self) -> bool:
        owners = await self.get_owners()
        return self.address in owners

    async def _require_owner(self) -> None:
        is_owner = await self._is_owner()
        if not is_owner:
            raise NotOwnerError("Only wallet owners can perform this action")

    async def _build_and_send(self, contract_fn: AsyncContractFunction) -> str:
        await self._require_owner()

        nonce = await self.web3.eth.get_transaction_count(
            self.address,
            "pending",
        )
        gas = await contract_fn.estimate_gas({"from": self.address})
        gas_price = await self.web3.eth.gas_price

        tx = await contract_fn.build_transaction(
            {
                "from": self.address,
                "nonce": nonce,
                "gas": gas,
                "gasPrice": gas_price,
            }
        )

        signed_tx = self.account.sign_transaction(tx)

        tx_hash = await self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        return tx_hash.hex()
