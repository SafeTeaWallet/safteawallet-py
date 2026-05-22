from web3 import Web3
import json


with open('abis/wallet.json') as f:
    wallet_abi = json.load(f)

with open('abis/factory.json') as f:
    factory_abi = json.load(f)




factory_address = '0x5FbDB2315678afecb367f032d93F642f64180aa3'
wallet_address = '0xa16E02E87b7454126E5E10d957A927A7F5B5d2be'



w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
factory_contract = w3.eth.contract(address=factory_address, abi=factory_abi)
wallet_contract = w3.eth.contract(address=wallet_address, abi=wallet_abi)



def get_wallet_transactions(wallet_contract):
    return wallet_contract.functions.getTransactionCount().call()

def get_transaction_details(index):
    return wallet_contract.functions.transactions(index).call()


if __name__ == "__main__":
    tx_count = get_wallet_transactions(wallet_contract)
    print(f"Total Transactions in Wallet: {tx_count}")

    for i in range(tx_count):
        tx_details = get_transaction_details(i)
        print(f"Transaction {i}: To: {tx_details[0]}, Value: {tx_details[1]}, Data: {tx_details[2]}, Executed: {tx_details[3]}")