from typing import Optional

from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount

from .factory import SafeTeaFactory
from .wallet import SafeTeaWallet
from .erc20_manager import ERC20Manager


class SafeTeaClient:
    """Client for interacting with the SafeTea protocol."""

    def __init__(
        self,
        rpc_url: str,
        factory_address: str,
        private_key: Optional[str] = None,
    ) -> None:
        """
        Initialize the SafeTea client.

        Args:
            rpc_url: HTTP RPC endpoint of the blockchain node.
            factory_address: Address of the SafeTea factory contract.
            private_key: Optional private key used for signing transactions.
        """
        self.rpc_url = rpc_url
        self.factory_address = Web3.to_checksum_address(factory_address)
        self.private_key = private_key

        self.web3 = Web3(Web3.HTTPProvider(rpc_url))

        if not self.web3.is_connected():
            raise ConnectionError(f"Failed to connect to RPC endpoint: {rpc_url}")

        self.account: Optional[LocalAccount] = None

        if private_key:
            self.account = Account.from_key(private_key)

        self.factory = SafeTeaFactory(
            web3=self.web3,
            factory_address=self.factory_address,
            account=self.account,
        )
        
    def wallet(self, wallet_address: str) -> SafeTeaWallet:
        """Get a SafeTeaWallet instance for the specified wallet address."""
        return SafeTeaWallet(
            web3=self.web3,
            wallet_address=wallet_address,
            account=self.account,
        )

    def erc20(self, token_address: str, wallet_address: str) -> ERC20Manager:
        """Get an ERC20Manager for *token_address* operating through *wallet_address*."""
        wallet = self.wallet(wallet_address)
        return ERC20Manager(
            web3=self.web3,
            token_address=token_address,
            wallet_address=wallet_address,
            account=self.account,
            wallet=wallet,
        )