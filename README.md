# safteawallet-py

SafteaWallet-Py is a Python SDK for interacting with SafeTea Multi-Signature Wallets on Ethereum-compatible networks.

It provides a simple and modular interface to create new multi-signature wallets, manage transaction proposals, and execute approved transactions. Both synchronous and asynchronous interfaces are available.

## Installation

Install the package via pip:

```bash
pip install safteawallet-py
```

## Usage

### Sync vs Async

| | Sync | Async |
|---|---|---|
| Import | `safteawallet_py` | `safteawallet_py.aio` |
| Client | `SafeTeaClient` | `AsyncSafeTeaClient` |
| Usage | Regular calls | `await` all methods |

---

## Synchronous API

### Connecting and Initializing the Client

```python
from safteawallet_py.client import SafeTeaClient

client = SafeTeaClient(
    rpc_url="https://your.rpc.endpoint",
    factory_address="0xYourFactoryAddress",
    private_key="0x...",
)
```

### Creating a New Multi-Signature Wallet

A minimum of two owners is required.

```python
owners = [
    "0xOwnerAddress1",
    "0xOwnerAddress2",
    "0xOwnerAddress3",
]

result = client.factory.create_wallet(owners)
print(f"Wallet: {result.wallet_address}")
print(f"Tx hash: {result.transaction_hash}")
```

### Proposing a Transaction

```python
wallet = client.wallet("0xYourWalletAddress")

expiry = w3.eth.get_block("latest")["timestamp"] + 86400  # 24 hours

tx_index = wallet.submit_transaction(
    to="0xRecipientAddress",
    value=w3.to_wei(1, "ether"),
    data=b"",
    expiry=expiry,
)
print(f"Submitted at index: {tx_index}")
```

### Confirming / Rejecting a Transaction

```python
wallet.confirm_transaction(tx_index)
wallet.reject_transaction(tx_index)
```

### Managing Owners

```python
expiry = w3.eth.get_block("latest")["timestamp"] + 86400

wallet.propose_add_owner("0xNewOwnerAddress", expiry)
wallet.propose_remove_owner("0xOwnerToRemove", expiry)

wallet.confirm_owner_proposal(proposal_index)
wallet.reject_owner_proposal(proposal_index)
```

---

## Async API (`safteawallet_py.aio`)

The async module mirrors the sync API but every method is a coroutine. Use it with `asyncio` or any async framework (FastAPI, aiohttp, etc.).

### Client

```python
from safteawallet_py.aio import AsyncSafeTeaClient

client = AsyncSafeTeaClient(
    rpc_url="https://your.rpc.endpoint",
    factory_address="0xYourFactoryAddress",
    private_key="0x...",          # optional — omit for read-only use
)
```

`AsyncSafeTeaClient` exposes two attributes after construction:

- `client.factory` — an `AsyncSafeTeaFactory` instance
- `client.account` — the `LocalAccount` derived from `private_key`, or `None`

#### Check connection

```python
await client.check_connection()   # raises ConnectionError if unreachable
```

#### Get a wallet instance

```python
wallet = client.wallet("0xYourWalletAddress")  # returns AsyncSafeTeaWallet
```

---

### Factory — `AsyncSafeTeaFactory`

#### Create a wallet

```python
from safteawallet_py.aio import AsyncSafeTeaClient

client = AsyncSafeTeaClient(rpc_url=..., factory_address=..., private_key=...)

owners = ["0xOwner1", "0xOwner2", "0xOwner3"]  # minimum 2
result = await client.factory.create_wallet(owners)

print(result.wallet_address)    # checksummed address of the new wallet
print(result.transaction_hash)  # hex tx hash
```

Raises `ValueError` if fewer than 2 owners are provided.

#### Get wallets for a user

```python
wallets = await client.factory.get_user_wallets("0xUserAddress")
# returns List[ChecksumAddress]
```

---

### Wallet — `AsyncSafeTeaWallet`

Obtain a wallet instance via `client.wallet(address)` or construct directly:

```python
from safteawallet_py.aio.wallet import AsyncSafeTeaWallet

wallet = AsyncSafeTeaWallet(web3=client.web3, wallet_address="0x...", account=client.account)
```

All write methods require the `account` to be one of the wallet's owners, otherwise `NotOwnerError` is raised.

---

#### Info

```python
# Full wallet snapshot
info = await wallet.get_info()
# info.address    — wallet address
# info.owners     — list of owner addresses
# info.threshold  — majority threshold (votes needed to execute)

# Individual getters
owners    = await wallet.get_owners()     # List[ChecksumAddress]
threshold = await wallet.get_threshold()  # int
```

