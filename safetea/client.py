from typing import List, Optional
from web3 import Web3
from .factory import SafeTeaFactory

class SafeTeaClient:
    def __init__(self, rpc_url: str, factory_address: str) -> None:
        """Initialize the SafeTeaClient.

        Args:
            rpc_url (str): The RPC URL (HTTP) of the Blockchain node to connect to.
            factory_address (str): The address of the SafeTea factory contract.
        """
        self.rpc_url = rpc_url
        self.factory_address = factory_address
        self.factory = SafeTeaFactory(rpc_url, factory_address)