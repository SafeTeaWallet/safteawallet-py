import pytest
from unittest.mock import MagicMock
from web3 import Web3
from safteawallet_py.wallet import SafeTeaWallet
from safteawallet_py.exceptions import SafeTeaError, NotOwnerError, ProposalNotFoundError

@pytest.fixture
def mock_web3():
    web3 = MagicMock()
    web3.to_checksum_address.side_effect = lambda x: Web3.to_checksum_address(x)
    web3.eth = MagicMock()
    return web3

@pytest.fixture
def mock_account():
    account = MagicMock()
    account.address = Web3.to_checksum_address("0x" + "1" * 40)
    return account

@pytest.fixture
def wallet(mock_web3, mock_account):
    wallet_addr = Web3.to_checksum_address("0x" + "2" * 40)
    mock_contract = MagicMock()
    mock_web3.eth.contract.return_value = mock_contract
    
    w = SafeTeaWallet(mock_web3, wallet_addr, mock_account)
    
    # Mocking is_owner to bypass require_owner
    w.wallet_contract.functions.getOwners.return_value.call.return_value = [mock_account.address]
    
    return w

def test_get_info(wallet):
    wallet.wallet_contract.functions.getInfo.return_value.call.return_value = [
        [wallet.account.address], # owners
        2 # threshold
    ]
    
    info = wallet.get_info()
    assert info.address == wallet.wallet_address
    assert info.owners == [wallet.account.address]
    assert info.threshold == 2

def test_get_transaction_count(wallet):
    wallet.wallet_contract.functions.getTransactionCount.return_value.call.return_value = 5
    count = wallet.get_transaction_count()
    assert count == 5

def test_submit_transaction(wallet):
    wallet.wallet_contract.functions.submitTransaction.return_value.estimate_gas.return_value = 100000
    wallet.wallet_contract.functions.submitTransaction.return_value.build_transaction.return_value = {"from": wallet.account.address}
    
    wallet.account.sign_transaction.return_value.raw_transaction = b"signed"
    wallet.web3.eth.send_raw_transaction.return_value = b"txhash"
    
    mock_receipt = MagicMock()
    wallet.web3.eth.wait_for_transaction_receipt.return_value = mock_receipt
    
    mock_event = [{"args": {"txIndex": 1}}]
    wallet.wallet_contract.events.TransactionSubmitted.return_value.process_receipt.return_value = mock_event
    
    tx_index = wallet.submit_transaction(Web3.to_checksum_address("0x" + "3" * 40), 100)
    assert tx_index == 1

def test_propose_add_owner(wallet):
    wallet.wallet_contract.functions.proposeOwner.return_value.estimate_gas.return_value = 100000
    wallet.wallet_contract.functions.proposeOwner.return_value.build_transaction.return_value = {"from": wallet.account.address}
    
    wallet.account.sign_transaction.return_value.raw_transaction = b"signed"
    wallet.web3.eth.send_raw_transaction.return_value = b"txhash"
    
    tx_hash = wallet.propose_add_owner(Web3.to_checksum_address("0x" + "3" * 40))
    assert tx_hash == b"txhash".hex()

def test_confirm_owner_proposal_not_found(wallet):
    wallet.wallet_contract.functions.getOwnerProposalCount.return_value.call.return_value = 0
    with pytest.raises(ProposalNotFoundError):
        wallet.confirm_owner_proposal(0)

def test_get_owners_error(wallet):
    wallet.wallet_contract.functions.getOwners.return_value.call.side_effect = Exception("error")
    with pytest.raises(SafeTeaError):
        wallet.get_owners()
