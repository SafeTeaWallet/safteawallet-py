import pytest
from unittest.mock import MagicMock
from web3 import Web3

from safteawallet_py.erc20_manager import ERC20Manager
from safteawallet_py.exceptions import SafeTeaError

OWNER_ADDR = Web3.to_checksum_address("0x" + "1" * 40)
WALLET_ADDR = Web3.to_checksum_address("0x" + "2" * 40)
TOKEN_ADDR = Web3.to_checksum_address("0x" + "3" * 40)
SPENDER_ADDR = Web3.to_checksum_address("0x" + "4" * 40)
RECIPIENT_ADDR = Web3.to_checksum_address("0x" + "5" * 40)


@pytest.fixture
def mock_web3():
    web3 = MagicMock()
    web3.to_checksum_address.side_effect = lambda x: Web3.to_checksum_address(x)
    web3.eth = MagicMock()
    return web3


@pytest.fixture
def mock_account():
    account = MagicMock()
    account.address = OWNER_ADDR
    return account


@pytest.fixture
def mock_wallet():
    wallet = MagicMock()
    return wallet


@pytest.fixture
def manager(mock_web3, mock_account, mock_wallet):
    mock_token_contract = MagicMock()
    mock_web3.eth.contract.return_value = mock_token_contract

    mgr = ERC20Manager(
        web3=mock_web3,
        token_address=TOKEN_ADDR,
        wallet_address=WALLET_ADDR,
        account=mock_account,
        wallet=mock_wallet,
    )
    return mgr


# ── read helpers ──────────────────────────────────────────────────────────────

def test_name_success(manager):
    manager.token_contract.functions.name.return_value.call.return_value = "MyToken"
    assert manager.name() == "MyToken"


def test_name_error(manager):
    manager.token_contract.functions.name.return_value.call.side_effect = Exception("rpc error")
    with pytest.raises(SafeTeaError, match="Error fetching token name"):
        manager.name()


def test_symbol_success(manager):
    manager.token_contract.functions.symbol.return_value.call.return_value = "MTK"
    assert manager.symbol() == "MTK"


def test_symbol_error(manager):
    manager.token_contract.functions.symbol.return_value.call.side_effect = Exception("fail")
    with pytest.raises(SafeTeaError, match="Error fetching token symbol"):
        manager.symbol()


def test_decimals_success(manager):
    manager.token_contract.functions.decimals.return_value.call.return_value = 18
    assert manager.decimals() == 18


def test_decimals_error(manager):
    manager.token_contract.functions.decimals.return_value.call.side_effect = Exception("fail")
    with pytest.raises(SafeTeaError, match="Error fetching token decimals"):
        manager.decimals()


def test_total_supply_success(manager):
    manager.token_contract.functions.totalSupply.return_value.call.return_value = 1_000_000 * 10**18
    assert manager.total_supply() == 1_000_000 * 10**18


def test_total_supply_error(manager):
    manager.token_contract.functions.totalSupply.return_value.call.side_effect = Exception("fail")
    with pytest.raises(SafeTeaError, match="Error fetching total supply"):
        manager.total_supply()


def test_balance_of_success(manager):
    manager.token_contract.functions.balanceOf.return_value.call.return_value = 500 * 10**18
    assert manager.balance_of(OWNER_ADDR) == 500 * 10**18


def test_balance_of_error(manager):
    manager.token_contract.functions.balanceOf.return_value.call.side_effect = Exception("fail")
    with pytest.raises(SafeTeaError, match="Error fetching balance"):
        manager.balance_of(OWNER_ADDR)


def test_wallet_balance_uses_wallet_address(manager):
    manager.token_contract.functions.balanceOf.return_value.call.return_value = 250 * 10**18
    result = manager.wallet_balance()
    assert result == 250 * 10**18
    manager.token_contract.functions.balanceOf.assert_called_with(WALLET_ADDR)


def test_allowance_success(manager):
    manager.token_contract.functions.allowance.return_value.call.return_value = 100 * 10**18
    assert manager.allowance(WALLET_ADDR, SPENDER_ADDR) == 100 * 10**18


