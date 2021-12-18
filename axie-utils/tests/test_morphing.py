from mock import patch
import requests_mock
from hexbytes import HexBytes
from eth_account.messages import encode_defunct

from axie_utils.morphing import Morph, TrezorMorph
from tests.utils import MockedSignedMsg


def test_morph_init():
    m = Morph(axie=1, account="ronin:abcd1", private_key="0xabc1")
    assert m.axie == 1
    assert m.account == "0xabcd1"
    assert m.private_key == "0xabc1"


@patch("web3.eth.Eth.account.sign_message", return_value={"signature": HexBytes(b"123")})
@patch("axie_utils.Morph.get_jwt", return_value="token")
def test_morph_execute(mock_get_jwt, mock_sign_msg):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post(
            'https://graphql-gateway.axieinfinity.com/graphql',
            json={
                "data": {"morphAxie": True}
            }
        )
        m = Morph(axie=1, account="ronin:abc1", private_key="0xabc1")
        m.execute()
    mock_get_jwt.assert_called()
    mock_sign_msg.assert_called_with(encode_defunct(text=f"axie_id={m.axie}&owner={m.account}"),
                                     private_key=m.private_key)


@patch("web3.eth.Eth.account.sign_message", return_value={"signature": HexBytes(b"123")})
@patch("axie_utils.Morph.get_jwt", return_value="token")
def test_morph_execute_bad_json_response(mock_get_jwt, mock_sign_msg):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post(
            'https://graphql-gateway.axieinfinity.com/graphql',
            json={
                "foo": "bar"
            }
        )
        m = Morph(axie=1, account="ronin:abc1", private_key="0xabc1")
        m.execute()
    mock_get_jwt.assert_called()
    mock_sign_msg.assert_called_with(encode_defunct(text=f"axie_id={m.axie}&owner={m.account}"),
                                     private_key=m.private_key)


@patch("axie_utils.graphql.parse_path", return_value="m/44'/60'/0'/0/0")
def test_morph_init_trezor(mock_parse):
    m = TrezorMorph(axie=1, account="ronin:abcd1", client='client', bip_path="m/44'/60'/0'/0/0")
    mock_parse.assert_called()
    assert m.axie == 1
    assert m.account == "0xabcd1"
    assert m.client == "client"
    assert m.bip_path == "m/44'/60'/0'/0/0"


@patch("axie_utils.graphql.parse_path", return_value="m/44'/60'/0'/0/0")
@patch("axie_utils.morphing.ethereum.sign_message", return_value=MockedSignedMsg())
@patch("axie_utils.TrezorMorph.get_jwt", return_value="token")
def test_morph_execute_trezor(mock_get_jwt, mock_sign_msg, mock_parse):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post(
            'https://graphql-gateway.axieinfinity.com/graphql',
            json={
                "data": {"morphAxie": True}
            }
        )
        m = TrezorMorph(axie=1, account="ronin:abcd1", client='client', bip_path="m/44'/60'/0'/0/0")
        m.execute()
    mock_parse.assert_called()
    mock_get_jwt.assert_called()
    mock_sign_msg.assert_called()


@patch("axie_utils.graphql.parse_path", return_value="m/44'/60'/0'/0/0")
@patch("axie_utils.morphing.ethereum.sign_message", return_value=MockedSignedMsg())
@patch("axie_utils.TrezorMorph.get_jwt", return_value="token")
def test_morph_execute_bad_json_response_trezor(mock_get_jwt, mock_sign_msg, mock_parse):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post(
            'https://graphql-gateway.axieinfinity.com/graphql',
            json={
                "foo": "bar"
            }
        )
        m = TrezorMorph(axie=1, account="ronin:abcd1", client='client', bip_path="m/44'/60'/0'/0/0")
        m.execute()
    mock_parse.assert_called()
    mock_get_jwt.assert_called()
    mock_sign_msg.assert_called()
