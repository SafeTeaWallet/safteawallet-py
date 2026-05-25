from eth_typing import ChecksumAddress
from web3 import Web3
from eth_account.signers.local import LocalAccount

from .utils import erc20_abi
from .exceptions import SafeTeaError


class ERC20Manager:
    """Interact with an ERC20 token on behalf of a SafeTea wallet.

    Read operations (balanceOf, allowance, etc.) are called directly against
    the token contract.  Write operations (transfer, approve, transferFrom) are
    encoded as calldata and submitted through the wallet's multi-sig flow via
    ``submit_transaction``, so they require owner confirmation before execution.
    """

    def __init__(
        self,
        web3: Web3,
        token_address: str,
        wallet_address: str,
        account: LocalAccount,
        wallet,
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

    def name(self) -> str:
        """Return the token name."""
        try:
            return self.token_contract.functions.name().call()
        except Exception as e:
            raise SafeTeaError(f"Error fetching token name: {e}")

    def symbol(self) -> str:
        """Return the token symbol."""
        try:
            return self.token_contract.functions.symbol().call()
        except Exception as e:
            raise SafeTeaError(f"Error fetching token symbol: {e}")

    def decimals(self) -> int:
        """Return the number of decimals."""
        try:
            return self.token_contract.functions.decimals().call()
        except Exception as e:
            raise SafeTeaError(f"Error fetching token decimals: {e}")

    def total_supply(self) -> int:
        """Return the total token supply (in smallest unit)."""
        try:
            return self.token_contract.functions.totalSupply().call()
        except Exception as e:
            raise SafeTeaError(f"Error fetching total supply: {e}")

    def balance_of(self, owner: ChecksumAddress) -> int:
        """Return the token balance of *owner* (in smallest unit)."""
        try:
            return self.token_contract.functions.balanceOf(owner).call()
        except Exception as e:
            raise SafeTeaError(f"Error fetching balance: {e}")

    def wallet_balance(self) -> int:
        """Return the token balance held by the SafeTea wallet."""
        return self.balance_of(self.wallet_address)

    def allowance(self, owner: ChecksumAddress, spender: ChecksumAddress) -> int:
        """Return the remaining allowance that *spender* may use on behalf of *owner*."""
        try:
            return self.token_contract.functions.allowance(owner, spender).call()
        except Exception as e:
            raise SafeTeaError(f"Error fetching allowance: {e}")

    # Write helpers – submitted through the wallet's multi-sig flow

    def transfer(self, to: ChecksumAddress, amount: int, expiry: int = 3600) -> int:
        """Propose a token transfer from the wallet to *to*.

        Returns the transaction index in the wallet's proposal queue.
        """
        try:
            data = self.token_contract.encode_abi("transfer", args=[to, amount])
            return self._wallet.submit_transaction(
                to=self.token_address, value=0, data=data, expiry=expiry
            )
        except Exception as e:
            raise SafeTeaError(f"Error submitting token transfer: {e}")

    def approve(self, spender: ChecksumAddress, amount: int, expiry: int = 3600) -> int:
        """Propose an ERC20 approval from the wallet for *spender*.

        Returns the transaction index in the wallet's proposal queue.
        """
        try:
            data = self.token_contract.encode_abi("approve", args=[spender, amount])
            return self._wallet.submit_transaction(
                to=self.token_address, value=0, data=data, expiry=expiry
            )
        except Exception as e:
            raise SafeTeaError(f"Error submitting token approval: {e}")

    def transfer_from(
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
            return self._wallet.submit_transaction(
                to=self.token_address, value=0, data=data, expiry=expiry
            )
        except Exception as e:
            raise SafeTeaError(f"Error submitting transferFrom: {e}")
