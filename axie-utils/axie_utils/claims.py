import asyncio
import rlp
import logging
from time import sleep
from datetime import datetime, timedelta, timezone

import requests
from requests.exceptions import RetryError
from web3 import Web3, exceptions
from trezorlib import ethereum

from axie_utils.abis import SLP_ABI
from axie_utils.utils import (
    check_balance,
    get_nonce,
    SLP_CONTRACT,
    RONIN_PROVIDER,
    TIMEOUT_MINS
)
from axie_utils.graphql import AxieGraphQL, TrezorAxieGraphQL


class Claim(AxieGraphQL):
    def __init__(self, acc_name, force, **kwargs):
        super().__init__(**kwargs)
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": self.user_agent}}))
        self.slp_contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(SLP_CONTRACT),
            abi=SLP_ABI
        )
        self.acc_name = acc_name
        self.force = force
        self.request = requests.Session()

    def localize_date(self, date_utc):
        return date_utc.replace(tzinfo=timezone.utc).astimezone(tz=None)

    def humanize_date(self, date):
        local_date = self.localize_date(date)
        return local_date.strftime("%m/%d/%Y, %H:%M")

    def has_unclaimed_slp(self):
        url = f"http://game-api-pre.skymavis.com/v1/players/{self.account}/items/1"
        try:
            response = self.request.get(url, headers={"User-Agent": self.user_agent})
        except RetryError:
            logging.critical(f"Important: Failed to check if there is unclaimed SLP for acc {self.acc_name} "
                             f"({self.account.replace('0x', 'ronin:')})")
            return None
        if 200 <= response.status_code <= 299:
            data = response.json()
            last_claimed = datetime.utcfromtimestamp(data['lastClaimedItemAt'])
            next_claim_date = last_claimed + timedelta(days=14)
            utcnow = datetime.utcnow()
            if utcnow < next_claim_date and not self.force:
                logging.critical(
                    f"Important: This account will be claimable again on {self.humanize_date(next_claim_date)}.")
                return None
            elif self.force:
                logging.info('Important: Skipping check of dates, --force option was selected')
            claimable_total = int(data['rawClaimableTotal'])
            if claimable_total > 0:
                return claimable_total
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
            logging.critical("Important: Skipping claiming, we could not get the JWT for account "
                             f"{self.account.replace('0x', 'ronin:')}")
            return
        headers = {
            "User-Agent": self.user_agent,
            "authorization": f"Bearer {jwt}"
        }
        url = "http://game-api-pre.skymavis.com/v1/players/me/items/1/claim"
        try:
            response = self.request.post(url, headers=headers, json="")
        except RetryError as e:
            logging.critical(f"Important: Error! Executing SLP claim API call for account {self.acc_name}"
                             f"({self.account.replace('0x', 'ronin:')}). Error {e}")
            return
        if 200 <= response.status_code <= 299:
            signature = response.json()["blockchainRelated"].get("signature")
            if not signature or not signature["signature"]:
                logging.critical(f"Important: Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) had no signature "
                                 "in blockchainRelated")
                return
        else:
            logging.info(f"Important: Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "had to be skipped")
            return
        nonce = get_nonce(self.account)
        # Build claim
        claim = self.slp_contract.functions.checkpoint(
            Web3.toChecksumAddress(self.account),
            signature['amount'],
            signature['timestamp'],
            signature['signature']
        ).buildTransaction({'gas': 492874, 'gasPrice': self.w3.toWei('1', 'gwei'), 'nonce': nonce})
        # Sign claim
        signed_claim = self.w3.eth.account.sign_transaction(
            claim,
            private_key=self.private_key
        )
        # Send raw transaction
        self.w3.eth.send_raw_transaction(signed_claim.rawTransaction)
        # Get transaction hash
        hash = self.w3.toHex(self.w3.keccak(signed_claim.rawTransaction))
       # Wait for transaction to finish or timeout
        start_time = datetime.now()
        while True:
            # We will wait for max 5 minutes for this tx to respond
            if datetime.now() - start_time > timedelta(minutes=TIMEOUT_MINS):
                success = False
                logging.info(f"Important: Transaction {self}, timed out!")
                break
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
            logging.info(f"Important: SLP Claimed! New balance for account {self.acc_name} "
                         f"({self.account.replace('0x', 'ronin:')}) is: {check_balance(self.account)}")
        else:
            logging.info(f"Important: Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
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
            logging.critical("Important: Skipping claiming, we could not get the JWT for account "
                             f"{self.account.replace('0x', 'ronin:')}")
            return
        headers = {
            "User-Agent": self.user_agent,
            "authorization": f"Bearer {jwt}"
        }
        url = "http://game-api-pre.skymavis.com/v1/players/me/items/1/claim"
        try:
            response = self.request.post(url, headers=headers, json="")
        except RetryError as e:
            logging.critical(f"Important: Error! Executing SLP claim API call for account {self.acc_name}"
                             f"({self.account.replace('0x', 'ronin:')}). Error {e}")
            return
        if 200 <= response.status_code <= 299:
            signature = response.json()["blockchainRelated"].get("signature")
            if not signature or not signature["signature"]:
                logging.critical(f"Important: Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) had no signature "
                                 "in blockchainRelated")
                return
        else:
            logging.info(f"Important: Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "had to be skipped")
            return
        nonce = get_nonce(self.account)
        # Build claim
        claim = self.slp_contract.functions.checkpoint(
            Web3.toChecksumAddress(self.account),
            signature['amount'],
            signature['timestamp'],
            signature['signature']
        ).buildTransaction({'gas': 492874, 'gasPrice': self.w3.toWei('1', 'gwei'), 'nonce': nonce})
        # Sign claim
        signed_claim = self.w3.eth.account.sign_transaction(
            claim,
            private_key=self.private_key
        )
        # Send raw transaction
        self.w3.eth.send_raw_transaction(signed_claim.rawTransaction)
        # Get transaction hash
        hash = self.w3.toHex(self.w3.keccak(signed_claim.rawTransaction))
        # Wait for transaction to finish or timeout
        start_time = datetime.now()
        while True:
            # We will wait for max 5 minutes for this tx to respond
            if datetime.now() - start_time > timedelta(minutes=TIMEOUT_MINS):
                success = False
                logging.info(f"Important: Transaction {self}, timed out!")
                break
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
            logging.info(f"Important: SLP Claimed! New balance for account {self.acc_name} "
                         f"({self.account.replace('0x', 'ronin:')}) is: {check_balance(self.account)}")
        else:
            logging.info(f"Important: Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "failed")

    def __str__(self):
        return f"SLP claim for account {self.account.replace('0x', 'ronin:')}"

class TrezorClaim(TrezorAxieGraphQL):
    def __init__(self, acc_name, force, **kwargs):
        super().__init__(**kwargs)
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": self.user_agent}}))
        self.slp_contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(SLP_CONTRACT),
            abi=SLP_ABI
        )
        self.acc_name = acc_name
        self.force = force
        self.request = requests.Session()
        self.gwei = self.w3.toWei('1', 'gwei')
        self.gas = 492874

    def localize_date(self, date_utc):
        return date_utc.replace(tzinfo=timezone.utc).astimezone(tz=None)

    def humanize_date(self, date):
        local_date = self.localize_date(date)
        return local_date.strftime("%m/%d/%Y, %H:%M")

    def has_unclaimed_slp(self):
        url = f"http://game-api-pre.skymavis.com/v1/players/{self.account}/items/1"
        try:
            response = self.request.get(url, headers={"User-Agent": self.user_agent})
        except RetryError:
            logging.critical(f"Important: Failed to check if there is unclaimed SLP for acc {self.acc_name} "
                             f"({self.account.replace('0x','ronin:')})")
            return None
        if 200 <= response.status_code <= 299:
            data = response.json()
            last_claimed = datetime.utcfromtimestamp(data['lastClaimedItemAt'])
            next_claim_date = last_claimed + timedelta(days=14)
            utcnow = datetime.utcnow()
            if utcnow < next_claim_date and not self.force:
                logging.critical(f"Important: This account will be claimable again on {self.humanize_date(next_claim_date)}.")
                return None
            elif self.force:
                logging.info('Important: Skipping check of dates, --force option was selected')
            claimable_total = int(data['rawClaimableTotal'])
            if claimable_total > 0:
                return claimable_total
        return None

    async def async_execute(self):
        unclaimed = self.has_unclaimed_slp()
        if not unclaimed:
            logging.info(f"Important: Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "has no claimable SLP")
            return
        logging.info(f"Important: Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) has "
                     f"{unclaimed} unclaimed SLP")
        jwt = self.get_jwt()
        if not jwt:
            logging.critical("Important: Skipping claiming, we could not get the JWT for account "
                             f"{self.account.replace('0x', 'ronin:')}")
            return
        headers = {
            "User-Agent": self.user_agent,
            "authorization": f"Bearer {jwt}"
        }
        url = "http://game-api-pre.skymavis.com/v1/players/me/items/1/claim"
        try:
            response = self.request.post(url, headers=headers, json="")
        except RetryError as e:
            logging.critical(f"Important: Error! Executing SLP claim API call for account {self.acc_name}"
                             f"({self.account.replace('0x', 'ronin:')}). Error {e}")
            return
        if 200 <= response.status_code <= 299:
            signature = response.json()["blockchainRelated"].get("signature")
            if not signature or not signature["signature"]:
                logging.critical(f"Important: Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) had no signature "
                                 "in blockchainRelated")
                return
        else:
            logging.info(f"Important: Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "had to be skipped")
            return
        nonce = get_nonce(self.account)
        # Build claim
        claim = self.slp_contract.functions.checkpoint(
            Web3.toChecksumAddress(self.account),
            signature['amount'],
            signature['timestamp'],
            signature['signature']
        ).buildTransaction({'gas': self.gas, 'gasPrice': self.w3.toWei('1', 'gwei'), 'nonce': nonce})
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
        l_sig = list(sig)
        l_sig[1] = l_sig[1].lstrip(b'\x00')
        l_sig[2] = l_sig[2].lstrip(b'\x00')
        sig = tuple(l_sig)
        transaction = rlp.encode((nonce, self.gwei, self.gas, to, 0, data) + sig)
        # Send raw transaction
        self.w3.eth.send_raw_transaction(transaction)
        hash = self.w3.toHex(self.w3.keccak(transaction))
        # Wait for transaction to finish or timeout
        start_time = datetime.now()
        while True:
            # We will wait for max 5 minutes for this tx to respond
            if datetime.now() - start_time > timedelta(minutes=TIMEOUT_MINS):
                success = False
                logging.info(f"Important: Transaction {self}, timed out!")
                break
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
            logging.info(f"Important: SLP Claimed! New balance for account {self.acc_name} "
                         f"({self.account.replace('0x', 'ronin:')}) is: {check_balance(self.account)}")
            return
        else:
            logging.info(f"Important: Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "failed")
        return

    def execute(self):
        unclaimed = self.has_unclaimed_slp()
        if not unclaimed:
            logging.info(f"Important: Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "has no claimable SLP")
            return
        logging.info(f"Important: Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) has "
                     f"{unclaimed} unclaimed SLP")
        jwt = self.get_jwt()
        if not jwt:
            logging.critical("Important: Skipping claiming, we could not get the JWT for account "
                             f"{self.account.replace('0x', 'ronin:')}")
            return
        headers = {
            "User-Agent": self.user_agent,
            "authorization": f"Bearer {jwt}"
        }
        url = "http://game-api-pre.skymavis.com/v1/players/me/items/1/claim"
        try:
            response = self.request.post(url, headers=headers, json="")
        except RetryError as e:
            logging.critical(f"Important: Error! Executing SLP claim API call for account {self.acc_name}"
                             f"({self.account.replace('0x', 'ronin:')}). Error {e}")
            return
        if 200 <= response.status_code <= 299:
            signature = response.json()["blockchainRelated"].get("signature")
            if not signature or not signature["signature"]:
                logging.critical(f"Important: Account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) had no signature "
                                 "in blockchainRelated")
                return
        else:
            logging.info(f"Important: Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "had to be skipped")
            return
        nonce = get_nonce(self.account)
        # Build claim
        claim = self.slp_contract.functions.checkpoint(
            Web3.toChecksumAddress(self.account),
            signature['amount'],
            signature['timestamp'],
            signature['signature']
        ).buildTransaction({'gas': self.gas, 'gasPrice': self.w3.toWei('1', 'gwei'), 'nonce': nonce})
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
        l_sig = list(sig)
        l_sig[1] = l_sig[1].lstrip(b'\x00')
        l_sig[2] = l_sig[2].lstrip(b'\x00')
        sig = tuple(l_sig)
        transaction = rlp.encode((nonce, self.gwei, self.gas, to, 0, data) + sig)
        # Send raw transaction
        self.w3.eth.send_raw_transaction(transaction)
        hash = self.w3.toHex(self.w3.keccak(transaction))
        # Wait for transaction to finish or timeout
        start_time = datetime.now()
        while True:
            # We will wait for max 5 minutes for this tx to respond
            if datetime.now() - start_time > timedelta(minutes=TIMEOUT_MINS):
                success = False
                logging.info(f"Important: Transaction {self}, timed out!")
                break
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
            logging.info(f"Important: SLP Claimed! New balance for account {self.acc_name} "
                         f"({self.account.replace('0x', 'ronin:')}) is: {check_balance(self.account)}")
            return
        else:
            logging.info(f"Important: Claim for account {self.acc_name} ({self.account.replace('0x', 'ronin:')}) "
                         "failed")
        return

    def __str__(self):
        return f"SLP claim for account {self.account.replace('0x', 'ronin:')}"
