import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from web3 import Web3
from safteawallet_py.aio.wallet import AsyncSafeTeaWallet
from safteawallet_py.exceptions import SafeTeaError, NotOwnerError, ProposalNotFoundError, AlreadyVotedError, TransactionExpiredError
from safteawallet_py.models import Transaction, TxStatus, OwnerProposal, ProposalType


OWNER_ADDR = Web3.to_checksum_address("0x" + "1" * 40)
WALLET_ADDR = Web3.to_checksum_address("0x" + "2" * 40)
OTHER_ADDR = Web3.to_checksum_address("0x" + "3" * 40)


@pytest.fixture
def mock_web3():
    web3 = MagicMock()
    web3.to_checksum_address.side_effect = lambda x: Web3.to_checksum_address(x)
    web3.eth = MagicMock()
    web3.eth.get_block = AsyncMock(return_value={"timestamp": 9999999999})
    web3.eth.get_transaction_count = AsyncMock(return_value=0)
    web3.eth.send_raw_transaction = AsyncMock(return_value=b"txhash")
    web3.eth.wait_for_transaction_receipt = AsyncMock(return_value=MagicMock())

    gas_price_mock = AsyncMock(return_value=1000000000)
    type(web3.eth).gas_price = PropertyMock(side_effect=lambda: gas_price_mock())
    return web3


@pytest.fixture
def mock_account():
    account = MagicMock()
    account.address = OWNER_ADDR
    account.sign_transaction.return_value.raw_transaction = b"signed"
    return account


@pytest.fixture
def aio_wallet(mock_web3, mock_account):
    mock_contract = MagicMock()
    mock_web3.eth.contract.return_value = mock_contract

    w = AsyncSafeTeaWallet(mock_web3, WALLET_ADDR, mock_account)
    # Default: caller is an owner
    w.wallet_contract.functions.getOwners.return_value.call = AsyncMock(return_value=[OWNER_ADDR])
    return w


# ── info_manager ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_info_success(aio_wallet):
    aio_wallet.wallet_contract.functions.getInfo.return_value.call = AsyncMock(
        return_value=[[OWNER_ADDR], 2]
    )
    info = await aio_wallet.get_info()
    assert info.address == WALLET_ADDR
    assert info.owners == [OWNER_ADDR]
    assert info.threshold == 2


@pytest.mark.asyncio
async def test_get_info_error(aio_wallet):
    aio_wallet.wallet_contract.functions.getInfo.return_value.call = AsyncMock(
        side_effect=Exception("rpc error")
    )
    with pytest.raises(SafeTeaError, match="Error getting wallet info"):
        await aio_wallet.get_info()


@pytest.mark.asyncio
async def test_get_owners_success(aio_wallet):
    owners = await aio_wallet.get_owners()
    assert owners == [OWNER_ADDR]


@pytest.mark.asyncio
async def test_get_owners_error(aio_wallet):
    aio_wallet.wallet_contract.functions.getOwners.return_value.call = AsyncMock(
        side_effect=Exception("error")
    )
    with pytest.raises(SafeTeaError, match="Error getting owners"):
        await aio_wallet.get_owners()


@pytest.mark.asyncio
async def test_get_threshold_success(aio_wallet):
    aio_wallet.wallet_contract.functions.getMajorityThreshold.return_value.call = AsyncMock(return_value=2)
    threshold = await aio_wallet.get_threshold()
    assert threshold == 2


@pytest.mark.asyncio
async def test_get_threshold_error(aio_wallet):
    aio_wallet.wallet_contract.functions.getMajorityThreshold.return_value.call = AsyncMock(
        side_effect=Exception("fail")
    )
    with pytest.raises(SafeTeaError, match="Error getting threshold"):
        await aio_wallet.get_threshold()


# ── transaction_manager ───────────────────────────────────────────────────────

@pytest.fixture
def pending_tx():
    return Transaction(
        to=OTHER_ADDR,
        value=100,
        data=b"",
        status=TxStatus.PENDING,
        confirmations=0,
        rejections=0,
        expiry=9999999999,
        created_at=0,
    )


