from datetime import datetime

from mock import patch
import requests_mock

from axie_utils import TrezorConfig, get_lastclaim


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
    assert d == datetime(2021, 12, 28, 1, 1, 55)


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
