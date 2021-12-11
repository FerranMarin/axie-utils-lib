import json
import logging
import rlp
from time import sleep
from datetime import datetime, timedelta

from web3 import Web3, exceptions
from trezorlib.tools import parse_path
from trezorlib import ethereum

from axie_utils.utils import (
    get_nonce,
    RONIN_PROVIDER_FREE,
    AXIE_CONTRACT,
    TIMEOUT_MINS,
    USER_AGENT
)


class Breed:
    def __init__(self, sire_axie, matron_axie, address, private_key):
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER_FREE,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}))
        self.sire_axie = sire_axie
        self.matron_axie = matron_axie
        self.address = address.replace("ronin:", "0x")
        self.private_key = private_key

    def execute(self):
        # Prepare transaction
        with open("axie_utils/axie_abi.json") as f:
            axie_abi = json.load(f)
        axie_contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(AXIE_CONTRACT),
            abi=axie_abi
        )
        # Get Nonce
        nonce = get_nonce(self.address)
        # Build transaction
        transaction = axie_contract.functions.breedAxies(
            self.sire_axie,
            self.matron_axie
        ).buildTransaction({
            "chainId": 2020,
            "gas": 492874,
            "gasPrice": self.w3.toWei("0", "gwei"),
            "nonce": nonce
        })
        # Sign transaction
        signed = self.w3.eth.account.sign_transaction(
            transaction,
            private_key=self.private_key
        )
        # Send raw transaction
        self.w3.eth.send_raw_transaction(signed.rawTransaction)
        # get transaction hash
        hash = self.w3.toHex(self.w3.keccak(signed.rawTransaction))
        # Wait for transaction to finish or timeout
        logging.info("{self} about to start!")
        start_time = datetime.now()
        while True:
            # We will wait for max 10minutes for this tx to respond
            if datetime.now() - start_time > timedelta(minutes=TIMEOUT_MINS):
                success = False
                logging.info(f"Transaction {self}, timed out!")
                break
            try:
                recepit = self.w3.eth.get_transaction_receipt(hash)
                if recepit["status"] == 1:
                    success = True
                else:
                    success = False
                break
            except exceptions.TransactionNotFound:
                # Sleep 10s while waiting
                sleep(10)
                logging.info(f"Waiting for transactions '{self}' to finish (Nonce: {nonce})...")

        if success:
            logging.info(f"{self} completed successfully")
        else:
            logging.info(f"{self} failed")

    def __str__(self):
        return (f"Breeding axie {self.sire_axie} with {self.matron_axie} in account "
                f"{self.address.replace('0x', 'ronin:')}")


class TrezorBreed:
    def __init__(self, sire_axie, matron_axie, address, client, bip_path):
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER_FREE,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}))
        self.sire_axie = sire_axie
        self.matron_axie = matron_axie
        self.address = address.replace("ronin:", "0x")
        self.client = client
        self.bip_path = parse_path(bip_path)
        self.gwei = self.w3.toWei('0', 'gwei')
        self.gas = 250000

    def execute(self):
        # Prepare transaction
        with open("axie/axie_abi.json") as f:
            axie_abi = json.load(f)
        axie_contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(AXIE_CONTRACT),
            abi=axie_abi
        )
        # Get Nonce
        nonce = get_nonce(self.address)
        # Build transaction
        breed_tx = axie_contract.functions.breedAxies(
            self.sire_axie,
            self.matron_axie
        ).buildTransaction({
            "chainId": 2020,
            "gas": self.gas,
            "gasPrice": self.w3.toWei("0", "gwei"),
            "nonce": nonce
        })
        data = self.w3.toBytes(hexstr=breed_tx['data'])
        to = self.w3.toBytes(hexstr=AXIE_CONTRACT)
        sig = ethereum.sign_tx(
            self.client,
            n=self.bip_path,
            nonce=nonce,
            gas_price=self.gwei,
            gas_limit=self.gas,
            to=AXIE_CONTRACT,
            value=0,
            data=data,
            chain_id=2020
        )
        transaction = rlp.encode((nonce, self.gwei, self.gas, to, 0, data) + sig)
        # Send raw transaction
        self.w3.eth.send_raw_transaction(transaction)
        # get transaction hash
        hash = self.w3.toHex(self.w3.keccak(transaction))
        # Wait for transaction to finish or timeout
        logging.info("{self} about to start!")
        start_time = datetime.now()
        while True:
            # We will wait for max 10minutes for this tx to respond
            if datetime.now() - start_time > timedelta(minutes=TIMEOUT_MINS):
                success = False
                logging.info(f"Transaction {self}, timed out!")
                break
            try:
                recepit = self.w3.eth.get_transaction_receipt(hash)
                if recepit["status"] == 1:
                    success = True
                else:
                    success = False
                break
            except exceptions.TransactionNotFound:
                # Sleep 10s while waiting
                sleep(10)
                logging.info(f"Waiting for transactions '{self}' to finish (Nonce: {nonce})...")

        if success:
            logging.info(f"{self} completed successfully")
        else:
            logging.info(f"{self} failed")

    def __str__(self):
        return (f"Breeding axie {self.sire_axie} with {self.matron_axie} in account "
                f"{self.address.replace('0x', 'ronin:')}")
