from mock import patch

from axie_utils import TrezorConfig


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
