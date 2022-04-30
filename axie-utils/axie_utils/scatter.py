import rlp
import logging
from datetime import datetime, timedelta
from time import sleep

from trezorlib import ethereum
from trezorlib.tools import parse_path
from web3 import Web3, exceptions

from axie_utils.abis import SCATTER_ABI, APPROVE_ABI
from axie_utils.utils import (
    get_nonce,
    check_balance,
    SCATTER_CONTRACT,
    TOKEN,
    RONIN_PROVIDER,
    USER_AGENT,
    TIMEOUT_MINS
)
    

class Scatter:
    def __init__(self, token, from_acc, from_private, to_ronin_ammount_dict):
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}))
        self.token = token.lower()
        if self.token != 'ron':
            self.token_contract = self.w3.eth.contract(
                address=Web3.toChecksumAddress(TOKEN[self.token]),
                abi=APPROVE_ABI
            )
        self.from_acc = from_acc.replace("ronin:", "0x")
        self.from_private = from_private
        self.contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(SCATTER_CONTRACT),
            abi=SCATTER_ABI
        )
        self.to_list = []
        self.amounts_list = []
        for k,v in to_ronin_ammount_dict.items():
            self.to_list.append(Web3.toChecksumAddress(k.replace("ronin:", "0x")))
            if self.token == 'ron':
                self.amounts_list.append(self.w3.toWei(v,'ether'))
            else:
                self.amounts_list.append(v)
   
    def is_contract_accepted(self):
        allowance = self.token_contract.functions.allowance(
            Web3.toChecksumAddress(self.from_acc),
            Web3.toChecksumAddress(SCATTER_CONTRACT)).call()
        if int(allowance) > sum(self.amounts_list):
            return True
        return self.approve_contract()

    def approve_contract(self):
        approve_tx = self.token_contract.functions.approve(
            Web3.toChecksumAddress(SCATTER_CONTRACT),
            115792089237316195423570985008687907853269984665640564039457584007913129639935
        ).buildTransaction({
            "gas": 1000000,
            "gasPrice": self.w3.toWei(1, "gwei"),
            "nonce": get_nonce(self.from_acc)
        })
        signed_approval = self.w3.eth.account.sign_transaction(
            approve_tx,
            private_key=self.from_private
        )
        self.w3.eth.send_raw_transaction(signed_approval.rawTransaction)
        approve_hash = self.w3.toHex(self.w3.keccak(signed_approval.rawTransaction))
        approved = self.w3.eth.wait_for_transaction_receipt(approve_hash, timeout=240)
        if approved['status'] == 1:
            return True
        return False

    def increase_gas_tx(self, nonce):
        # check nonce is still available, do nothing if nonce is not available anymore
        if nonce != get_nonce(self.from_acc):
            return
        # Increase gas price to get tx unstuck
        return self.execute(1.01, nonce)

    def execute_token(self, gas_price=1, nonce=None):
        # Check token is approved
        if not self.is_contract_accepted():
            logging.warning(f"Token {self.token} is not approved to use scatter, "
                            "you can re-try or manually accept it on "
                            "scatter website (https://scatter.roninchain.com/).")
            return

        # Check enough balance is present
        if not check_balance(self.from_acc, self.token) >= sum(self.amounts_list) and check_balance(self.from_acc, 'ron') >= self.w3.toWei(0.00001, 'ether'):
            logging.warning(f"Important: Not enough {TOKEN[self.token]} balance or not enough RON to pay for the tx")
            return
        
        # Get Nonce
        if nonce is None:
            nonce = get_nonce(self.from_acc)
        # Build transaction
        transaction = self.contract.functions.disperseTokenSimple(
            Web3.toChecksumAddress(TOKEN[self.token]),
            self.to_list,
            self.amounts_list
        ).buildTransaction({
            "chainId": 2020,
            "gas": 1000000,
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
                logging.info(f"Important:Transaction {self}, timed out!")
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
            logging.info(f"Important: Transaction {self} completed! hash: {_hash} - "
                         f"Explorer: https://explorer.roninchain.com/tx/{str(_hash)}")
            return _hash
        else:
            logging.info(f"Important: Transaction {self} failed. Trying to augment gas price to unstuck it.")
            self.increase_gas_tx(nonce)
    
    
    def execute_ron(self, gas_price=1, nonce=None):
        # Check enough balance is present
        if not self.w3.toWei(check_balance(self.from_acc, 'ron'), 'ether') >= (sum(self.amounts_list) + self.w3.toWei(0.00001, 'ether')):
            logging.warning("Important: Not enough RON balance to scatter and pay the tx.")
            return
                
        # Get Nonce
        if nonce is None:
            nonce = get_nonce(self.from_acc)
        # Build transaction
        transaction = self.contract.functions.disperseEther(
            self.to_list,
            self.amounts_list
        ).buildTransaction({
            "chainId": 2020,
            "gas": 1000000,
            "gasPrice": self.w3.toWei(str(gas_price), "gwei"),
            "nonce": nonce,
            "value": sum(self.amounts_list)
        })
        logging.debug(f'DEBUG: {transaction}. \n to_list: {self.to_list}   \n amounts_list: {self.amounts_list}')
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
            logging.info(f"Important: Transaction {self} completed! hash: {_hash} - "
                         f"Explorer: https://explorer.roninchain.com/tx/{str(_hash)}")
            return _hash
        else:
            logging.info(f"Important: Transaction {self} failed. Trying to augment gas price to unstuck it.")
            self.increase_gas_tx(nonce)

    def execute(self, gas_price=1, nonce=None):
        if self.token == 'ron':
            return self.execute_ron(gas_price, nonce)
        return self.execute_token(gas_price, nonce)

    def __str__(self):
        return f"Scatter of {self.token} from {self.from_acc.replace('0x', 'ronin:')}"


class TrezorScatter:
    def __init__(self, token, from_acc, client, bip_path, to_ronin_ammount_dict):
        self.w3 = Web3(
            Web3.HTTPProvider(
                RONIN_PROVIDER,
                request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}))
        self.token = token.lower()
        if self.token != 'ron':
            self.token_contract = self.w3.eth.contract(
                address=Web3.toChecksumAddress(TOKEN[self.token]),
                abi=APPROVE_ABI
            )
        self.from_acc = from_acc.replace("ronin:", "0x")
        self.client = client
        self.bip_path = parse_path(bip_path)
        self.contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(SCATTER_CONTRACT),
            abi=SCATTER_ABI
        )
        self.to_list = []
        self.amounts_list = []
        for k,v in to_ronin_ammount_dict.items():
            self.to_list.append(Web3.toChecksumAddress(k.replace("ronin:", "0x")))
            if self.token == 'ron':
                self.amounts_list.append(self.w3.toWei(v,'ether'))
            else:
                self.amounts_list.append(v)
   
    def is_contract_accepted(self):        
        allowance = self.token_contract.functions.allowance(
            Web3.toChecksumAddress(self.from_acc),
            Web3.toChecksumAddress(SCATTER_CONTRACT)).call()
        if int(allowance) > sum(self.amounts_list):
            return True
        self.approve_contract()

    def approve_contract(self):
        nonce = get_nonce(self.from_acc)
        approve_tx = self.token_contract.functions.approve(
            Web3.toChecksumAddress(SCATTER_CONTRACT),
            115792089237316195423570985008687907853269984665640564039457584007913129639935
        ).buildTransaction({
            "gas": 1000000,
            "gasPrice": self.w3.toWei(1, "gwei"),
            "nonce": nonce
        })
        data = self.w3.toBytes(hexstr=approve_tx['data'])
        to = self.w3.toBytes(hexstr=TOKEN[self.token])
        sig = ethereum.sign_tx(
            self.client,
            n=self.bip_path,
            nonce=nonce,
            gas_price=self.w3.toWei(1, "gwei"),
            gas_limit=1000000,
            to=Web3.toChecksumAddress(TOKEN[self.token]),
            value=0,
            data=data,
            chain_id=2020
        )
        l_sig = list(sig)
        l_sig[1] = l_sig[1].lstrip(b'\x00')
        l_sig[2] = l_sig[2].lstrip(b'\x00')
        sig = tuple(l_sig)
        transaction = rlp.encode((nonce, self.w3.toWei(1, "gwei"), 1000000, to, 0, data) + sig)
        self.w3.eth.send_raw_transaction(transaction)
        approve_hash = self.w3.toHex(self.w3.keccak(transaction))
        approved = self.w3.eth.wait_for_transaction_receipt(approve_hash, timeout=240)
        if approved['status'] == 1:
            return True
        return False

    def increase_gas_tx(self, nonce):
        # check nonce is still available, do nothing if nonce is not available anymore
        if nonce != get_nonce(self.from_acc):
            return
        # Increase gas price to get tx unstuck
        if self.token == 'ron':
            self.execute_ron(1.01, nonce)
        self.execute_token(1.01, nonce)

    def execute_token(self, gas_price=1, nonce=None):
        # Check token is approved
        if not self.is_contract_accepted():
            logging.warning(f"Important: Token {self.token} is not approved to use scatter, "
                            "you can re-try or manually accept it on "
                            "scatter website (https://scatter.roninchain.com/).")
            return

        # Check enough balance is present
        if not check_balance(self.from_acc, self.token) >= (sum(self.amounts_list) and check_balance(self.from_acc, 'ron') >= self.w3.toWei(0.00001, 'ether')):
            logging.warning(f"Important: Not enough {TOKEN[self.token]} balance or not enough RON to pay for the tx")
            return
        
        # Get Nonce
        if nonce is None:
            nonce = get_nonce(self.from_acc)
        # Build transaction
        transaction = self.contract.functions.disperseTokenSimple(
            Web3.toChecksumAddress(TOKEN[self.token]),
            self.to_list,
            self.amounts_list
        ).buildTransaction({
            "chainId": 2020,
            "gas": 1000000,
            "gasPrice": self.w3.toWei(str(gas_price), "gwei"),
            "nonce": nonce
        })
        data = self.w3.toBytes(hexstr=transaction['data'])
        to = self.w3.toBytes(hexstr=SCATTER_CONTRACT)
        sig = ethereum.sign_tx(
            self.client,
            n=self.bip_path,
            nonce=nonce,
            gas_price=self.w3.toWei(str(gas_price), "gwei"),
            gas_limit=1000000,
            to=SCATTER_CONTRACT,
            value=0,
            data=data,
            chain_id=2020
        )
        l_sig = list(sig)
        l_sig[1] = l_sig[1].lstrip(b'\x00')
        l_sig[2] = l_sig[2].lstrip(b'\x00')
        sig = tuple(l_sig)
        transaction = rlp.encode((nonce, self.w3.toWei(str(gas_price), "gwei"), 1000000, to, 0, data) + sig)
        # Send raw transaction
        self.w3.eth.send_raw_transaction(transaction)
        _hash = self.w3.toHex(self.w3.keccak(transaction))
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
            logging.info(f"Important: Transaction {self} completed! hash: {_hash} - "
                         f"Explorer: https://explorer.roninchain.com/tx/{str(_hash)}")
            return _hash
        else:
            logging.info(f"Important: Transaction {self} failed. Trying to augment gas price to unstuck it.")
            self.increase_gas_tx(nonce)
    
    
    def execute_ron(self, gas_price=1, nonce=None):
        # Check enough balance is present
        if not self.w3.toWei(check_balance(self.from_acc, 'ron'), 'ether') >= (sum(self.amounts_list) + self.w3.toWei(0.00001, 'ether')):
            logging.warning("Not enough RON balance to scatter and pay the tx.")
            return

        # Get Nonce
        if nonce is None:
            nonce = get_nonce(self.from_acc)
        # Build transaction
        transaction = self.contract.functions.disperseEther(
            self.to_list,
            self.amounts_list
        ).buildTransaction({
            "chainId": 2020,
            "gas": 1000000,
            "gasPrice": self.w3.toWei(str(gas_price), "gwei"),
            "nonce": nonce,
            "value": sum(self.amounts_list)
        })
        data = self.w3.toBytes(hexstr=transaction['data'])
        to = self.w3.toBytes(hexstr=SCATTER_CONTRACT)
        sig = ethereum.sign_tx(
            self.client,
            n=self.bip_path,
            nonce=nonce,
            gas_price=self.w3.toWei(str(gas_price), "gwei"),
            gas_limit=1000000,
            to=SCATTER_CONTRACT,
            value=sum(self.amounts_list),
            data=data,
            chain_id=2020
        )
        l_sig = list(sig)
        l_sig[1] = l_sig[1].lstrip(b'\x00')
        l_sig[2] = l_sig[2].lstrip(b'\x00')
        sig = tuple(l_sig)
        transaction = rlp.encode((nonce, self.w3.toWei(str(gas_price), "gwei"), 1000000, to, 0, data) + sig)
        # Send raw transaction
        self.w3.eth.send_raw_transaction(transaction)
        _hash = self.w3.toHex(self.w3.keccak(transaction))
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
            logging.info(f"Important: Transaction {self} completed! hash: {_hash} - "
                         f"Explorer: https://explorer.roninchain.com/tx/{str(_hash)}")
            return _hash
        else:
            logging.info(f"Important: Transaction {self} failed. Trying to augment gas price to unstuck it.")
            self.increase_gas_tx(nonce)

    def execute(self, gas_price=1, nonce=None):
        if self.token == 'ron':
            return self.execute_ron(gas_price, nonce)
        return self.execute_token(gas_price, nonce)

    def __str__(self):
        return f"Scatter of {self.token} from {self.from_acc.replace('0x', 'ronin:')}"
