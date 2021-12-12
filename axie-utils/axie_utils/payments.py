import json
import rlp
import logging
from datetime import datetime, timedelta
from time import sleep

from trezorlib import ethereum
from trezorlib.tools import parse_path
from web3 import Web3, exceptions

from axie_utils.abis import SLP_ABI
from axie_utils.utils import (
    get_nonce,
    SLP_CONTRACT,
    RONIN_PROVIDER_FREE,
    TIMEOUT_MINS,
    USER_AGENT
)


class Payment:
    def __init__(self, name, from_acc, from_private, to_acc, amount):
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER_FREE,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}))
        self.name = name
        self.from_acc = from_acc.replace("ronin:", "0x")
        self.from_private = from_private
        self.to_acc = to_acc.replace("ronin:", "0x")
        self.amount = amount
        self.contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(SLP_CONTRACT),
            abi=SLP_ABI
        )

    def send_replacement_tx(self, nonce):
        # check nonce is still available, do nothing if nonce is not available anymore
        if nonce != get_nonce(self.from_acc):
            return
        # build replacement tx
        replacement_tx = self.contract.functions.transfer(
            Web3.toChecksumAddress(self.from_acc),
            0
        ).buildTransaction({
            "chainId": 2020,
            "gas": 492874,
            "gasPrice": self.w3.toWei("0", "gwei"),
            "nonce": nonce
        })
        # Sign Transaction
        signed = self.w3.eth.account.sign_transaction(
            replacement_tx,
            private_key=self.from_private
        )
        # Send raw transaction
        self.w3.eth.send_raw_transaction(signed.rawTransaction)
        # get transaction hash
        new_hash = self.w3.toHex(self.w3.keccak(signed.rawTransaction))
        # Wait for transaction to finish or timeout
        start_time = datetime.now()
        while True:
            # We will wait for max 5min for this replacement tx to happen
            if datetime.now() - start_time > timedelta(minutes=TIMEOUT_MINS):
                success = False
                logging.info("Replacement transaction, timed out!")
                break
            try:
                receipt = self.w3.eth.get_transaction_receipt(new_hash)
                if receipt['status'] == 1:
                    success = True
                else:
                    success = False
                break
            except exceptions.TransactionNotFound:
                sleep(10)
                logging.info(f"Waiting for replacement tx to finish (Nonce: {nonce})")

        if success:
            logging.info(f"Successfuly replaced transaction with nonce: {nonce}")
            logging.info(f"Trying again to execute transaction {self} in 10 seconds")
            sleep(10)
            self.execute()
        else:
            logging.info(f"Important: Replacement transaction failed. Means we could not complete tx {self}")
            logging.info(f"Important: Please fix account ({self.name}) transactions manually before launching again.")

    def execute(self):
        # Get Nonce
        nonce = get_nonce(self.from_acc)
        # Build transaction
        transaction = self.contract.functions.transfer(
            Web3.toChecksumAddress(self.to_acc),
            self.amount
        ).buildTransaction({
            "chainId": 2020,
            "gas": 246437,
            "gasPrice": self.w3.toWei("0", "gwei"),
            "nonce": nonce
        })
        # Sign Transaction
        signed = self.w3.eth.account.sign_transaction(
            transaction,
            private_key=self.from_private
        )
        # Send raw transaction
        self.w3.eth.send_raw_transaction(signed.rawTransaction)
        # get transaction hash
        hash = self.w3.toHex(self.w3.keccak(signed.rawTransaction))
        # Wait for transaction to finish or timeout
        start_time = datetime.now()
        while True:
            # We will wait for max 5minutes for this tx to respond, if it does not, we will re-try
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
                logging.info(f"Waiting for transaction '{self}' to finish (Nonce:{nonce})...")

        if success:
            logging.info(f"Transaction {self} completed! Hash: {hash} - "
                         f"Explorer: https://explorer.roninchain.com/tx/{str(hash)}")
        else:
            logging.info(f"Transaction {self} failed. Trying to replace it with a 0 value tx and re-try.")
            self.send_replacement_tx(nonce)

    def __str__(self):
        return f"{self.name}({self.to_acc.replace('0x', 'ronin:')}) for the amount of {self.amount} SLP"


