from typing import Optional

from web3 import AsyncWeb3, AsyncHTTPProvider
from eth_account import Account
from eth_account.signers.local import LocalAccount

from .factory import AsyncSafeTeaFactory
from .wallet import AsyncSafeTeaWallet
from .erc20_manager import AsyncERC20Manager


class AsyncSafeTeaClient:
    """Async Client for interacting with the SafeTea protocol."""

    def __init__(
        self,
        rpc_url: str,
        factory_address: str,
        private_key: Optional[str] = None,
    ) -> None:
        """
        Initialize the Async SafeTea client.

        Args:
            rpc_url: HTTP RPC endpoint of the blockchain node.
            factory_address: Address of the SafeTea factory contract.
            private_key: Optional private key used for signing transactions.
        """
        self.rpc_url = rpc_url
        self.factory_address = AsyncWeb3.to_checksum_address(factory_address)
        self.private_key = private_key

        self.web3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))

        self.account: Optional[LocalAccount] = None

        if private_key:
            self.account = Account.from_key(private_key)

        self.factory = AsyncSafeTeaFactory(
            web3=self.web3,
            factory_address=self.factory_address,
            account=self.account,
        )
        
    async def check_connection(self) -> None:
        """Check the connection to the RPC endpoint asynchronously."""
        is_connected = await self.web3.is_connected()
        if not is_connected:
            raise ConnectionError(f"Failed to connect to RPC endpoint: {self.rpc_url}")

    def wallet(self, wallet_address: str) -> AsyncSafeTeaWallet:
        """Get an AsyncSafeTeaWallet instance for the specified wallet address."""
        return AsyncSafeTeaWallet(
            web3=self.web3,
            wallet_address=wallet_address,
            account=self.account,
        )

    def erc20(self, token_address: str, wallet_address: str) -> AsyncERC20Manager:
        """Get an AsyncERC20Manager for *token_address* operating through *wallet_address*."""
        wallet = self.wallet(wallet_address)
        return AsyncERC20Manager(
            web3=self.web3,
            token_address=token_address,
            wallet_address=wallet_address,
            account=self.account,
            wallet=wallet,
        )
