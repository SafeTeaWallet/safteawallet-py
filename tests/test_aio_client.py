import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from web3 import Web3
from safteawallet_py.aio.client import AsyncSafeTeaClient
from safteawallet_py.aio.wallet import AsyncSafeTeaWallet
import safteawallet_py.exceptions as sdk_exceptions

FACTORY_ADDR = Web3.to_checksum_address("0x" + "2" * 40)
WALLET_ADDR = Web3.to_checksum_address("0x" + "3" * 40)
PRIVATE_KEY = "0x" + "a" * 64


def _make_client(private_key=None):
    """Build a client with all external dependencies patched."""
    with patch("safteawallet_py.aio.client.AsyncHTTPProvider"), \
         patch("safteawallet_py.aio.client.AsyncWeb3") as mock_w3_cls, \
         patch("safteawallet_py.aio.client.AsyncSafeTeaFactory"):

        mock_w3_cls.to_checksum_address.side_effect = Web3.to_checksum_address

        c = AsyncSafeTeaClient(
            rpc_url="http://localhost:8545",
            factory_address=FACTORY_ADDR,
            private_key=private_key,
        )

    # Replace web3 instance with a controllable mock after construction
    c.web3 = MagicMock()
    c.web3.is_connected = AsyncMock(return_value=True)
    c.web3.to_checksum_address.side_effect = Web3.to_checksum_address
    c.web3.eth = MagicMock()
    c.web3.eth.contract = MagicMock(return_value=MagicMock())
    return c


@pytest.fixture
def client():
    return _make_client(private_key=PRIVATE_KEY)


@pytest.fixture
def client_no_key():
    return _make_client()


@pytest.mark.asyncio
async def test_check_connection_success(client):
    await client.check_connection()  # should not raise


@pytest.mark.asyncio
async def test_check_connection_failure(client):
    client.web3.is_connected = AsyncMock(return_value=False)
    # client.py raises the builtin ConnectionError (not the SDK one)
    with pytest.raises(ConnectionError, match="Failed to connect"):
        await client.check_connection()


def test_wallet_returns_async_wallet_instance(client):
    wallet = client.wallet(WALLET_ADDR)
    assert isinstance(wallet, AsyncSafeTeaWallet)


def test_wallet_uses_client_account(client):
    wallet = client.wallet(WALLET_ADDR)
    assert wallet.account == client.account


def test_no_private_key_account_is_none(client_no_key):
    assert client_no_key.account is None


def test_with_private_key_account_is_set(client):
    assert client.account is not None


def test_factory_is_initialized(client):
    assert client.factory is not None


def test_factory_address_is_checksummed(client):
    assert client.factory_address == FACTORY_ADDR