class TrezorPayment:
    def __init__(self, name, client, bip_path, from_acc, to_acc, amount):
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER_FREE,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}))
        self.name = name
        self.from_acc = from_acc.replace("ronin:", "0x")
        self.to_acc = to_acc.replace("ronin:", "0x")
        self.amount = amount
        self.contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(SLP_CONTRACT),
            abi=SLP_ABI
        )
        self.client = client
        self.bip_path = parse_path(bip_path)
        self.gwei = self.w3.toWei('0', 'gwei')
        self.gas = 250000

    def send_replacement_tx(self, nonce):
        # check nonce is still available, do nothing if nonce is not available anymore
        if nonce != get_nonce(self.from_acc):
            return
        # build replacement tx
        replace_tx = self.contract.functions.transfer(
            Web3.toChecksumAddress(self.from_acc),
            0
        ).buildTransaction({
            "chainId": 2020,
            "gas": self.gas,
            "gasPrice": self.w3.toWei("0", "gwei"),
            "nonce": nonce
        })
        data = self.w3.toBytes(hexstr=replace_tx['data'])
        to = self.w3.toBytes(hexstr=SLP_CONTRACT)
        sig = ethereum.sign_tx(
            self.client,
            n=self.bip_path,
            nonce=nonce,
            gas_price=self.gwei,
            gas_limit=self.gas,
            to=SLP_CONTRACT,
            value=0,
            data=data,
            chain_id=2020
        )
        replacement_tx = rlp.encode((nonce, self.gwei, self.gas, to, 0, data) + sig)
        # Send raw transaction
        self.w3.eth.send_raw_transaction(replacement_tx)
        # get transaction hash
        new_hash = self.w3.toHex(self.w3.keccak(replacement_tx))
        # Wait for transaction to finish or timeout
        start_time = datetime.now()
        while True:
            # We will wait for max 5min for this replacement tx to happen
            if datetime.now() - start_time > timedelta(minutes=TIMEOUT_MINS):
                success = False
                logging.info("Replacement transaction, timed out!")
                break
            try:
                receipt = self.w3.eth.get_transaction_receipt(new_hash)
                if receipt['status'] == 1:
                    success = True
                else:
                    success = False
                break
            except exceptions.TransactionNotFound:
                sleep(10)
                logging.info(f"Waiting for replacement tx to finish (Nonce: {nonce})")

        if success:
            logging.info(f"Successfuly replaced transaction with nonce: {nonce}")
            logging.info(f"Trying again to execute transaction {self} in 10 seconds")
            sleep(10)
            self.execute()
        else:
            logging.info(f"Replacement transaction failed. Means we could not complete tx {self}")

    def execute(self):
        # Get Nonce
        nonce = get_nonce(self.from_acc)
        # Build transaction
        send_tx = self.contract.functions.transfer(
            Web3.toChecksumAddress(self.to_acc),
            self.amount
        ).buildTransaction({
            "chainId": 2020,
            "gas": self.gas,
            "gasPrice": self.gwei,
            "nonce": nonce
        })
        data = self.w3.toBytes(hexstr=send_tx['data'])
        to = self.w3.toBytes(hexstr=SLP_CONTRACT)
        sig = ethereum.sign_tx(
            self.client,
            n=self.bip_path,
            nonce=nonce,
            gas_price=self.gwei,
            gas_limit=self.gas,
            to=SLP_CONTRACT,
            value=0,
            data=data,
            chain_id=2020
        )
        transaction = rlp.encode((nonce, self.gwei, self.gas, to, 0, data) + sig)
        # Send raw transaction
        self.w3.eth.send_raw_transaction(transaction)
        hash = self.w3.toHex(self.w3.keccak(transaction))
        # Wait for transaction to finish or timeout
        start_time = datetime.now()
        while True:
            # We will wait for max 5 minutes for this tx to respond, if it does not, we will re-try
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
                logging.info(f"Waiting for transaction '{self}' to finish (Nonce:{nonce})...")

        if success:
            logging.info(f"Transaction {self} completed! Hash: {hash} - "
                         f"Explorer: https://explorer.roninchain.com/tx/{str(hash)}")
        else:
            logging.info(f"Transaction {self} failed. Trying to replace it with a 0 value tx and re-try.")
            self.send_replacement_tx(nonce)

    def __str__(self):
        return f"{self.name}({self.to_acc.replace('0x', 'ronin:')}) for the amount of {self.amount} SLP"
