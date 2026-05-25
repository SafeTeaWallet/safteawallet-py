import pytest
from unittest.mock import MagicMock, AsyncMock, PropertyMock
from web3 import Web3
from safteawallet_py.aio.factory import AsyncSafeTeaFactory
from safteawallet_py.exceptions import SafeTeaError

@pytest.fixture
def mock_web3():
    web3 = MagicMock()
    web3.to_checksum_address.side_effect = lambda x: Web3.to_checksum_address(x)
    web3.eth = MagicMock()
    web3.eth.get_transaction_count = AsyncMock()
    web3.eth.send_raw_transaction = AsyncMock()
    web3.eth.wait_for_transaction_receipt = AsyncMock()
    
    # Mock gas_price as a coroutine that returns 1000000000
    gas_price_mock = AsyncMock(return_value=1000000000)
    type(web3.eth).gas_price = PropertyMock(side_effect=lambda: gas_price_mock())
    return web3

@pytest.fixture
def mock_account():
    account = MagicMock()
    account.address = Web3.to_checksum_address("0x" + "1" * 40)
    account.key = b"fake_key"
    return account

@pytest.fixture
def aio_factory(mock_web3, mock_account):
    factory_addr = Web3.to_checksum_address("0x" + "2" * 40)
    mock_contract = MagicMock()
    mock_web3.eth.contract.return_value = mock_contract
    
    fac = AsyncSafeTeaFactory(mock_web3, factory_addr, mock_account)
    fac.factory_contract = mock_contract
    return fac

@pytest.mark.asyncio
async def test_create_wallet_success(aio_factory, mock_web3):
    owners = [Web3.to_checksum_address("0x" + "3" * 40), Web3.to_checksum_address("0x" + "4" * 40)]
    
    mock_tx = {"from": aio_factory.account.address, "nonce": 0, "gas": 4000000, "gasPrice": 1000000000}
    
    aio_factory.factory_contract.functions.createWallet.return_value.estimate_gas = AsyncMock(return_value=4000000)
    aio_factory.factory_contract.functions.createWallet.return_value.build_transaction = AsyncMock(return_value=mock_tx)
    mock_web3.eth.get_transaction_count.return_value = 0
    
    mock_signed_tx = MagicMock()
    mock_signed_tx.raw_transaction = b"signed"
    mock_web3.eth.account.sign_transaction.return_value = mock_signed_tx
    
    mock_web3.eth.send_raw_transaction.return_value = b"txhash"
    
    mock_receipt = MagicMock()
    mock_receipt.status = 1
    mock_web3.eth.wait_for_transaction_receipt.return_value = mock_receipt
    
    mock_event = [{"args": {"wallet": Web3.to_checksum_address("0x" + "5" * 40)}}]
    aio_factory.factory_contract.events.WalletCreated.return_value.process_receipt.return_value = mock_event
    
    result = await aio_factory.create_wallet(owners)
    
    assert result.wallet_address == Web3.to_checksum_address("0x" + "5" * 40)
    assert result.transaction_hash == b"txhash".hex()

@pytest.mark.asyncio
async def test_create_wallet_requires_two_owners(aio_factory):
    with pytest.raises(ValueError, match="At least 2 owners are required"):
        await aio_factory.create_wallet([Web3.to_checksum_address("0x" + "3" * 40)])

@pytest.mark.asyncio
async def test_get_user_wallets_success(aio_factory):
    user = Web3.to_checksum_address("0x" + "3" * 40)
    expected_wallets = [Web3.to_checksum_address("0x" + "5" * 40)]
    
    aio_factory.factory_contract.functions.getUserWallets.return_value.call = AsyncMock(return_value=expected_wallets)
    
    wallets = await aio_factory.get_user_wallets(user)
    assert wallets == expected_wallets

@pytest.mark.asyncio
async def test_get_user_wallets_failure(aio_factory):
    user = Web3.to_checksum_address("0x" + "3" * 40)
    aio_factory.factory_contract.functions.getUserWallets.return_value.call = AsyncMock(side_effect=Exception("Contract revert"))
    
    with pytest.raises(SafeTeaError, match="Error getting user wallets"):
        await aio_factory.get_user_wallets(user)
