from typing import List
from eth_typing import ChecksumAddress
from ..models import OwnerProposal
from ..exceptions import SafeTeaError, ProposalNotFoundError

class AsyncOwnerManagerMixin:
    async def propose_add_owner(self, new_owner: ChecksumAddress, expiry: int = 3600):
        """Propose adding a new owner to the wallet asynchronously."""
        try:
            tx_hash = await self._build_and_send(
                self.wallet_contract.functions.proposeOwner(new_owner, 0, expiry)
            )
            return tx_hash
        except Exception as e:
            raise SafeTeaError(f"Error occurred while proposing to add owner: {e}")

    async def propose_remove_owner(self, owner_to_remove: ChecksumAddress, expiry: int = 3600):
        """Propose removing an owner from the wallet asynchronously."""
        try:
            tx_hash = await self._build_and_send(
                self.wallet_contract.functions.proposeOwner(owner_to_remove, 1, expiry)
            )
            return tx_hash
        except Exception as e:
            raise SafeTeaError(f"Error occurred while proposing to remove owner: {e}")

    async def get_owner_proposal_count(self) -> int:
        """Get the total number of owner proposals asynchronously."""
        try:
            return await self.wallet_contract.functions.getOwnerProposalCount().call()
        except Exception as e:
            raise SafeTeaError(f"Error getting owner proposal count: {e}")

    async def _validate_owner_proposal_exists(self, proposal_index: int) -> None:
        try:
            count = await self.get_owner_proposal_count()
            if proposal_index < 0 or proposal_index >= count:
                raise ProposalNotFoundError(f"Owner proposal {proposal_index} does not exist.")
        except SafeTeaError:
            raise
        except Exception as e:
            raise SafeTeaError(f"Error validating owner proposal: {e}")

    async def confirm_owner_proposal(self, proposal_index: int):
        """Confirm an owner change proposal asynchronously."""
        await self._validate_owner_proposal_exists(proposal_index)
        try:
            tx_hash = await self._build_and_send(
                self.wallet_contract.functions.confirmOwnerProposal(proposal_index)
            )
            return tx_hash
        except Exception as e:
            raise SafeTeaError(f"Error occurred while confirming owner proposal: {e}")

    async def reject_owner_proposal(self, proposal_index: int):
        """Reject an owner change proposal asynchronously."""
        await self._validate_owner_proposal_exists(proposal_index)
        try:
            tx_hash = await self._build_and_send(
                self.wallet_contract.functions.rejectOwnerProposal(proposal_index)
            )
            return tx_hash
        except Exception as e:
            raise SafeTeaError(f"Error occurred while rejecting owner proposal: {e}")

    async def get_owner_proposal(self, index: int) -> OwnerProposal:
        """Get a specific owner proposal by index asynchronously."""
        try:
            proposal_tuple = await self.wallet_contract.functions.getOwnerProposal(index).call()
            return OwnerProposal.from_tuple(proposal_tuple)
        except Exception as e:
            raise SafeTeaError(f"Error getting owner proposal: {e}")
