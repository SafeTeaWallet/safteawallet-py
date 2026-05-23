class SafeTeaError(Exception):
    """Base for all SDK errors."""

class ContractError(SafeTeaError):
    """Raised when the contract reverts. Subclasses map to Solidity custom errors."""
    revert_data: bytes

class NotOwnerError(ContractError): ...
class AlreadyVotedError(ContractError): ...
class TransactionExpiredError(ContractError): ...
class InsufficientConfirmationsError(ContractError): ...
class ProposalNotFoundError(ContractError): ...

class ConfigurationError(SafeTeaError):
    """Raised when the client is misconfigured (e.g. write op without a signer)."""

class ConnectionError(SafeTeaError):
    """Raised when the RPC endpoint is unreachable."""