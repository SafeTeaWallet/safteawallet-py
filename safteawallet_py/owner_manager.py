from typing import List
from eth_typing import ChecksumAddress
from .models import OwnerProposal
from .exceptions import SafeTeaError, ProposalNotFoundError

class OwnerManagerMixin:
    def propose_add_owner(self, new_owner: ChecksumAddress, expiry: int = 3600):
        """Propose adding a new owner to the wallet."""
        try:
            # 0 corresponds to OwnerProposalType.Add
            tx_hash = self._build_and_send(
                self.wallet_contract.functions.proposeOwner(new_owner, 0, expiry)
            )
            return tx_hash
        except Exception as e:
            raise SafeTeaError(f"Error occurred while proposing to add owner: {e}")

    def propose_remove_owner(self, owner_to_remove: ChecksumAddress, expiry: int = 3600):
        """Propose removing an owner from the wallet."""
        try:
            # 1 corresponds to OwnerProposalType.Remove
            tx_hash = self._build_and_send(
                self.wallet_contract.functions.proposeOwner(owner_to_remove, 1, expiry)
            )
            return tx_hash
        except Exception as e:
            raise SafeTeaError(f"Error occurred while proposing to remove owner: {e}")

    def get_owner_proposal_count(self) -> int:
        """Get the total number of owner proposals."""
        try:
            return self.wallet_contract.functions.getOwnerProposalCount().call()
        except Exception as e:
            raise SafeTeaError(f"Error getting owner proposal count: {e}")

    def _validate_owner_proposal_exists(self, proposal_index: int) -> None:
        try:
            count = self.get_owner_proposal_count()
            if proposal_index < 0 or proposal_index >= count:
                raise ProposalNotFoundError(f"Owner proposal {proposal_index} does not exist.")
        except SafeTeaError:
            raise
        except Exception as e:
            raise SafeTeaError(f"Error validating owner proposal: {e}")

    def confirm_owner_proposal(self, proposal_index: int):
        """Confirm an owner change proposal."""
        self._validate_owner_proposal_exists(proposal_index)
        try:
            tx_hash = self._build_and_send(
                self.wallet_contract.functions.confirmOwnerProposal(proposal_index)
            )
            return tx_hash
        except Exception as e:
            raise SafeTeaError(f"Error occurred while confirming owner proposal: {e}")

    def reject_owner_proposal(self, proposal_index: int):
        """Reject an owner change proposal."""
        self._validate_owner_proposal_exists(proposal_index)
        try:
            tx_hash = self._build_and_send(
                self.wallet_contract.functions.rejectOwnerProposal(proposal_index)
            )
            return tx_hash
        except Exception as e:
            raise SafeTeaError(f"Error occurred while rejecting owner proposal: {e}")

    def get_owner_proposal(self, index: int) -> OwnerProposal:
        """Get a specific owner proposal by index."""
        try:
            proposal_tuple = self.wallet_contract.functions.getOwnerProposal(index).call()
            return OwnerProposal.from_tuple(proposal_tuple)
        except Exception as e:
            raise SafeTeaError(f"Error getting owner proposal: {e}")
