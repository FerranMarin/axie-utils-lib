import json
import logging
from datetime import datetime, timedelta

from web3 import Web3
import requests

from axie_utils.abis import AXIE_ABI
from axie_utils.utils import check_balance, RONIN_PROVIDER, AXIE_CONTRACT, USER_AGENT


class Axies:
    def __init__(self, account):
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}))
        self.acc = account.replace("ronin:", "0x").lower()
        self.contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(AXIE_CONTRACT),
            abi=AXIE_ABI
        )
        self.now = datetime.now()

    def number_of_axies(self):
        return check_balance(self.acc, 'axies')

    def check_axie_owner(self, axie_id):
        logging.debug(f'Owner: {self.contract.functions.ownerOf(axie_id).call().lower()}, "checker": {self.acc}')
        return self.contract.functions.ownerOf(axie_id).call().lower() ==self.acc

    def find_axies_to_morph(self):
        axie_list = self.get_axies()
        axies = []
        for axie in axie_list:
            morph_date, body_shape = self.get_morph_date_and_body(axie)
            if not morph_date and not body_shape:
                logging.info(f"Something went wrong getting info for Axie {axie}, skipping it")
            elif self.now >= morph_date and not body_shape:
                axies.append(axie)
            elif not body_shape:
                logging.info(f"Axie {axie} cannot be morphed until {morph_date}")
            else:
                logging.info(f"Axie {axie} is already an adult!")
        return axies

    def get_axies(self):
        num_axies = self.number_of_axies()
        axies = []
        for i in range(num_axies):
            axie = self.contract.functions.tokenOfOwnerByIndex(
                _owner=Web3.toChecksumAddress(self.acc),
                _index=i
            ).call()
            axies.append(axie)
        return axies

    @staticmethod
    def get_morph_date_and_body(axie_id):
        payload = {
            "operationName": "GetAxieDetail",
            "variables":
                {"axieId": axie_id},
            "query": "query GetAxieDetail($axieId: ID!) { axie(axieId: $axieId) "
            "{ ...AxieDetail __typename}} fragment AxieDetail on Axie "
            "{ id birthDate bodyShape __typename }"
        }
        url = "https://graphql-gateway.axieinfinity.com/graphql"
        response = requests.post(url, json=payload)
        try:
            json_response = response.json()
        except json.decoder.JSONDecodeError:
            logging.debug("Response contains no json info")
            return None, None

        if "data" in json_response and "axie" in json_response['data']:
            if 'bodyShape' in json_response['data']['axie'] and 'birthDate' in json_response['data']['axie']:
                # In case we want to check correctly morphed
                body_shape = json_response["data"]["axie"]["bodyShape"]
                birth_date = json_response["data"]["axie"]["birthDate"]
                morph_date = datetime.utcfromtimestamp(birth_date) + timedelta(days=5)
                return morph_date, body_shape

        return None, None

    @staticmethod
    def get_axie_details(axie_id):
        payload = {
            "operationName": "GetAxieDetail",
            "variables":
                {"axieId": axie_id},
            "query": "query GetAxieDetail($axieId: ID!) { axie(axieId: $axieId) "
            "{ ...AxieDetail }} fragment AxieDetail on Axie "
            "{ id class parts { ...AxiePart }} fragment AxiePart on AxiePart "
            "{ id name class type }"
        }
        url = "https://graphql-gateway.axieinfinity.com/graphql"
        response = requests.post(url, json=payload)
        try:
            json_response = response.json()
        except json.decoder.JSONDecodeError:
            logging.debug("Response contains no json info")
            return None
        if ("data" in json_response and 
            "axie" in json_response['data'] and 
            "parts" in json_response['data']['axie']):
            parts = {}
            for part in json_response['data']['axie']['parts']:
                parts[part['type'].lower()] = part['name'].lower()
            if "class" in json_response['data']['axie']:
                parts['class'] = json_response['data']['axie']['class'].lower()
            return parts
        return None
