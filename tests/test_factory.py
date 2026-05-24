import pytest
from unittest.mock import MagicMock
from web3 import Web3
from safteawallet_py.factory import SafeTeaFactory
from safteawallet_py.exceptions import SafeTeaError

@pytest.fixture
def mock_web3():
    web3 = MagicMock()
    web3.to_checksum_address.side_effect = lambda x: Web3.to_checksum_address(x)
    web3.eth = MagicMock()
    return web3

@pytest.fixture
def mock_account():
    account = MagicMock()
    account.address = "0x" + "1" * 40
    account.key = b"fake_key"
    return account

@pytest.fixture
def factory(mock_web3, mock_account):
    factory_addr = Web3.to_checksum_address("0x" + "2" * 40)
    # mock eth.contract
    mock_contract = MagicMock()
    mock_web3.eth.contract.return_value = mock_contract
    
    fac = SafeTeaFactory(mock_web3, factory_addr, mock_account)
    fac.factory_contract = mock_contract
    return fac

def test_create_wallet_success(factory, mock_web3):
    owners = [Web3.to_checksum_address("0x" + "3" * 40), Web3.to_checksum_address("0x" + "4" * 40)]
    
    mock_tx = {"from": factory.account.address, "nonce": 0, "gas": 4000000, "gasPrice": 1000000000}
    factory.factory_contract.functions.createWallet.return_value.estimate_gas.return_value = 4000000
    factory.factory_contract.functions.createWallet.return_value.build_transaction.return_value = mock_tx
    
    mock_signed_tx = MagicMock()
    mock_signed_tx.raw_transaction = b"signed"
    mock_web3.eth.account.sign_transaction.return_value = mock_signed_tx
    
    mock_web3.eth.send_raw_transaction.return_value = b"txhash"
    
    mock_receipt = MagicMock()
    mock_receipt.status = 1
    mock_web3.eth.wait_for_transaction_receipt.return_value = mock_receipt
    
    mock_event = [{"args": {"wallet": Web3.to_checksum_address("0x" + "5" * 40)}}]
    factory.factory_contract.events.WalletCreated.return_value.process_receipt.return_value = mock_event
    
    result = factory.create_wallet(owners)
    
    assert result.wallet_address == Web3.to_checksum_address("0x" + "5" * 40)
    assert result.transaction_hash == b"txhash".hex()

def test_create_wallet_requires_two_owners(factory):
    with pytest.raises(ValueError, match="At least 2 owners are required"):
        factory.create_wallet([Web3.to_checksum_address("0x" + "3" * 40)])

def test_get_user_wallets_success(factory):
    user = Web3.to_checksum_address("0x" + "3" * 40)
    expected_wallets = [Web3.to_checksum_address("0x" + "5" * 40)]
    
    factory.factory_contract.functions.getUserWallets.return_value.call.return_value = expected_wallets
    
    wallets = factory.get_user_wallets(user)
    assert wallets == expected_wallets

def test_get_user_wallets_failure(factory):
    user = Web3.to_checksum_address("0x" + "3" * 40)
    factory.factory_contract.functions.getUserWallets.return_value.call.side_effect = Exception("Contract revert")
    
    with pytest.raises(SafeTeaError, match="Error getting user wallets"):
        factory.get_user_wallets(user)
