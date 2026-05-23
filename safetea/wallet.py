from typing import List, Optional, Dict, Any
from eth_typing import ChecksumAddress
from web3 import Web3, Account
from .utils import wallet_abi
from .models import WalletResult



class SafeTeaWallet:
    def __init__(self, web3: Web3, wallet_address: str, account: Account) -> None:
        self.web3 = web3
        self.wallet_address = self.web3.to_checksum_address(wallet_address)
        self.account = account

        self.wallet_contract = self.web3.eth.contract(
            address=self.wallet_address, abi=wallet_abi()
        )
        
    def get_info(self) -> WalletResult:
        """Get wallet information including owners and threshold."""
        info = self.wallet_contract.functions.getInfo().call()
        print("Raw Wallet Info:", info)  # Debugging statement
        return WalletResult(
            address=self.wallet_address,
            owners=info[0],
            threshold=info[1],
        )