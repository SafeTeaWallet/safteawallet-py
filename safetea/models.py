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
    confirmations: int
    rejections: int
    expiry: int  # unix timestamp
    created_at: int  # unix timestamp

    @classmethod
    def from_tuple(cls, t: tuple) -> Transaction:
        """Build from the raw tuple returned by getTransaction()."""
        (
            to,
            value,
            data,
            executed,
            canceled,
            confirmations,
            rejections,
            expiry,
            created_at,
        ) = t
        if canceled:
            status = TxStatus.CANCELED
        elif executed:
            status = TxStatus.EXECUTED
        else:
            status = TxStatus.PENDING
        return cls(
            to=to,
            value=value,
            data=bytes(data),
            status=status,
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
    def from_tuple(cls, t: tuple, proposal_type: int) -> OwnerProposal:
        """Build from the raw tuple returned by getOwnerProposal().

        proposal_type must be fetched separately (not included in the view return).
        """
        (
            proposed_owner,
            executed,
            canceled,
            confirmations,
            rejections,
            expiry,
            created_at,
        ) = t
        if canceled:
            status = TxStatus.CANCELED
        elif executed:
            status = TxStatus.EXECUTED
        else:
            status = TxStatus.PENDING
        return cls(
            proposed_owner=proposed_owner,
            status=status,
            proposal_type=ProposalType(proposal_type),
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