@pytest.mark.asyncio
async def test_get_transaction_count_success(aio_wallet):
    aio_wallet.wallet_contract.functions.getTransactionCount.return_value.call = AsyncMock(return_value=5)
    assert await aio_wallet.get_transaction_count() == 5


@pytest.mark.asyncio
async def test_get_transaction_count_error(aio_wallet):
    aio_wallet.wallet_contract.functions.getTransactionCount.return_value.call = AsyncMock(
        side_effect=Exception("fail")
    )
    with pytest.raises(SafeTeaError, match="Error getting transaction count"):
        await aio_wallet.get_transaction_count()


@pytest.mark.asyncio
async def test_get_transaction_success(aio_wallet):
    # (index, to, value, data, status, isExpired, confirmations, rejections, expiry, createdAt)
    raw = (0, OTHER_ADDR, 100, b"", 0, False, 0, 0, 9999999999, 0)
    aio_wallet.wallet_contract.functions.getTransaction.return_value.call = AsyncMock(return_value=raw)
    tx = await aio_wallet.get_transaction(0)
    assert tx.to == OTHER_ADDR
    assert tx.value == 100
    assert tx.status == TxStatus.PENDING


@pytest.mark.asyncio
async def test_get_transaction_error(aio_wallet):
    aio_wallet.wallet_contract.functions.getTransaction.return_value.call = AsyncMock(
        side_effect=Exception("fail")
    )
    with pytest.raises(SafeTeaError, match="Error getting transaction"):
        await aio_wallet.get_transaction(0)


@pytest.mark.asyncio
async def test_submit_transaction_success(aio_wallet):
    fn = aio_wallet.wallet_contract.functions.submitTransaction.return_value
    fn.estimate_gas = AsyncMock(return_value=100000)
    fn.build_transaction = AsyncMock(return_value={"from": OWNER_ADDR, "nonce": 0})

    mock_receipt = MagicMock()
    aio_wallet.web3.eth.wait_for_transaction_receipt.return_value = mock_receipt
    aio_wallet.wallet_contract.events.TransactionSubmitted.return_value.process_receipt.return_value = [
        {"args": {"txIndex": 3}}
    ]

    tx_index = await aio_wallet.submit_transaction(OTHER_ADDR, 100)
    assert tx_index == 3


@pytest.mark.asyncio
async def test_submit_transaction_not_owner(aio_wallet):
    aio_wallet.wallet_contract.functions.getOwners.return_value.call = AsyncMock(return_value=[OTHER_ADDR])
    with pytest.raises(SafeTeaError):
        await aio_wallet.submit_transaction(OTHER_ADDR, 100)


@pytest.mark.asyncio
async def test_confirm_transaction_success(aio_wallet, pending_tx):
    # (index, to, value, data, status=0, isExpired, confirmations, rejections, expiry, createdAt)
    raw = (0, OTHER_ADDR, 100, b"", 0, False, 0, 0, 9999999999, 0)
    aio_wallet.wallet_contract.functions.getTransaction.return_value.call = AsyncMock(return_value=raw)
    aio_wallet.wallet_contract.functions.hasConfirmedTransaction.return_value.call = AsyncMock(return_value=False)
    aio_wallet.wallet_contract.functions.hasRejectedTransaction.return_value.call = AsyncMock(return_value=False)

    fn = aio_wallet.wallet_contract.functions.confirmTransaction.return_value
    fn.estimate_gas = AsyncMock(return_value=100000)
    fn.build_transaction = AsyncMock(return_value={"from": OWNER_ADDR, "nonce": 0})

    result = await aio_wallet.confirm_transaction(0)
    assert result == b"txhash".hex()


@pytest.mark.asyncio
async def test_confirm_transaction_already_executed(aio_wallet):
    raw = (0, OTHER_ADDR, 100, b"", 1, False, 0, 0, 9999999999, 0)  # status=1 executed
    aio_wallet.wallet_contract.functions.getTransaction.return_value.call = AsyncMock(return_value=raw)
    with pytest.raises(SafeTeaError, match="already been executed"):
        await aio_wallet.confirm_transaction(0)


