from datetime import datetime
from tabnanny import check
from unittest import mock

from mock import patch, call
import requests_mock

from axie_utils import TrezorConfig, get_lastclaim, check_balance
from axie_utils.utils import (
    AXIE_CONTRACT,
    AXS_CONTRACT,
    SLP_CONTRACT,
    WETH_CONTRACT,
    USDC_CONTRACT
)


def test_trezor_config_init():
    tf = TrezorConfig(10, 'foo')
    assert tf.passphrase == 'foo'
    assert tf.accounts_number == 10
    tf = TrezorConfig(23)
    assert tf.passphrase == ''
    assert tf.accounts_number == 23


@patch('axie_utils.utils.parse_path', return_value='path')
@patch('axie_utils.utils.ethereum.get_address', return_value='0xbar')
@patch('axie_utils.utils.get_default_client', return_value='client')
def test_trezor_list_paths(mock_get_client, mocked_get_address, mocked_parse_path):
    tf = TrezorConfig(1, 'foo')
    resp = tf.list_bip_paths()
    mock_get_client.assert_called()
    mocked_parse_path.assert_called_with("m/44'/60'/0'/0/0")
    mocked_get_address.assert_called_with('client', 'path', True)
    assert resp == {"ronin:bar": {"passphrase": "foo", "bip_path": "m/44'/60'/0'/0/0"}}


def test_get_lastclaim():
    account = 'ronin:abc'
    url = f'https://game-api.skymavis.com/game-api/clients/{account.replace("ronin:", "0x")}/items/1'
    with requests_mock.Mocker() as req_mocker:
        req_mocker.get(url, json={"last_claimed_item_at": 1640649715})
        d = get_lastclaim(account)
    assert d == datetime(2021, 12, 28, 0, 1, 55)


def test_get_lastclaim_missing_data():
    account = 'ronin:abc'
    url = f'https://game-api.skymavis.com/game-api/clients/{account.replace("ronin:", "0x")}/items/1'
    with requests_mock.Mocker() as req_mocker:
        req_mocker.get(url,json={"foo": "bar"})
        d = get_lastclaim(account)
    assert d == None


def test_get_lastclaim_no_json():
    account = 'ronin:abc'
    url = f'https://game-api.skymavis.com/game-api/clients/{account.replace("ronin:", "0x")}/items/1'
    with requests_mock.Mocker() as req_mocker:
        req_mocker.get(url)
        d = get_lastclaim(account)
    assert d == None


@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress")
def test_check_balance_slp(mocked_checksum, mock_contract):
    balance = check_balance('account', 'slp')
    mocked_checksum.assert_has_calls(calls=[
        call(SLP_CONTRACT),
        call("account")
    ])
    mock_contract.assert_called()
    assert balance == 1


@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress")
def test_check_balance_axs(mocked_checksum, mock_contract):
    balance = check_balance('account', 'axs')
    mocked_checksum.assert_has_calls(calls=[
        call(AXS_CONTRACT),
        call("account")
    ])
    mock_contract.assert_called()
    assert balance == 1


@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress")
def test_check_balance_axies(mocked_checksum, mock_contract):
    balance = check_balance('account', 'axies')
    mocked_checksum.assert_has_calls(calls=[
        call(AXIE_CONTRACT),
        call("account")
    ])
    mock_contract.assert_called()
    assert balance == 1


@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress")
def test_check_balance_weth(mocked_checksum, mock_contract):
    balance = check_balance('account', 'weth')
    mocked_checksum.assert_has_calls(calls=[
        call(WETH_CONTRACT),
        call("account")
    ])
    mock_contract.assert_called()
    assert balance == 1


@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress")
def test_check_balance_usdc(mocked_checksum, mock_contract):
    balance = check_balance('account', 'usdc')
    mocked_checksum.assert_has_calls(calls=[
        call(USDC_CONTRACT),
        call("account")
    ])
    mock_contract.assert_called()
    assert balance == 1


@patch("web3.eth.Eth.get_balance", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value='addrs')
def test_check_balance_ron(mocked_checksum, mocked_balance):
    balance = check_balance('account', 'ron')
    mocked_checksum.assert_called_with('account')
    mocked_balance.assert_called_with('addrs')
    assert balance == 123 / 1000000000000000000


def test_check_balance_invalid():
    balance = check_balance('account', 'foo')
    assert balance == 0
