import pytest
from safteawallet_py.models import Transaction, TxStatus, OwnerProposal, ProposalType

# TransactionView tuple: (index, to, value, data, status, isExpired, confirmations, rejections, expiry, createdAt)

def test_transaction_from_tuple():
    t = (
        0,               # index
        "0x" + "1"*40,  # to
        1000,            # value
        b"data",         # data
        0,               # status: PENDING
        False,           # isExpired
        1,               # confirmations
        0,               # rejections
        999999999,       # expiry
        888888888,       # created_at
    )

    tx = Transaction.from_tuple(t)
    assert tx.to == "0x" + "1"*40
    assert tx.value == 1000
    assert tx.data == b"data"
    assert tx.status == TxStatus.PENDING
    assert tx.confirmations == 1
    assert tx.rejections == 0
    assert tx.expiry == 999999999
    assert tx.created_at == 888888888
    assert tx.is_pending is True

def test_transaction_executed():
    t = (
        0,
        "0x" + "1"*40,
        1000,
        b"data",
        1,      # status: EXECUTED
        False,
        2,
        0,
        999999999,
        888888888,
    )

    tx = Transaction.from_tuple(t)
    assert tx.status == TxStatus.EXECUTED
    assert tx.is_executed is True

def test_transaction_canceled():
    t = (
        0,
        "0x" + "1"*40,
        1000,
        b"data",
        2,      # status: CANCELED
        False,
        0,
        2,
        999999999,
        888888888,
    )

    tx = Transaction.from_tuple(t)
    assert tx.status == TxStatus.CANCELED
    assert tx.is_canceled is True

# OwnerProposalView tuple: (index, proposedOwner, proposalType, status, isExpired, confirmations, rejections, expiry, createdAt)

def test_owner_proposal_from_tuple():
    t = (
        0,               # index
        "0x" + "2"*40,  # proposedOwner
        0,               # proposalType: ADD
        2,               # status: CANCELED
        False,           # isExpired
        0,               # confirmations
        2,               # rejections
        999999999,       # expiry
        888888888,       # created_at
    )

    proposal = OwnerProposal.from_tuple(t)
    assert proposal.proposed_owner == "0x" + "2"*40
    assert proposal.status == TxStatus.CANCELED
    assert proposal.proposal_type == ProposalType.ADD
    assert proposal.is_canceled is True

def test_owner_proposal_remove_pending():
    t = (
        1,
        "0x" + "3"*40,
        1,               # proposalType: REMOVE
        0,               # status: PENDING
        False,
        1,
        0,
        999999999,
        888888888,
    )

    proposal = OwnerProposal.from_tuple(t)
    assert proposal.proposal_type == ProposalType.REMOVE
    assert proposal.status == TxStatus.PENDING
    assert proposal.is_pending is True
