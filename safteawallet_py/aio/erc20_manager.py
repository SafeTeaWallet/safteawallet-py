from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from eth_account.signers.local import LocalAccount

from ..utils import erc20_abi
from ..exceptions import SafeTeaError


class AsyncERC20Manager:
    """Async version of ERC20Manager.

    Read operations are called directly against the token contract.
    Write operations are encoded as calldata and submitted through the wallet's
    multi-sig flow via ``submit_transaction``.
    """

    def __init__(
        self,
        web3: AsyncWeb3,
        token_address: str,
        wallet_address: str,
        account: LocalAccount,
        wallet,  # AsyncSafeTeaWallet – avoids circular import
    ) -> None:
        self.web3 = web3
        self.token_address: ChecksumAddress = web3.to_checksum_address(token_address)
        self.wallet_address: ChecksumAddress = web3.to_checksum_address(wallet_address)
        self.account = account
        self._wallet = wallet

        self.token_contract = web3.eth.contract(
            address=self.token_address, abi=erc20_abi()
        )

    # Read helpers

    async def name(self) -> str:
        """Return the token name."""
        try:
            return await self.token_contract.functions.name().call()
        except Exception as e:
            raise SafeTeaError(f"Error fetching token name: {e}")

    async def symbol(self) -> str:
        """Return the token symbol."""
        try:
            return await self.token_contract.functions.symbol().call()
        except Exception as e:
            raise SafeTeaError(f"Error fetching token symbol: {e}")

    async def decimals(self) -> int:
        """Return the number of decimals."""
        try:
            return await self.token_contract.functions.decimals().call()
        except Exception as e:
            raise SafeTeaError(f"Error fetching token decimals: {e}")

    async def total_supply(self) -> int:
        """Return the total token supply (in smallest unit)."""
        try:
            return await self.token_contract.functions.totalSupply().call()
        except Exception as e:
            raise SafeTeaError(f"Error fetching total supply: {e}")

    async def balance_of(self, owner: ChecksumAddress) -> int:
        """Return the token balance of *owner* (in smallest unit)."""
        try:
            return await self.token_contract.functions.balanceOf(owner).call()
        except Exception as e:
            raise SafeTeaError(f"Error fetching balance: {e}")

    async def wallet_balance(self) -> int:
        """Return the token balance held by the SafeTea wallet."""
        return await self.balance_of(self.wallet_address)

    async def allowance(self, owner: ChecksumAddress, spender: ChecksumAddress) -> int:
        """Return the remaining allowance that *spender* may use on behalf of *owner*."""
        try:
            return await self.token_contract.functions.allowance(owner, spender).call()
        except Exception as e:
            raise SafeTeaError(f"Error fetching allowance: {e}")

    # Write helpers – submitted through the wallet's multi-sig flow

    async def transfer(
        self, to: ChecksumAddress, amount: int, expiry: int = 3600
    ) -> int:
        """Propose a token transfer from the wallet to *to*.

        Returns the transaction index in the wallet's proposal queue.
        """
        try:
            data = self.token_contract.encode_abi("transfer", args=[to, amount])
            return await self._wallet.submit_transaction(
                to=self.token_address, value=0, data=data, expiry=expiry
            )
        except Exception as e:
            raise SafeTeaError(f"Error submitting token transfer: {e}")

    async def approve(
        self, spender: ChecksumAddress, amount: int, expiry: int = 3600
    ) -> int:
        """Propose an ERC20 approval from the wallet for *spender*.

        Returns the transaction index in the wallet's proposal queue.
        """
        try:
            data = self.token_contract.encode_abi("approve", args=[spender, amount])
            return await self._wallet.submit_transaction(
                to=self.token_address, value=0, data=data, expiry=expiry
            )
        except Exception as e:
            raise SafeTeaError(f"Error submitting token approval: {e}")

    async def transfer_from(
        self,
        from_address: ChecksumAddress,
        to: ChecksumAddress,
        amount: int,
        expiry: int = 3600,
    ) -> int:
        """Propose a transferFrom call executed by the wallet.

        Returns the transaction index in the wallet's proposal queue.
        """
        try:
            data = self.token_contract.encode_abi(
                "transferFrom", args=[from_address, to, amount]
            )
            return await self._wallet.submit_transaction(
                to=self.token_address, value=0, data=data, expiry=expiry
            )
        except Exception as e:
            raise SafeTeaError(f"Error submitting transferFrom: {e}")
