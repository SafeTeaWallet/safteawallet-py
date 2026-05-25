from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from eth_typing.evm import ChecksumAddress


class TxStatus(IntEnum):
    PENDING = 0
    EXECUTED = 1
    CANCELED = 2


class ProposalType(IntEnum):
    ADD = 0
    REMOVE = 1


@dataclass
class Transaction:
    to: str
    value: int  # wei
    data: bytes
    status: TxStatus
    confirmations: int  # vote count
    rejections: int     # vote count
    expiry: int  # unix timestamp
    created_at: int  # unix timestamp

    @classmethod
    def from_tuple(cls, t: tuple) -> Transaction:
        """Build from the TransactionView tuple returned by getTransaction().

        Tuple order: (index, to, value, data, status, isExpired, confirmations,
                      rejections, expiry, createdAt)
        """
        (
            _index,
            to,
            value,
            data,
            status_int,
            _is_expired,
            confirmations,
            rejections,
            expiry,
            created_at,
        ) = t
        return cls(
            to=to,
            value=value,
            data=bytes(data),
            status=TxStatus(status_int),
            confirmations=confirmations,
            rejections=rejections,
            expiry=expiry,
            created_at=created_at,
        )

    @property
    def is_pending(self) -> bool:
        return self.status == TxStatus.PENDING

    @property
    def is_executed(self) -> bool:
        return self.status == TxStatus.EXECUTED

    @property
    def is_canceled(self) -> bool:
        return self.status == TxStatus.CANCELED


@dataclass
class OwnerProposal:
    proposed_owner: str
    status: TxStatus
    proposal_type: ProposalType
    confirmations: int
    rejections: int
    expiry: int  # unix timestamp
    created_at: int  # unix timestamp

    @classmethod
    def from_tuple(cls, t: tuple) -> OwnerProposal:
        """Build from the OwnerProposalView tuple returned by getOwnerProposal().

        Tuple order: (index, proposedOwner, proposalType, status, isExpired,
                      confirmations, rejections, expiry, createdAt)
        """
        (
            _index,
            proposed_owner,
            proposal_type_int,
            status_int,
            _is_expired,
            confirmations,
            rejections,
            expiry,
            created_at,
        ) = t
        return cls(
            proposed_owner=proposed_owner,
            status=TxStatus(status_int),
            proposal_type=ProposalType(proposal_type_int),
            confirmations=confirmations,
            rejections=rejections,
            expiry=expiry,
            created_at=created_at,
        )

    @property
    def is_pending(self) -> bool:
        return self.status == TxStatus.PENDING

    @property
    def is_executed(self) -> bool:
        return self.status == TxStatus.EXECUTED

    @property
    def is_canceled(self) -> bool:
        return self.status == TxStatus.CANCELED


@dataclass(frozen=True)
class WalletInfo:
    address: ChecksumAddress
    owners: list[ChecksumAddress]
    threshold: int


@dataclass(frozen=True)
class TxReceipt:
    tx_hash: str
    block_number: int
    gas_used: int
    wallet_address: ChecksumAddress | None  # set for create_wallet receipts




@dataclass
class WalletCreationResult:
    wallet_address: str
    transaction_hash: str
    
@dataclass
class WalletResult:
    address: ChecksumAddress
    owners: list[ChecksumAddress]
    threshold: int