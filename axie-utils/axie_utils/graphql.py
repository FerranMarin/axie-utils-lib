import logging

from eth_account.messages import encode_defunct
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RetryError
from web3 import Web3
from hexbytes import HexBytes
from trezorlib import ethereum
from trezorlib.tools import parse_path

from axie_utils.utils import USER_AGENT, RETRIES


class AxieGraphQL:
    def __init__(self, account, private_key, **kwargs):
        self.account = account.lower().replace("ronin:", "0x")
        self.private_key = private_key.lower()
        self.request = requests.Session()
        self.request.mount('https://', HTTPAdapter(max_retries=RETRIES))
        self.user_agent = USER_AGENT

    def create_random_msg(self):
        payload = {
            "operationName": "CreateRandomMessage",
            "variables": {},
            "query": "mutation CreateRandomMessage{createRandomMessage}"
        }
        url = "https://graphql-gateway.axieinfinity.com/graphql"
        try:
            response = self.request.post(url, json=payload)
        except RetryError as e:
            logging.critical(f"Error! Creating random msg! Error: {e}")
            return None
        if 200 <= response.status_code <= 299:
            try:
                return response.json()['data']['createRandomMessage']
            except KeyError:
                return None
        return None

    def get_jwt(self):
        msg = self.create_random_msg()
        if not msg:
            return None
        signed_msg = Web3().eth.account.sign_message(
            encode_defunct(text=msg),
            private_key=self.private_key
        )
        hex_msg = signed_msg['signature'].hex()
        payload = {
            "operationName": "CreateAccessTokenWithSignature",
            "variables": {
                "input": {
                    "mainnet": "ronin",
                    "owner": f"{self.account}",
                    "message": f"{msg}",
                    "signature": f"{hex_msg}"
                }
            },
            "query": "mutation CreateAccessTokenWithSignature($input: SignatureInput!)"
            "{createAccessTokenWithSignature(input: $input) "
            "{newAccount result accessToken __typename}}"
        }
        url = "https://graphql-gateway.axieinfinity.com/graphql"
        try:
            response = self.request.post(url, headers={"User-Agent": self.user_agent}, json=payload)
        except RetryError as e:
            logging.critical(f"Error! Getting JWT! Error: {e}")
            return None
        if 200 <= response.status_code <= 299:
            if (not response.json().get('data') or not response.json()['data'].get('createAccessTokenWithSignature') or
               not response.json()['data']['createAccessTokenWithSignature'].get('accessToken')):
                logging.critical("Could not retreive JWT, probably your private key for this account is wrong. "
                                 f"Account: {self.account.replace('0x','ronin:')} \n AccountName: {self.acc_name}")
                return None
            return response.json()['data']['createAccessTokenWithSignature']['accessToken']
        return None


class TrezorAxieGraphQL:
    def __init__(self, account, client, bip_path):
        self.account = account.lower().replace("ronin:", "0x")
        self.request = requests.Session()
        self.request.mount('https://', HTTPAdapter(max_retries=RETRIES))
        self.user_agent = USER_AGENT
        self.client = client
        self.bip_path = parse_path(bip_path)

    def create_random_msg(self):
        payload = {
            "operationName": "CreateRandomMessage",
            "variables": {},
            "query": "mutation CreateRandomMessage{createRandomMessage}"
        }
        url = "https://graphql-gateway.axieinfinity.com/graphql"
        try:
            response = self.request.post(url, json=payload)
        except RetryError as e:
            logging.critical(f"Error! Creating random msg! Error: {e}")
            return None
        if 200 <= response.status_code <= 299:
            try:
                return response.json()['data']['createRandomMessage']
            except KeyError:
                return None
        return None

    def get_jwt(self):
        msg = self.create_random_msg()
        if not msg:
            return None
        signed_msg = ethereum.sign_message(self.client, self.bip_path, msg)
        hex_msg = HexBytes(signed_msg.signature).hex()
        payload = {
            "operationName": "CreateAccessTokenWithSignature",
            "variables": {
                "input": {
                    "mainnet": "ronin",
                    "owner": f"{self.account}",
                    "message": f"{msg}",
                    "signature": f"{hex_msg}"
                }
            },
            "query": "mutation CreateAccessTokenWithSignature($input: SignatureInput!)"
            "{createAccessTokenWithSignature(input: $input) "
            "{newAccount result accessToken __typename}}"
        }
        url = "https://graphql-gateway.axieinfinity.com/graphql"
        try:
            response = self.request.post(url, headers={"User-Agent": self.user_agent}, json=payload)
        except RetryError as e:
            logging.critical(f"Error! Getting JWT! Error: {e}")
            return None
        if 200 <= response.status_code <= 299:
            if (not response.json().get('data') or not response.json()['data'].get('createAccessTokenWithSignature') or
               not response.json()['data']['createAccessTokenWithSignature'].get('accessToken')):
                logging.critical("Could not retreive JWT, probably your private key for this account is wrong. "
                                 f"Account: {self.account.replace('0x','ronin:')} \n AccountName: {self.acc_name}")
                return None
            return response.json()['data']['createAccessTokenWithSignature']['accessToken']
        return None
