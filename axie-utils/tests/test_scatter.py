from mock import patch, call

from axie_utils import Scatter, TrezorScatter
from axie_utils.abis import SCATTER_ABI
from axie_utils.utils import (
    TOKENS,
    SLP_CONTRACT,
)
from tests.utils import MockedAllowed, MockedNotAllowed
    


def test_scatter_init():
    s = Scatter('slp', 'ronin:from_acc', '0xprivate_key', {'ronin:abc1': 1, 'ronin:dce2': 10})
    assert s.token == 'slp'
    assert s.from_acc == '0xfrom_acc'
    assert s.from_private == '0xprivate_key'
    assert s.to_list == ['ronin:abc1', 'ronin:dce2']
    assert s.amounts_list == [1, 10]

def test_scatter_init_ron():
    s = Scatter('ron', 'ronin:from_acc', '0xprivate_key', {'ronin:abc1': 1, 'ronin:dce2': 10})
    assert s.token == 'ron'
    assert s.from_acc == '0xfrom_acc'
    assert s.from_private == '0xprivate_key'
    assert s.to_list == ['ronin:abc1', 'ronin:dce2']
    assert s.amounts_list == [1, 10]


def test_scatter_init_trezor():
    s = TrezorScatter('slp', 'ronin:from_acc', 'client', "m/44'/60'/0'/0/0", {'ronin:abc1': 1, 'ronin:dce2': 10})
    assert s.token == 'slp'
    assert s.from_acc == '0xfrom_acc'
    assert s.client == 'client'
    assert s.to_list == ['ronin:abc1', 'ronin:dce2']
    assert s.amounts_list == [1, 10]


@patch("web3.eth.Eth.contract", return_value = MockedAllowed)
@patch("web3.Web3.toChecksumAddress")
def test_is_contract_accepted_success(mocked_checkssum, mocked_approve):
    s = Scatter('slp', 'ronin:from_acc', '0xprivate_key', {'ronin:abc1': 1, 'ronin:dce2': 10})
    mocked_checkssum.assert_called()
    mocked_approve.assert_called()
    assert s.is_contract_accepted() == True



@patch("axie_utils.scatter.Scatter.approve_contract", return_value='FOO')
@patch("web3.eth.Eth.contract", return_value = MockedNotAllowed)
@patch("web3.Web3.toChecksumAddress")
def test_is_contract_accepted_fail(mocked_checkssum, mocked_approve, _):
    s = Scatter('slp', 'ronin:from_acc', '0xprivate_key', {'ronin:abc1': 1, 'ronin:dce2': 10})
    mocked_checkssum.assert_called()
    mocked_approve.assert_called()
    assert s.is_contract_accepted() == "FOO"


@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.eth.Eth.account.sign_transaction")
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.wait_for_transaction_receipt", return_value={'status': 1})
def test_approve_contract(*args):
    s = Scatter('slp', 'ronin:from_acc', '0xprivate_key', {'ronin:abc1': 1, 'ronin:dce2': 10})
    r = s.approve_contract()
    assert r == True


@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.eth.Eth.account.sign_transaction")
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.wait_for_transaction_receipt", return_value={'status': 0})
def test_approve_contract_failed(*args):
    s = Scatter('slp', 'ronin:from_acc', '0xprivate_key', {'ronin:abc1': 1, 'ronin:dce2': 10})
    r = s.approve_contract()
    assert r == False


@patch("axie_utils.payments.rlp.encode")
@patch("web3.Web3.toBytes")
@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("axie_utils.payments.ethereum.sign_tx")
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.wait_for_transaction_receipt", return_value={'status': 1})
def test_approve_contract_trezor(*args):
    s = TrezorScatter('slp', 'ronin:from_acc', 'client', "m/44'/60'/0'/0/0", {'ronin:abc1': 1, 'ronin:dce2': 10})
    r = s.approve_contract()
    assert r == True


@patch("axie_utils.scatter.get_nonce", return_value=1)
def test_increase_gas_tx_no_avilable_nonce(mocked_nonce):
    s = Scatter('slp', 'ronin:from_acc', '0xprivate_key', {'ronin:abc1': 1, 'ronin:dce2': 10})
    r = s.increase_gas_tx(123)
    mocked_nonce.assert_called()
    assert r is None


@patch("axie_utils.scatter.Scatter.execute_token")
@patch("axie_utils.scatter.get_nonce", return_value=123)
def test_increase_gas_tx(mocked_nonce, mocked_execute_token):
    s = Scatter('slp', 'ronin:from_acc', '0xprivate_key', {'ronin:abc1': 1, 'ronin:dce2': 10})
    s.increase_gas_tx(123)
    mocked_nonce.assert_called()
    mocked_execute_token.assert_called_with(1.01, 123)


@patch("axie_utils.scatter.Scatter.execute_ron")
@patch("axie_utils.scatter.get_nonce", return_value=123)
def test_increase_gas_tx_ron(mocked_nonce, mocked_execute_ron):
    s = Scatter('ron', 'ronin:from_acc', '0xprivate_key', {'ronin:abc1': 1, 'ronin:dce2': 10})
    s.increase_gas_tx(123)
    mocked_nonce.assert_called()
    mocked_execute_ron.assert_called_with(1.01, 123)


@patch("axie_utils.scatter.check_balance", return_value=100000)
@patch("axie_utils.scatter.Scatter.is_contract_accepted", return_value=True)
@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.eth.Eth.account.sign_transaction")
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
def test_execute_token(*args):
    s = Scatter('slp', 'ronin:from_acc', '0xprivate_key', {'ronin:abc1': 1, 'ronin:dce2': 10})
    resp = s.execute()
    assert resp == 'transaction_hash'


@patch("axie_utils.scatter.check_balance", return_value=100000)
@patch("axie_utils.scatter.TrezorScatter.is_contract_accepted", return_value=True)
@patch("axie_utils.payments.rlp.encode")
@patch("web3.Web3.toBytes")
@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("axie_utils.payments.ethereum.sign_tx")
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
def test_execute_token_trezor(*args):
    s = TrezorScatter('slp', 'ronin:from_acc', 'client', "m/44'/60'/0'/0/0", {'ronin:abc1': 1, 'ronin:dce2': 10})
    resp = s.execute()
    assert resp == 'transaction_hash'


@patch("axie_utils.scatter.check_balance", return_value=100000)
@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.eth.Eth.account.sign_transaction")
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
def test_execute_ron(*args):
    s = Scatter('ron', 'ronin:from_acc', '0xprivate_key', {'ronin:abc1': 1, 'ronin:dce2': 10})
    resp = s.execute()
    assert resp == 'transaction_hash'


@patch("axie_utils.scatter.check_balance", return_value=100000)
@patch("axie_utils.payments.rlp.encode")
@patch("web3.Web3.toBytes")
@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("axie_utils.payments.ethereum.sign_tx")
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
def test_execute_ron_trezor(*args):
    s = TrezorScatter('ron', 'ronin:from_acc', 'client', "m/44'/60'/0'/0/0", {'ronin:abc1': 1, 'ronin:dce2': 10})
    resp = s.execute()
    assert resp == 'transaction_hash'