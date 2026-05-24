from safteawallet_py.client import SafeTeaClient
from safteawallet_py.exceptions import SafeTeaError
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    client = SafeTeaClient(
        rpc_url=os.getenv("RPC_URL"),
        factory_address=os.getenv("FACTORY_ADDRESS"),
        private_key=os.getenv("PRIVATE_KEY"),
    )
    
    wallets = client.factory.get_user_wallets(client.account.address)
    print("User Wallets:", wallets)
    
    
    # create a new wallet with the same owner
    result = client.factory.create_wallet([client.account.address, "0xEA7CD8779882802Aea420c57411d6bD830B73E95"])
    print("New Wallet Created:", result)
    
    # get info of the first wallet
    if wallets:
        wallet= client.wallet(wallets[0])
        wallet_info = wallet.get_info()
        print("Wallet Info:", wallet_info)

if __name__ == "__main__":
    main()