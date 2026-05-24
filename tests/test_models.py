import pytest
from safetea.models import Transaction, TxStatus, OwnerProposal, ProposalType

def test_transaction_from_tuple():
    t = (
        "0x" + "1"*40,  # to
        1000,           # value
        b"data",        # data
        False,          # executed
        False,          # canceled
        1,              # confirmations
        0,              # rejections
        999999999,      # expiry
        888888888       # created_at
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
        "0x" + "1"*40,
        1000,
        b"data",
        True,  # executed
        False, # canceled
        2,
        0,
        999999999,
        888888888
    )
    
    tx = Transaction.from_tuple(t)
    assert tx.status == TxStatus.EXECUTED
    assert tx.is_executed is True

def test_owner_proposal_from_tuple():
    t = (
        "0x" + "2"*40,  # proposed_owner
        False,          # executed
        True,           # canceled
        0,              # confirmations
        2,              # rejections
        999999999,      # expiry
        888888888       # created_at
    )
    
    proposal = OwnerProposal.from_tuple(t, 0)
    assert proposal.proposed_owner == "0x" + "2"*40
    assert proposal.status == TxStatus.CANCELED
    assert proposal.proposal_type == ProposalType.ADD
    assert proposal.is_canceled is True
