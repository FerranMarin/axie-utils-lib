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
    RONIN_PROVIDER,
    TIMEOUT_MINS,
    USER_AGENT
)


class Payment:
    def __init__(self, name, from_acc, from_private, to_acc, amount):
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER,
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

    def increase_gas_tx(self, nonce):
        # check nonce is still available, do nothing if nonce is not available anymore
        if nonce != get_nonce(self.from_acc):
            return
        # Increase gas price to get tx unstuck
        self.execute(1.01, nonce)

    def execute(self, gas_price=1, nonce=None):
        # Get Nonce
        if nonce is None:
            nonce = get_nonce(self.from_acc)
        # Build transaction
        transaction = self.contract.functions.transfer(
            Web3.toChecksumAddress(self.to_acc),
            self.amount
        ).buildTransaction({
            "chainId": 2020,
            "gas": 246437,
            "gasPrice": self.w3.toWei(str(gas_price), "gwei"),
            "nonce": nonce
        })
        # Sign Transaction
        signed = self.w3.eth.account.sign_transaction(
            transaction,
            private_key=self.from_private
        )
        # Send raw transaction
        self.w3.eth.send_raw_transaction(signed.rawTransaction)
        # get transaction _hash
        _hash = self.w3.toHex(self.w3.keccak(signed.rawTransaction))
        # Wait for transaction to finish or timeout
        start_time = datetime.now()
        while True:
            # We will wait for max 5minutes for this tx to respond, if it does not, we will re-try
            if datetime.now() - start_time > timedelta(minutes=TIMEOUT_MINS):
                success = False
                logging.info(f"Important: Transaction {self}, timed out!")
                break
            try:
                recepit = self.w3.eth.get_transaction_receipt(_hash)
                if recepit["status"] == 1:
                    success = True
                else:
                    success = False
                break
            except exceptions.TransactionNotFound:
                # Sleep 10s while waiting
                logging.info(f"Waiting for transaction '{self}' to finish (Nonce:{nonce})...")
                sleep(10)
            except ValueError as err:
                if 'receipts not found by' in err.args[0]['message']:
                    logging.info("Could not find TX, giving it a bit more time.")
                    sleep(20)
                else:
                    logging.warning(f"Important: Error occurred trying to find recepit for transaction '{self}'.\n"
                                    f"Error given: {err}.")
                    return

        if success:
            logging.info(f"Important: Transaction {self} completed! _hash: {_hash} - "
                         f"Explorer: https://explorer.roninchain.com/tx/{str(_hash)}")
            return _hash
        else:
            logging.info(f"Important: Transaction {self} failed. Trying to augment gas price to unstuck it.")
            self.increase_gas_tx(nonce)

    def __str__(self):
        return f"{self.name}({self.to_acc.replace('0x', 'ronin:')}) for the amount of {self.amount} SLP"


class TrezorPayment:
    def __init__(self, name, client, bip_path, from_acc, to_acc, amount):
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER,
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
        self.gas = 250000

    def increase_gas_tx(self, nonce):
        # check nonce is still available, do nothing if nonce is not available anymore
        if nonce != get_nonce(self.from_acc):
            return
        # Increase gas price to get tx unstuck
        self.execute(1.01, nonce)

    def execute(self, gas_price=1, nonce=None):
        # Get Nonce
        if nonce is None:
            nonce = get_nonce(self.from_acc)
        # Build transaction
        send_tx = self.contract.functions.transfer(
            Web3.toChecksumAddress(self.to_acc),
            self.amount
        ).buildTransaction({
            "chainId": 2020,
            "gas": self.gas,
            "gasPrice": self.w3.toWei(str(gas_price), "gwei"),
            "nonce": nonce
        })
        data = self.w3.toBytes(hexstr=send_tx['data'])
        to = self.w3.toBytes(hexstr=SLP_CONTRACT)
        sig = ethereum.sign_tx(
            self.client,
            n=self.bip_path,
            nonce=nonce,
            gas_price=self.w3.toWei(str(gas_price), "gwei"),
            gas_limit=self.gas,
            to=SLP_CONTRACT,
            value=0,
            data=data,
            chain_id=2020
        )
        l_sig = list(sig)
        l_sig[1] = l_sig[1].lstrip(b'\x00')
        l_sig[2] = l_sig[2].lstrip(b'\x00')
        sig = tuple(l_sig)
        transaction = rlp.encode((nonce, self.w3.toWei(str(gas_price), 'gwei'), self.gas, to, 0, data) + sig)
        # Send raw transaction
        self.w3.eth.send_raw_transaction(transaction)
        _hash = self.w3.toHex(self.w3.keccak(transaction))
        # Wait for transaction to finish or timeout
        start_time = datetime.now()
        while True:
            # We will wait for max 5 minutes for this tx to respond, if it does not, we will re-try
            if datetime.now() - start_time > timedelta(minutes=TIMEOUT_MINS):
                success = False
                logging.info(f"Important: Transaction {self}, timed out!")
                break
            try:
                recepit = self.w3.eth.get_transaction_receipt(_hash)
                if recepit["status"] == 1:
                    success = True
                else:
                    success = False
                break
            except exceptions.TransactionNotFound:
                # Sleep 10s while waiting
                logging.info(f"Waiting for transaction '{self}' to finish (Nonce:{nonce})...")
                sleep(10)
            except ValueError as err:
                if 'receipts not found by' in err.args[0]['message']:
                    logging.info("Could not find TX, giving it a bit more time.")
                    sleep(20)
                else:
                    logging.warning(f"Important: Error occurred trying to find recepit for transaction '{self}'.\n"
                                    f"Error given: {err}.")
                    return

        if success:
            logging.info(f"Important: Transaction {self} completed! _hash: {_hash} - "
                         f"Explorer: https://explorer.roninchain.com/tx/{str(_hash)}")
            return _hash
        else:
            logging.info(f"Important: Transaction {self} failed. Trying to augment gas price to unstuck it.")
            self.increase_gas_tx(nonce)

    def __str__(self):
        return f"{self.name}({self.to_acc.replace('0x', 'ronin:')}) for the amount of {self.amount} SLP"