@pytest.mark.asyncio
async def test_confirm_transaction_already_canceled(aio_wallet):
    raw = (0, OTHER_ADDR, 100, b"", 2, False, 0, 0, 9999999999, 0)  # status=2 canceled
    aio_wallet.wallet_contract.functions.getTransaction.return_value.call = AsyncMock(return_value=raw)
    with pytest.raises(SafeTeaError, match="been canceled"):
        await aio_wallet.confirm_transaction(0)


@pytest.mark.asyncio
async def test_confirm_transaction_already_voted(aio_wallet):
    raw = (0, OTHER_ADDR, 100, b"", 0, False, 1, 0, 9999999999, 0)
    aio_wallet.wallet_contract.functions.getTransaction.return_value.call = AsyncMock(return_value=raw)
    aio_wallet.wallet_contract.functions.hasConfirmedTransaction.return_value.call = AsyncMock(return_value=True)
    with pytest.raises(SafeTeaError, match="already confirmed"):
        await aio_wallet.confirm_transaction(0)


@pytest.mark.asyncio
async def test_confirm_transaction_expired(aio_wallet):
    raw = (0, OTHER_ADDR, 100, b"", 0, True, 0, 0, 1000, 0)  # expiry in the past
    aio_wallet.wallet_contract.functions.getTransaction.return_value.call = AsyncMock(return_value=raw)
    aio_wallet.wallet_contract.functions.hasConfirmedTransaction.return_value.call = AsyncMock(return_value=False)
    aio_wallet.wallet_contract.functions.hasRejectedTransaction.return_value.call = AsyncMock(return_value=False)
    aio_wallet.web3.eth.get_block.return_value = {"timestamp": 9999999999}
    with pytest.raises(SafeTeaError, match="expired"):
        await aio_wallet.confirm_transaction(0)


@pytest.mark.asyncio
async def test_reject_transaction_success(aio_wallet):
    raw = (0, OTHER_ADDR, 100, b"", 0, False, 0, 0, 9999999999, 0)
    aio_wallet.wallet_contract.functions.getTransaction.return_value.call = AsyncMock(return_value=raw)
    aio_wallet.wallet_contract.functions.hasConfirmedTransaction.return_value.call = AsyncMock(return_value=False)
    aio_wallet.wallet_contract.functions.hasRejectedTransaction.return_value.call = AsyncMock(return_value=False)

    fn = aio_wallet.wallet_contract.functions.rejectTransaction.return_value
    fn.estimate_gas = AsyncMock(return_value=100000)
    fn.build_transaction = AsyncMock(return_value={"from": OWNER_ADDR, "nonce": 0})

    result = await aio_wallet.reject_transaction(0)
    assert result == b"txhash".hex()


@pytest.mark.asyncio
async def test_reject_transaction_already_rejected(aio_wallet):
    raw = (0, OTHER_ADDR, 100, b"", 0, False, 0, 1, 9999999999, 0)
    aio_wallet.wallet_contract.functions.getTransaction.return_value.call = AsyncMock(return_value=raw)
    aio_wallet.wallet_contract.functions.hasConfirmedTransaction.return_value.call = AsyncMock(return_value=False)
    aio_wallet.wallet_contract.functions.hasRejectedTransaction.return_value.call = AsyncMock(return_value=True)
    with pytest.raises(SafeTeaError, match="already rejected"):
        await aio_wallet.reject_transaction(0)


# ── owner_manager ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_owner_proposal_count_success(aio_wallet):
    aio_wallet.wallet_contract.functions.getOwnerProposalCount.return_value.call = AsyncMock(return_value=3)
    assert await aio_wallet.get_owner_proposal_count() == 3


@pytest.mark.asyncio
async def test_get_owner_proposal_count_error(aio_wallet):
    aio_wallet.wallet_contract.functions.getOwnerProposalCount.return_value.call = AsyncMock(
        side_effect=Exception("fail")
    )
    with pytest.raises(SafeTeaError, match="Error getting owner proposal count"):
        await aio_wallet.get_owner_proposal_count()


