# Importing libraries
import os
import subprocess 
import json

from dotenv import load_dotenv

from constants import *
from bit import Key, PrivateKey, PrivateKeyTestnet
from bit.network import NetworkAPI
from bit import *
from web3 import Web3
from eth_account import Account 
from web3.middleware import geth_poa_middleware

# Web3 connection and loading mnemonic
# Nodes runing with POW
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Loading ENV
load_dotenv

# Loading Mnemonic EV and (set this mnemonic as an environment variable, and include the one you generated as a fallback using)
mnemonic = os.getenv('MNEMONIC', "sausage riot team tree because bag width strategy observe night satisfy danger")
print(mnemonic)
# Create a coin object to hold child wallets
#coins = {"eth", "btc-test", "btc"}
# dictionary to store keys and accounts generated
keys = {}
# dictionary to hold coins - from constants file
coins ={BTC,  BTCTEST, ETH}
# number of accounts to derive
numderive = 5
#1 function to show all the wallet accounts generated
def setup_accounts(num_accounts=numderive):
    ''' use this function first to get all the keys and use command read key of account e.g. eth_PrivateKey = keys["eth"][0]['privkey']  '''
    for coin in coins:
            keys[coin]= derive_wallets(os.getenv('mnemonic'), coin=coin, num_accounts=num_accounts)

    print(json.dumps(keys, indent=5, sort_keys=True))
    return keys

# Functions to transact
#2 create function to call the hd-wallet derive on windows machine where symlink is not available
def derive_wallets(mnemonic, coin, num_accounts):
    """Use the subprocess library to call the php file script from Python"""
    command = f'php hd-wallet-derive/hd-wallet-derive.php -g --mnemonic="{mnemonic}" --numderive="{numderive}" --coin="{coin}" --format=json' 
    
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
   
    keys = json.loads(output)
    return  keys
 


#3 - convert private key string 
def priv_key_to_account(coin, priv_key):
    """Convert the privkey string in a child key to an account object that bit or web3.py can use to transact"""
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    if coin == BTCTEST:
        return PrivateKeyTestnet(priv_key)
    

#4 create transaction and metadata

def create_trx(coin, account, recipient, amount,chain_id):
    """create the raw, unsigned transaction that contains all metadata needed to transact"""
    global trx_data
    if coin ==ETH:
        gasEstimate = w3.eth.estimateGas(
            {"from": account.address, "to": recipient, "value": amount}
        )
        trx_data = {
            "to": recipient,
            "chainId": chain_id,
            "from": account.address,
            "value": amount,
            "gasPrice": w3.eth.gasPrice,
            "gas": gasEstimate,
            "nonce": w3.eth.getTransactionCount(account.address)
        }
        return trx_data

    if coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account.address, [(recipient, amount, BTC)]) 

#4 create, sign, send the transaction 

def send_trx(coin, account, recipient, amount,chain_id):
    """call create_trx, sign the transaction, then send it to the designated network"""
    if coin == "eth": 
        trx_eth = create_trx(coin,account, recipient, amount,chain_id)
        sign = account.signTransaction(trx_eth)
        result = w3.eth.sendRawTransaction(sign.rawTransaction)
        print(result.hex())
        return result.hex()
    else:
        trx_btctest= create_trx(coin,account,recipient,amount)
        sign_trx_btctest = account.sign_transaction(trx_btctest)
        from bit.network import NetworkAPI
        NetworkAPI.broadcast_tx_testnet(sign_trx_btctest)       
        return sign_trx_btctest