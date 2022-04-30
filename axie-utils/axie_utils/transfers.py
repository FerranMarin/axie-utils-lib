import logging
import rlp
from datetime import datetime, timedelta
from time import sleep

from trezorlib.tools import parse_path
from trezorlib import ethereum
from web3 import Web3, exceptions

from axie_utils.abis import AXIE_ABI
from axie_utils.utils import (
    get_nonce,
    RONIN_PROVIDER,
    AXIE_CONTRACT,
    TIMEOUT_MINS,
    USER_AGENT
)


class Transfer:
    def __init__(self, from_acc, from_private, to_acc, axie_id):
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}))
        self.from_acc = from_acc.replace("ronin:", "0x")
        self.from_private = from_private
        self.to_acc = to_acc.replace("ronin:", "0x")
        self.axie_id = axie_id

    def execute(self):
        # Load ABI
        axie_contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(AXIE_CONTRACT),
            abi=AXIE_ABI
        )
        # Get Nonce
        nonce = get_nonce(self.from_acc)
        # Build transaction
        transaction = axie_contract.functions.safeTransferFrom(
            Web3.toChecksumAddress(self.from_acc),
            Web3.toChecksumAddress(self.to_acc),
            self.axie_id
        ).buildTransaction({
            "chainId": 2020,
            "gas": 492874,
            "from": Web3.toChecksumAddress(self.from_acc),
            "gasPrice": self.w3.toWei("1", "gwei"),
            "value": 0,
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
            # We will wait for max 5min for this trasnfer to happen
            if datetime.now() - start_time > timedelta(minutes=TIMEOUT_MINS):
                success = False
                logging.info(f"Important: Transfer {self}, timed out!")
                break
            try:
                recepit = self.w3.eth.get_transaction_receipt(_hash)
                if recepit["status"] == 1:
                    success = True
                else:
                    success = False
                break
            except exceptions.TransactionNotFound:
                logging.info(f"Waiting for transfer '{self}' to finish (Nonce:{nonce})...")
                # Sleep 10 seconds not to constantly send requests!
                sleep(10)
            except ValueError as err:
                if 'receipts not found by' in err.args[0]['message']:
                    logging.info("Could not find TX, giving it a bit more time.")
                    sleep(20)
                else:
                    logging.warning("Important: Error occurred trying to find recepit for transaction '{self}'.\n"
                                    "Error given: {err}.")
                    return
        if success:
            logging.info(f"Important: {self} completed! Hash: {_hash} - "
                         f"Explorer: https://explorer.roninchain.com/tx/{str(_hash)}")
            return _hash
        else:
            logging.info(f"Important: {self} failed")
            return

    def __str__(self):
        return (f"Axie Transfer of axie ({self.axie_id}) from account ({self.from_acc.replace('0x', 'ronin:')}) "
                f"to account ({self.to_acc.replace('0x', 'ronin:')})")


class TrezorTransfer:
    def __init__(self, from_acc, client, bip_path, to_acc, axie_id):
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}))
        self.from_acc = from_acc.replace("ronin:", "0x")
        self.to_acc = to_acc.replace("ronin:", "0x")
        self.axie_id = axie_id
        self.client = client
        self.bip_path = parse_path(bip_path)
        self.gwei = self.w3.toWei('1', 'gwei')
        self.gas = 250000

    def execute(self):
        axie_contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(AXIE_CONTRACT),
            abi=AXIE_ABI
        )
        # Get Nonce
        nonce = get_nonce(self.from_acc)
        # Build transaction
        transfer_tx = axie_contract.functions.safeTransferFrom(
            Web3.toChecksumAddress(self.from_acc),
            Web3.toChecksumAddress(self.to_acc),
            self.axie_id
        ).buildTransaction({
            "chainId": 2020,
            "gas": self.gas,
            "from": Web3.toChecksumAddress(self.from_acc),
            "gasPrice": self.w3.toWei("1", "gwei"),
            "value": 0,
            "nonce": nonce
        })
        data = self.w3.toBytes(hexstr=transfer_tx['data'])
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
        l_sig = list(sig)
        l_sig[1] = l_sig[1].lstrip(b'\x00')
        l_sig[2] = l_sig[2].lstrip(b'\x00')
        sig = tuple(l_sig)
        transaction = rlp.encode((nonce, self.gwei, self.gas, to, 0, data) + sig)
        # Send raw transaction
        self.w3.eth.send_raw_transaction(transaction)
        # Get transaction _hash
        _hash = self.w3.toHex(self.w3.keccak(transaction))
        # Wait for transaction to finish or timeout
        start_time = datetime.now()
        while True:
            # We will wait for max 5min for this trasnfer to happen
            if datetime.now() - start_time > timedelta(minutes=TIMEOUT_MINS):
                success = False
                logging.info(f"Important: Transfer {self}, timed out!")
                break
            try:
                recepit = self.w3.eth.get_transaction_receipt(_hash)
                if recepit["status"] == 1:
                    success = True
                else:
                    success = False
                break
            except exceptions.TransactionNotFound:
                logging.info(f"Waiting for transfer '{self}' to finish (Nonce:{nonce})...")
                # Sleep 10 seconds not to constantly send requests!
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
            logging.info(f"Important: {self} completed! Hash: {_hash} - "
                         f"Explorer: https://explorer.roninchain.com/tx/{str(_hash)}")
            return _hash
        else:
            logging.info(f"Important: {self} failed")
            return

    def __str__(self):
        return (f"Axie Transfer of axie ({self.axie_id}) from account ({self.from_acc.replace('0x', 'ronin:')}) "
                f"to account ({self.to_acc.replace('0x', 'ronin:')})")
