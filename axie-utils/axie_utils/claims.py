import asyncio
import rlp
import logging
from time import sleep

import requests
from requests.exceptions import RetryError
from web3 import Web3, exceptions
from trezorlib import ethereum

from axie_utils.abis import SLP_ABI
from axie_utils.utils import (
    check_balance,
    get_nonce,
    SLP_CONTRACT,
    RONIN_PROVIDER_FREE
)
from axie_utils.graphql import AxieGraphQL, TrezorAxieGraphQL


class Claim(AxieGraphQL):
    def __init__(self, acc_name, **kwargs):
        super().__init__(**kwargs)
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER_FREE,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": self.user_agent}}))
        self.slp_contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(SLP_CONTRACT),
            abi=SLP_ABI
        )
        self.acc_name = acc_name
        self.request = requests.Session()

    def has_unclaimed_slp(self):
        url = f"https://game-api.skymavis.com/game-api/clients/{self.account}/items/1"
        try:
            response = self.request.get(url, headers={"User-Agent": self.user_agent})
        except RetryError:
            logging.critical(f"Failed to check if there is unclaimed SLP for acc {self.acc_name} "
                             f"({self.account.replace('0x','ronin:')})")
            return None
        if 200 <= response.status_code <= 299:
            return int(response.json()['total'])
        return None

    async def async_execute(self):
        unclaimed = self.has_unclaimed_slp()
        if not unclaimed:
            logging.info(f"Important: Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "has no claimable SLP")
            return
        logging.info(f"Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) has "
                     f"{unclaimed} unclaimed SLP")
        jwt = self.get_jwt()
        if not jwt:
            logging.critical("Skipping claiming, we could not get the JWT for account "
                             f"{self.account.replace('0x', 'ronin:')}")
            return
        headers = {
            "User-Agent": self.user_agent,
            "authorization": f"Bearer {jwt}"
        }
        url = f"https://game-api.skymavis.com/game-api/clients/{self.account}/items/1/claim"
        try:
            response = self.request.post(url, headers=headers, json="")
        except RetryError as e:
            logging.critical(f"Error! Executing SLP claim API call for account {self.acc_name}"
                             f"({self.account.replace('0x', 'ronin:')}). Error {e}")
            return
        if 200 <= response.status_code <= 299:
            signature = response.json()["blockchain_related"].get("signature")
            if not signature or not signature["signature"]:
                logging.critical(f"Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) had no signature "
                                 "in blockchain_related")
                return
        else:
            logging.info(f"Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "had to be skipped")
            return
        nonce = get_nonce(self.account)
        # Build claim
        claim = self.slp_contract.functions.checkpoint(
            Web3.toChecksumAddress(self.account),
            signature['amount'],
            signature['timestamp'],
            signature['signature']
        ).buildTransaction({'gas': 492874, 'gasPrice': 0, 'nonce': nonce})
        # Sign claim
        signed_claim = self.w3.eth.account.sign_transaction(
            claim,
            private_key=self.private_key
        )
        # Send raw transaction
        self.w3.eth.send_raw_transaction(signed_claim.rawTransaction)
        # Get transaction hash
        hash = self.w3.toHex(self.w3.keccak(signed_claim.rawTransaction))
        # Wait for transaction to finish
        while True:
            try:
                recepit = self.w3.eth.get_transaction_receipt(hash)
                if recepit["status"] == 1:
                    success = True
                else:
                    success = False
                break
            except exceptions.TransactionNotFound:
                logging.debug(f"Waiting for claim for {self.acc_name} ({self.account.replace('0x', 'ronin:')}) to "
                              f"finish (Nonce:{nonce}) (Hash: {hash})...")
                # Sleep 5 seconds not to constantly send requests!
                await asyncio.sleep(5)
        if success:
            logging.info(f"SLP Claimed! New balance for account {self.acc_name} "
                         f"({self.account.replace('0x', 'ronin:')}) is: {check_balance(self.account)}")
        else:
            logging.info(f"Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "failed")

    def execute(self):
        unclaimed = self.has_unclaimed_slp()
        if not unclaimed:
            logging.info(f"Important: Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "has no claimable SLP")
            return
        logging.info(f"Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) has "
                     f"{unclaimed} unclaimed SLP")
        jwt = self.get_jwt()
        if not jwt:
            logging.critical("Skipping claiming, we could not get the JWT for account "
                             f"{self.account.replace('0x', 'ronin:')}")
            return
        headers = {
            "User-Agent": self.user_agent,
            "authorization": f"Bearer {jwt}"
        }
        url = f"https://game-api.skymavis.com/game-api/clients/{self.account}/items/1/claim"
        try:
            response = self.request.post(url, headers=headers, json="")
        except RetryError as e:
            logging.critical(f"Error! Executing SLP claim API call for account {self.acc_name}"
                             f"({self.account.replace('0x', 'ronin:')}). Error {e}")
            return
        if 200 <= response.status_code <= 299:
            signature = response.json()["blockchain_related"].get("signature")
            if not signature or not signature["signature"]:
                logging.critical(f"Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) had no signature "
                                 "in blockchain_related")
                return
        else:
            logging.info(f"Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "had to be skipped")
            return
        nonce = get_nonce(self.account)
        # Build claim
        claim = self.slp_contract.functions.checkpoint(
            Web3.toChecksumAddress(self.account),
            signature['amount'],
            signature['timestamp'],
            signature['signature']
        ).buildTransaction({'gas': 492874, 'gasPrice': 0, 'nonce': nonce})
        # Sign claim
        signed_claim = self.w3.eth.account.sign_transaction(
            claim,
            private_key=self.private_key
        )
        # Send raw transaction
        self.w3.eth.send_raw_transaction(signed_claim.rawTransaction)
        # Get transaction hash
        hash = self.w3.toHex(self.w3.keccak(signed_claim.rawTransaction))
        # Wait for transaction to finish
        while True:
            try:
                recepit = self.w3.eth.get_transaction_receipt(hash)
                if recepit["status"] == 1:
                    success = True
                else:
                    success = False
                break
            except exceptions.TransactionNotFound:
                logging.debug(f"Waiting for claim for {self.acc_name} ({self.account.replace('0x', 'ronin:')}) to "
                              f"finish (Nonce:{nonce}) (Hash: {hash})...")
                # Sleep 5 seconds not to constantly send requests!
                sleep(5)
        if success:
            logging.info(f"SLP Claimed! New balance for account {self.acc_name} "
                         f"({self.account.replace('0x', 'ronin:')}) is: {check_balance(self.account)}")
        else:
            logging.info(f"Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "failed")


class TrezorClaim(TrezorAxieGraphQL):
    def __init__(self, acc_name, **kwargs):
        super().__init__(**kwargs)
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER_FREE,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": self.user_agent}}))
        self.slp_contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(SLP_CONTRACT),
            abi=SLP_ABI
        )
        self.acc_name = acc_name
        self.request = requests.Session()
        self.gwei = self.w3.toWei('0', 'gwei')
        self.gas = 492874

    def has_unclaimed_slp(self):
        url = f"https://game-api.skymavis.com/game-api/clients/{self.account}/items/1"
        try:
            response = self.request.get(url, headers={"User-Agent": self.user_agent})
        except RetryError:
            logging.critical(f"Failed to check if there is unclaimed SLP for acc {self.acc_name} "
                             f"({self.account.replace('0x','ronin:')})")
            return None
        if 200 <= response.status_code <= 299:
            return int(response.json()['total'])
        return None

    async def async_execute(self):
        unclaimed = self.has_unclaimed_slp()
        if not unclaimed:
            logging.info(f"Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "has no claimable SLP")
            return
        logging.info(f"Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) has "
                     f"{unclaimed} unclaimed SLP")
        jwt = self.get_jwt()
        if not jwt:
            logging.critical("Skipping claiming, we could not get the JWT for account "
                             f"{self.account.replace('0x', 'ronin:')}")
            return
        headers = {
            "User-Agent": self.user_agent,
            "authorization": f"Bearer {jwt}"
        }
        url = f"https://game-api.skymavis.com/game-api/clients/{self.account}/items/1/claim"
        try:
            response = self.request.post(url, headers=headers, json="")
        except RetryError as e:
            logging.critical(f"Error! Executing SLP claim API call for account {self.acc_name}"
                             f"({self.account.replace('0x', 'ronin:')}). Error {e}")
            return
        if 200 <= response.status_code <= 299:
            signature = response.json()["blockchain_related"].get("signature")
            if not signature or not signature["signature"]:
                logging.critical(f"Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) had no signature "
                                 "in blockchain_related")
                return
        else:
            logging.info(f"Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "had to be skipped")
            return
        nonce = get_nonce(self.account)
        # Build claim
        claim = self.slp_contract.functions.checkpoint(
            Web3.toChecksumAddress(self.account),
            signature['amount'],
            signature['timestamp'],
            signature['signature']
        ).buildTransaction({'gas': self.gas, 'gasPrice': 0, 'nonce': nonce})
        data = self.w3.toBytes(hexstr=claim['data'])
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
        # Wait for transaction to finish
        while True:
            try:
                recepit = self.w3.eth.get_transaction_receipt(hash)
                if recepit["status"] == 1:
                    success = True
                else:
                    success = False
                break
            except exceptions.TransactionNotFound:
                logging.debug(f"Waiting for claim for {self.acc_name} ({self.account.replace('0x', 'ronin:')}) to "
                              f"finish (Nonce:{nonce}) (Hash: {hash})...")
                # Sleep 5 seconds not to constantly send requests!
                await asyncio.sleep(5)
        if success:
            logging.info(f"SLP Claimed! New balance for account {self.acc_name} "
                         f"({self.account.replace('0x', 'ronin:')}) is: {check_balance(self.account)}")
            return
        else:
            logging.info(f"Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "failed")
        return

    def execute(self):
        unclaimed = self.has_unclaimed_slp()
        if not unclaimed:
            logging.info(f"Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "has no claimable SLP")
            return
        logging.info(f"Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) has "
                     f"{unclaimed} unclaimed SLP")
        jwt = self.get_jwt()
        if not jwt:
            logging.critical("Skipping claiming, we could not get the JWT for account "
                             f"{self.account.replace('0x', 'ronin:')}")
            return
        headers = {
            "User-Agent": self.user_agent,
            "authorization": f"Bearer {jwt}"
        }
        url = f"https://game-api.skymavis.com/game-api/clients/{self.account}/items/1/claim"
        try:
            response = self.request.post(url, headers=headers, json="")
        except RetryError as e:
            logging.critical(f"Error! Executing SLP claim API call for account {self.acc_name}"
                             f"({self.account.replace('0x', 'ronin:')}). Error {e}")
            return
        if 200 <= response.status_code <= 299:
            signature = response.json()["blockchain_related"].get("signature")
            if not signature or not signature["signature"]:
                logging.critical(f"Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) had no signature "
                                 "in blockchain_related")
                return
        else:
            logging.info(f"Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "had to be skipped")
            return
        nonce = get_nonce(self.account)
        # Build claim
        claim = self.slp_contract.functions.checkpoint(
            Web3.toChecksumAddress(self.account),
            signature['amount'],
            signature['timestamp'],
            signature['signature']
        ).buildTransaction({'gas': self.gas, 'gasPrice': 0, 'nonce': nonce})
        data = self.w3.toBytes(hexstr=claim['data'])
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
        # Wait for transaction to finish
        while True:
            try:
                recepit = self.w3.eth.get_transaction_receipt(hash)
                if recepit["status"] == 1:
                    success = True
                else:
                    success = False
                break
            except exceptions.TransactionNotFound:
                logging.debug(f"Waiting for claim for {self.acc_name} ({self.account.replace('0x', 'ronin:')}) to "
                              f"finish (Nonce:{nonce}) (Hash: {hash})...")
                # Sleep 5 seconds not to constantly send requests!
                sleep(5)
        if success:
            logging.info(f"SLP Claimed! New balance for account {self.acc_name} "
                         f"({self.account.replace('0x', 'ronin:')}) is: {check_balance(self.account)}")
            return
        else:
            logging.info(f"Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "failed")
        return
