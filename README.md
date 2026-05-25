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

### ERC20 Token Operations

Get an `ERC20Manager` via `client.erc20(token_address, wallet_address)`.

```python
token = client.erc20("0xTokenAddress", "0xYourWalletAddress")
```

**Read operations** query the token contract directly:

```python
name     = token.name()
symbol   = token.symbol()
decimals = token.decimals()
supply   = token.total_supply()

# Balance of any address
balance = token.balance_of("0xSomeAddress")

# Shortcut — balance held by the wallet itself
wallet_balance = token.wallet_balance()

# Allowance
allowance = token.allowance("0xOwner", "0xSpender")
```

**Write operations** encode the ERC20 calldata and submit it through the wallet's multi-sig queue. They return the proposal `tx_index`, which owners then confirm or reject like any other transaction.

```python
import time
expiry = int(time.time()) + 3600

# Propose a token transfer from the wallet
tx_index = token.transfer("0xRecipient", 100 * 10**18, expiry=expiry)

# Propose an approval
tx_index = token.approve("0xSpender", 500 * 10**18, expiry=expiry)

# Propose a transferFrom
tx_index = token.transfer_from("0xFrom", "0xTo", 50 * 10**18, expiry=expiry)

# Owners vote on the proposal as usual
wallet = client.wallet("0xYourWalletAddress")
wallet.confirm_transaction(tx_index)
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

#### ERC20 token operations

Get an `AsyncERC20Manager` via `client.erc20(token_address, wallet_address)`.

```python
token = client.erc20("0xTokenAddress", "0xYourWalletAddress")
```

**Read operations** query the token contract directly:

```python
name     = await token.name()
symbol   = await token.symbol()
decimals = await token.decimals()
supply   = await token.total_supply()

# Balance of any address
balance = await token.balance_of("0xSomeAddress")

# Shortcut — balance held by the wallet itself
wallet_balance = await token.wallet_balance()

# Allowance
allowance = await token.allowance("0xOwner", "0xSpender")
```

**Write operations** encode the ERC20 calldata and submit it through the wallet's multi-sig queue. They return the proposal `tx_index`, which owners then confirm or reject like any other transaction.

```python
import time
expiry = int(time.time()) + 3600

# Propose a token transfer from the wallet
tx_index = await token.transfer("0xRecipient", 100 * 10**18, expiry=expiry)

# Propose an approval
tx_index = await token.approve("0xSpender", 500 * 10**18, expiry=expiry)

# Propose a transferFrom
tx_index = await token.transfer_from("0xFrom", "0xTo", 50 * 10**18, expiry=expiry)

# Owners vote on the proposal as usual
wallet = client.wallet("0xYourWalletAddress")
await wallet.confirm_transaction(tx_index)
```

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

### Full async ERC20 example

```python
import asyncio
import time
from safteawallet_py.aio import AsyncSafeTeaClient

async def main():
    client = AsyncSafeTeaClient(
        rpc_url="https://your.rpc.endpoint",
        factory_address="0xFactoryAddress",
        private_key="0xOwner1PrivateKey",
    )
    await client.check_connection()

    token = client.erc20("0xTokenAddress", "0xYourWalletAddress")

    # Read token info
    print(await token.name())
    print(await token.symbol())
    print(await token.decimals())
    print("Wallet balance:", await token.wallet_balance())

    # Propose a transfer — goes into the multi-sig queue
    expiry = int(time.time()) + 3600
    tx_index = await token.transfer("0xRecipient", 100 * 10**18, expiry=expiry)
    print("Transfer proposal submitted at index:", tx_index)

    # Second owner confirms
    client2 = AsyncSafeTeaClient(
        rpc_url="https://your.rpc.endpoint",
        factory_address="0xFactoryAddress",
        private_key="0xOwner2PrivateKey",
    )
    wallet2 = client2.wallet("0xYourWalletAddress")
    await wallet2.confirm_transaction(tx_index)
    print("Transfer confirmed and executed.")

asyncio.run(main())
```

---

## Exceptions

| Exception | Description |
|---|---|
| `SafeTeaError` | Base exception for all SDK errors (also wraps ERC20 operation errors) |
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
