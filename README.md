# SafeTea

SafeTea is a Python SDK for interacting with SafeTea Multi-Signature Wallets on Ethereum-compatible networks.

It provides a simple and modular interface to create new multi-signature wallets, manage transaction proposals, and execute approved transactions.

## Installation

Install the package via pip:

```bash
pip install safteawallet-py
```

## Usage

### Connecting and Initializing the Client

To interact with SafeTea contracts, initialize the `SafeTeaClient` using a Web3 instance and your private key.

```python
from web3 import Web3
from safteawallet_py.client import SafeTeaClient

# Initialize the SafeTea client
private_key = "0x..."
client = SafeTeaClient(rpc_url="https://your.rpc.endpoint", factory_address="0xYourFactoryAddress", private_key=private_key)
```

### Creating a New Multi-Signature Wallet

You can deploy a new SafeTea wallet by specifying the owners. A minimum of two owners is required.

```python
# Assuming the factory is already deployed at this address
factory_address = "0xYourFactoryAddress"
factory = client.get_factory(factory_address)

owners = [
    "0xOwnerAddress1",
    "0xOwnerAddress2",
    "0xOwnerAddress3"
]

result = factory.create_wallet(owners)
print(f"New Wallet Address: {result.wallet_address}")
print(f"Transaction Hash: {result.transaction_hash}")
```

### Proposing a Transaction

Once a wallet is deployed, any owner can submit a transaction proposal.

```python
wallet_address = "0xYourWalletAddress"
wallet = client.get_wallet(wallet_address)

# Submit a transaction (e.g., sending 1 ETH)
to_address = "0xRecipientAddress"
value_in_wei = w3.to_wei(1, "ether")
data = b""

# The expiry is defined as a Unix timestamp
expiry_timestamp = w3.eth.get_block("latest")["timestamp"] + 86400 # 24 hours

tx_index = wallet.submit_transaction(to_address, value_in_wei, data, expiry_timestamp)
print(f"Transaction submitted with index: {tx_index}")
```

### Confirming a Transaction

Other owners can review and confirm pending transactions. Once the confirmation threshold is reached, the transaction executes automatically.

```python
# Assuming you are initialized as another owner
tx_index = 0
wallet.confirm_transaction(tx_index)
print(f"Transaction {tx_index} confirmed.")
```

### Managing Owners

Owners can propose adding or removing participants.

```python
new_owner = "0xNewOwnerAddress"
expiry_timestamp = w3.eth.get_block("latest")["timestamp"] + 86400

# Propose a new owner
wallet.propose_add_owner(new_owner, expiry_timestamp)

# Other owners can confirm this proposal
proposal_index = 0
wallet.confirm_owner_proposal(proposal_index)
```

## Development

To run the test suite, ensure dependencies are installed and execute:

```bash
pytest tests/
```

## License

This project is open-source and available under the MIT License.
