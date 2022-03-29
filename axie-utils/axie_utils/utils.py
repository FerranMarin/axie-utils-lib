import logging
from datetime import datetime
from json.decoder import JSONDecodeError

import requests
from requests.packages.urllib3.util.retry import Retry
from web3 import Web3
from trezorlib.ui import ClickUI
from trezorlib.client import get_default_client
from trezorlib.tools import parse_path
from trezorlib import ethereum

from axie_utils.abis import BALANCE_ABI

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1944.0 Safari/537.36" # noqa
TIMEOUT_MINS = 5
AXIE_CONTRACT = "0x32950db2a7164ae833121501c797d79e7b79d74c"
AXS_CONTRACT = "0x97a9107c1793bc407d6f527b77e7fff4d812bece"
SLP_CONTRACT = "0xa8754b9fa15fc18bb59458815510e40a12cd2014"
WETH_CONTRACT = "0xc99a6a985ed2cac1ef41640596c5a5f9f4e19ef5"
USDC_CONTRACT = "0x0b7007c13325c48911f73a2dad5fa5dcbf808adc"
SCATTER_CONTRACT = "0x14978681c5f8ce2f6b66d1f1551b0ec67405574c"
RONIN_PROVIDER_FREE = "https://proxy.roninchain.com/free-gas-rpc"
RONIN_PROVIDER = "https://api.roninchain.com/rpc"
RETRIES = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=frozenset(['GET', 'POST'])
)

TOKEN = {
    'slp': SLP_CONTRACT,
    'axs': AXS_CONTRACT,
    'axies': AXIE_CONTRACT,
    'weth': WETH_CONTRACT,
    'usdc': USDC_CONTRACT
}


def check_balance(account, token='slp'):
    w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER,
                request_kwargs={
                    "headers": {"content-type": "application/json",
                                "user-agent": USER_AGENT}}))
    if token.lower() in TOKEN:
        contract = TOKEN[token.lower()]
    elif token.lower() == "ron":
        return float(w3.eth.get_balance(Web3.toChecksumAddress(account.replace("ronin:", "0x"))) / 1000000000000000000)
    else:
        return 0
    ctr = w3.eth.contract(
        address=Web3.toChecksumAddress(contract),
        abi=BALANCE_ABI
    )
    balance = ctr.functions.balanceOf(
        Web3.toChecksumAddress(account.replace("ronin:", "0x"))
    ).call()
    if token == 'weth':
        return float(balance/1000000000000000000)
    return int(balance)


def get_nonce(account):
    w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER_FREE,
                request_kwargs={
                    "headers": {"content-type": "application/json",
                                "user-agent": USER_AGENT}}))
    nonce = w3.eth.get_transaction_count(
        Web3.toChecksumAddress(account.replace("ronin:", "0x"))
    )
    return nonce


def get_lastclaim(account):
    url = f'https://game-api.skymavis.com/game-api/clients/{account.replace("ronin:", "0x")}/items/1'
    try:
        r = requests.get(url)
        rjs = r.json()
        if rjs.get('last_claimed_item_at'):
            date = datetime.utcfromtimestamp(rjs['last_claimed_item_at'])
            return date
    except JSONDecodeError:
        logging.critical('Something went wrong getting last claim')

    return None


class CustomUI(ClickUI):
    def __init__(self, passphrase=None, *args, **kwargs):
        self.passphrase = passphrase
        super().__init__(*args, **kwargs)

    def get_passphrase(self, *args, **kwargs):
        return self.passphrase


class TrezorConfig:
    def __init__(self, accounts_number, passphrase=None):
        self.accounts_number = accounts_number
        self.passphrase = '' if not passphrase else passphrase

    def list_bip_paths(self):
        response = {}
        ui = CustomUI(passphrase=self.passphrase)
        for i in range(self.accounts_number):
            bip_path = f"m/44'/60'/0'/0/{i}"
            client = get_default_client(ui=ui)
            ronin = ethereum.get_address(client, parse_path(bip_path), True).lower().replace('0x', 'ronin:')
            response[ronin] = {"passphrase": self.passphrase, "bip_path": bip_path}

        return response