---

#### Transactions

```python
# Submit a new proposal
expiry = int(time.time()) + 3600   # unix timestamp, must be within 30 days

tx_index = await wallet.submit_transaction(
    to="0xRecipientAddress",
    value=1_000_000_000_000_000_000,  # wei
    data=b"",                          # optional calldata
    expiry=expiry,                     # optional, default 3600s from now
)

# Confirm or reject
await wallet.confirm_transaction(tx_index)
await wallet.reject_transaction(tx_index)

# Read
count = await wallet.get_transaction_count()   # int
tx    = await wallet.get_transaction(tx_index) # Transaction dataclass
```

`Transaction` fields:

| Field | Type | Description |
|---|---|---|
| `to` | `str` | Recipient address |
| `value` | `int` | Value in wei |
| `data` | `bytes` | Calldata |
| `status` | `TxStatus` | `PENDING`, `EXECUTED`, or `CANCELED` |
| `confirmations` | `int` | Confirmation vote count |
| `rejections` | `int` | Rejection vote count |
| `expiry` | `int` | Unix timestamp |
| `created_at` | `int` | Unix timestamp |

`confirm_transaction` and `reject_transaction` validate state before sending and raise:

- `SafeTeaError` — if already executed or canceled
- `AlreadyVotedError` — if the caller already voted
- `TransactionExpiredError` — if the proposal has expired

---

#### Owner proposals

```python
expiry = int(time.time()) + 3600

# Propose changes
await wallet.propose_add_owner("0xNewOwner", expiry)
await wallet.propose_remove_owner("0xOwnerToRemove", expiry)

# Vote on a proposal
await wallet.confirm_owner_proposal(proposal_index)
await wallet.reject_owner_proposal(proposal_index)

# Read
count    = await wallet.get_owner_proposal_count()      # int
proposal = await wallet.get_owner_proposal(index)       # OwnerProposal dataclass
```

`OwnerProposal` fields:

| Field | Type | Description |
|---|---|---|
| `proposed_owner` | `str` | Address being added or removed |
| `proposal_type` | `ProposalType` | `ADD` or `REMOVE` |
| `status` | `TxStatus` | `PENDING`, `EXECUTED`, or `CANCELED` |
| `confirmations` | `int` | Confirmation vote count |
| `rejections` | `int` | Rejection vote count |
| `expiry` | `int` | Unix timestamp |
| `created_at` | `int` | Unix timestamp |

`confirm_owner_proposal` and `reject_owner_proposal` raise `ProposalNotFoundError` if the index is out of range.

---

### Full async example

```python
import asyncio
from safteawallet_py.aio import AsyncSafeTeaClient

async def main():
    client = AsyncSafeTeaClient(
        rpc_url="https://your.rpc.endpoint",
        factory_address="0xFactoryAddress",
        private_key="0xYourPrivateKey",
    )

    await client.check_connection()

    # Deploy a new wallet
    result = await client.factory.create_wallet([
        "0xOwner1",
        "0xOwner2",
    ])
    print("Wallet deployed:", result.wallet_address)

    wallet = client.wallet(result.wallet_address)

    # Submit a transaction
    import time
    tx_index = await wallet.submit_transaction(
        to="0xRecipient",
        value=10 ** 18,   # 1 ETH in wei
        expiry=int(time.time()) + 3600,
    )
    print("Submitted tx index:", tx_index)

    # Second owner confirms
    client2 = AsyncSafeTeaClient(
        rpc_url="https://your.rpc.endpoint",
        factory_address="0xFactoryAddress",
        private_key="0xOwner2PrivateKey",
    )
    wallet2 = client2.wallet(result.wallet_address)
    await wallet2.confirm_transaction(tx_index)
    print("Transaction confirmed and executed.")

asyncio.run(main())
```

---

## Exceptions

| Exception | Description |
|---|---|
| `SafeTeaError` | Base exception for all SDK errors |
| `NotOwnerError` | Caller is not a wallet owner |
| `AlreadyVotedError` | Caller already voted on this proposal |
| `TransactionExpiredError` | Proposal has passed its expiry timestamp |
| `ProposalNotFoundError` | Owner proposal index does not exist |
| `ConfigurationError` | Client misconfigured (e.g. write op without a signer) |

---

## Development

To run the test suite:

```bash
pytest tests/
```

## License

This project is open-source and available under the MIT License.