def test_allowance_error(manager):
    manager.token_contract.functions.allowance.return_value.call.side_effect = Exception("fail")
    with pytest.raises(SafeTeaError, match="Error fetching allowance"):
        manager.allowance(WALLET_ADDR, SPENDER_ADDR)


# ── write helpers ─────────────────────────────────────────────────────────────

def test_transfer_success(manager, mock_wallet):
    manager.token_contract.encode_abi.return_value = b"transfer_data"
    mock_wallet.submit_transaction.return_value = 0

    tx_index = manager.transfer(RECIPIENT_ADDR, 100 * 10**18)

    assert tx_index == 0
    manager.token_contract.encode_abi.assert_called_once_with(
        "transfer", args=[RECIPIENT_ADDR, 100 * 10**18]
    )
    mock_wallet.submit_transaction.assert_called_once_with(
        to=TOKEN_ADDR, value=0, data=b"transfer_data", expiry=3600
    )


def test_transfer_custom_expiry(manager, mock_wallet):
    manager.token_contract.encode_abi.return_value = b"transfer_data"
    mock_wallet.submit_transaction.return_value = 1

    tx_index = manager.transfer(RECIPIENT_ADDR, 50 * 10**18, expiry=7200)

    assert tx_index == 1
    mock_wallet.submit_transaction.assert_called_once_with(
        to=TOKEN_ADDR, value=0, data=b"transfer_data", expiry=7200
    )


def test_transfer_error(manager, mock_wallet):
    manager.token_contract.encode_abi.return_value = b"transfer_data"
    mock_wallet.submit_transaction.side_effect = Exception("wallet error")

    with pytest.raises(SafeTeaError, match="Error submitting token transfer"):
        manager.transfer(RECIPIENT_ADDR, 100 * 10**18)


def test_approve_success(manager, mock_wallet):
    manager.token_contract.encode_abi.return_value = b"approve_data"
    mock_wallet.submit_transaction.return_value = 2

    tx_index = manager.approve(SPENDER_ADDR, 200 * 10**18)

    assert tx_index == 2
    manager.token_contract.encode_abi.assert_called_once_with(
        "approve", args=[SPENDER_ADDR, 200 * 10**18]
    )
    mock_wallet.submit_transaction.assert_called_once_with(
        to=TOKEN_ADDR, value=0, data=b"approve_data", expiry=3600
    )


def test_approve_error(manager, mock_wallet):
    manager.token_contract.encode_abi.return_value = b"approve_data"
    mock_wallet.submit_transaction.side_effect = Exception("wallet error")

    with pytest.raises(SafeTeaError, match="Error submitting token approval"):
        manager.approve(SPENDER_ADDR, 200 * 10**18)


def test_transfer_from_success(manager, mock_wallet):
    manager.token_contract.encode_abi.return_value = b"transferfrom_data"
    mock_wallet.submit_transaction.return_value = 3

    tx_index = manager.transfer_from(OWNER_ADDR, RECIPIENT_ADDR, 75 * 10**18)

    assert tx_index == 3
    manager.token_contract.encode_abi.assert_called_once_with(
        "transferFrom", args=[OWNER_ADDR, RECIPIENT_ADDR, 75 * 10**18]
    )
    mock_wallet.submit_transaction.assert_called_once_with(
        to=TOKEN_ADDR, value=0, data=b"transferfrom_data", expiry=3600
    )


def test_transfer_from_error(manager, mock_wallet):
    manager.token_contract.encode_abi.return_value = b"transferfrom_data"
    mock_wallet.submit_transaction.side_effect = Exception("wallet error")

    with pytest.raises(SafeTeaError, match="Error submitting transferFrom"):
        manager.transfer_from(OWNER_ADDR, RECIPIENT_ADDR, 75 * 10**18)


# ── client integration ────────────────────────────────────────────────────────

def test_client_erc20_returns_manager():
    from safteawallet_py.client import SafeTeaClient

    client = MagicMock(spec=SafeTeaClient)
    client.erc20.return_value = MagicMock(spec=ERC20Manager)

    mgr = client.erc20(TOKEN_ADDR, WALLET_ADDR)
    assert isinstance(mgr, ERC20Manager)
    client.erc20.assert_called_once_with(TOKEN_ADDR, WALLET_ADDR)
