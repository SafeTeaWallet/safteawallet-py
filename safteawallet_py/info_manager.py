from typing import List
from eth_typing import ChecksumAddress
from .models import WalletResult
from .exceptions import SafeTeaError

class InfoManagerMixin:
    def get_info(self) -> WalletResult:
        """Get wallet information including owners and threshold."""
        try:
            info = self.wallet_contract.functions.getInfo().call()
            return WalletResult(
                address=self.wallet_address,
                owners=info[0],
                threshold=info[1],
            )
        except Exception as e:
            raise SafeTeaError(f"Error getting wallet info: {e}")

    def get_owners(self) -> List[ChecksumAddress]:
        """Get the list of wallet owners."""
        try:
            return self.wallet_contract.functions.getOwners().call()
        except Exception as e:
            raise SafeTeaError(f"Error getting owners: {e}")

    def get_threshold(self) -> int:
        """Get the current threshold for transaction execution."""
        try:
            return self.wallet_contract.functions.getMajorityThreshold().call()
        except Exception as e:
            raise SafeTeaError(f"Error getting threshold: {e}")