@pytest.mark.asyncio
async def test_get_owner_proposal_success(aio_wallet):
    # (index, proposedOwner, proposalType=0 ADD, status=0 pending, isExpired, confirmations, rejections, expiry, createdAt)
    raw = (0, OTHER_ADDR, 0, 0, False, 0, 0, 9999999999, 0)
    aio_wallet.wallet_contract.functions.getOwnerProposal.return_value.call = AsyncMock(return_value=raw)
    proposal = await aio_wallet.get_owner_proposal(0)
    assert proposal.proposed_owner == OTHER_ADDR
    assert proposal.status == TxStatus.PENDING
    assert proposal.proposal_type == ProposalType.ADD


@pytest.mark.asyncio
async def test_get_owner_proposal_error(aio_wallet):
    aio_wallet.wallet_contract.functions.getOwnerProposal.return_value.call = AsyncMock(
        side_effect=Exception("fail")
    )
    with pytest.raises(SafeTeaError, match="Error getting owner proposal"):
        await aio_wallet.get_owner_proposal(0)


@pytest.mark.asyncio
async def test_propose_add_owner_success(aio_wallet):
    fn = aio_wallet.wallet_contract.functions.proposeOwner.return_value
    fn.estimate_gas = AsyncMock(return_value=100000)
    fn.build_transaction = AsyncMock(return_value={"from": OWNER_ADDR, "nonce": 0})

    result = await aio_wallet.propose_add_owner(OTHER_ADDR)
    assert result == b"txhash".hex()


@pytest.mark.asyncio
async def test_propose_remove_owner_success(aio_wallet):
    fn = aio_wallet.wallet_contract.functions.proposeOwner.return_value
    fn.estimate_gas = AsyncMock(return_value=100000)
    fn.build_transaction = AsyncMock(return_value={"from": OWNER_ADDR, "nonce": 0})

    result = await aio_wallet.propose_remove_owner(OTHER_ADDR)
    assert result == b"txhash".hex()


@pytest.mark.asyncio
async def test_confirm_owner_proposal_success(aio_wallet):
    aio_wallet.wallet_contract.functions.getOwnerProposalCount.return_value.call = AsyncMock(return_value=2)

    fn = aio_wallet.wallet_contract.functions.confirmOwnerProposal.return_value
    fn.estimate_gas = AsyncMock(return_value=100000)
    fn.build_transaction = AsyncMock(return_value={"from": OWNER_ADDR, "nonce": 0})

    result = await aio_wallet.confirm_owner_proposal(0)
    assert result == b"txhash".hex()


@pytest.mark.asyncio
async def test_confirm_owner_proposal_not_found(aio_wallet):
    aio_wallet.wallet_contract.functions.getOwnerProposalCount.return_value.call = AsyncMock(return_value=0)
    with pytest.raises(ProposalNotFoundError):
        await aio_wallet.confirm_owner_proposal(0)


@pytest.mark.asyncio
async def test_reject_owner_proposal_success(aio_wallet):
    aio_wallet.wallet_contract.functions.getOwnerProposalCount.return_value.call = AsyncMock(return_value=2)

    fn = aio_wallet.wallet_contract.functions.rejectOwnerProposal.return_value
    fn.estimate_gas = AsyncMock(return_value=100000)
    fn.build_transaction = AsyncMock(return_value={"from": OWNER_ADDR, "nonce": 0})

    result = await aio_wallet.reject_owner_proposal(1)
    assert result == b"txhash".hex()


@pytest.mark.asyncio
async def test_reject_owner_proposal_not_found(aio_wallet):
    aio_wallet.wallet_contract.functions.getOwnerProposalCount.return_value.call = AsyncMock(return_value=1)
    with pytest.raises(ProposalNotFoundError):
        await aio_wallet.reject_owner_proposal(5)


# ── _build_and_send / _require_owner ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_require_owner_raises_when_not_owner(aio_wallet):
    aio_wallet.wallet_contract.functions.getOwners.return_value.call = AsyncMock(return_value=[OTHER_ADDR])
    with pytest.raises(NotOwnerError):
        await aio_wallet._require_owner()


@pytest.mark.asyncio
async def test_is_owner_true(aio_wallet):
    assert await aio_wallet._is_owner() is True


@pytest.mark.asyncio
async def test_is_owner_false(aio_wallet):
    aio_wallet.wallet_contract.functions.getOwners.return_value.call = AsyncMock(return_value=[OTHER_ADDR])
    assert await aio_wallet._is_owner() is False
