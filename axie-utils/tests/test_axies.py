from datetime import datetime, timedelta

from mock import patch, call
from freezegun import freeze_time
import requests_mock
import pytest

from axie_utils import Axies
from axie_utils.abis import AXIE_ABI
from axie_utils.utils import AXIE_CONTRACT, RONIN_PROVIDER, USER_AGENT
from tests.utils import MockedOwner

@freeze_time('2021-01-14 01:10:05')
@patch("web3.eth.Eth.contract", return_value="contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_axies_init(mocked_provider, mocked_checksum, mocked_contract):
    a = Axies("ronin:abc1")
    mocked_provider.assert_called_with(
        RONIN_PROVIDER,
        request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
    )
    mocked_checksum.assert_called_with(AXIE_CONTRACT)
    mocked_contract.assert_called_with(address="checksum", abi=AXIE_ABI)
    assert a.acc == "0xabc1"
    assert a.now == datetime(2021, 1, 14, 1, 10, 5)
    assert a.contract == "contract"


@patch("axie_utils.axies.check_balance", return_value=100)
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
def test_number_of_axies(mocked_checksum, mocked_contract, mocked_balance_of):
    a = Axies("ronin:abc1")
    number = a.number_of_axies()
    assert number == 100
    mocked_balance_of.assert_called_with(a.acc, 'axies')
    mocked_checksum.assert_called_with(AXIE_CONTRACT)
    mocked_contract.assert_called_with(address="checksum", abi=AXIE_ABI)


@patch("web3.eth.Eth.contract", return_value=MockedOwner)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
def test_check_axie_owner(mocked_checksum, mocked_contract):
    a = Axies("ronin:abc123")
    owner = a.check_axie_owner(123)
    assert owner == True
    a = Axies("ronin:abc1234")
    owner = a.check_axie_owner(123)
    assert owner == False
    mocked_checksum.assert_called_with(AXIE_CONTRACT)
    mocked_contract.assert_called_with(address="checksum", abi=AXIE_ABI)


@patch("web3.eth.Eth.contract.functions.tokenOfOwnerByIndex")
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("axie_utils.Axies.number_of_axies", return_value=5)
def test_get_axies(mocked_number_of_axies, mocked_checksum, mocked_contract, _):
    a = Axies("ronin:abc1")
    axies = a.get_axies()
    mocked_contract.assert_called_with(address="checksum", abi=AXIE_ABI)
    mocked_number_of_axies.assert_called()
    mocked_checksum.assert_has_calls(calls=[
        call(AXIE_CONTRACT), call(a.acc)
    ])
    assert len(axies) == 5


@freeze_time('2021-01-14 01:10:05')
@patch("web3.eth.Eth.contract.functions.tokenOfOwnerByIndex")
@patch("axie_utils.Axies.get_morph_date_and_body", return_value=(None, None))
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("axie_utils.Axies.number_of_axies", return_value=1)
def test_find_axies_to_morph_none_morph_date_shape(mocked_number_of_axies,
                                                   mocked_checksum,
                                                   mocked_contract,
                                                   mocked_get_data,
                                                   _):
    a = Axies("ronin:abc1")
    axies_to_morph = a.find_axies_to_morph()
    mocked_contract.assert_called_with(address="checksum", abi=AXIE_ABI)
    mocked_number_of_axies.assert_called()
    mocked_checksum.assert_has_calls(calls=[
        call(AXIE_CONTRACT), call(a.acc)
    ])
    mocked_get_data.assert_called()
    assert axies_to_morph == []


@freeze_time('2021-01-14 01:10:05')
@patch("web3.eth.Eth.contract.functions.tokenOfOwnerByIndex")
@patch("axie_utils.Axies.get_morph_date_and_body", return_value=(datetime(2021, 1, 14, 1, 0, 0), "Normal"))
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("axie_utils.Axies.number_of_axies", return_value=1)
def test_find_axies_to_morph_already_adult(mocked_number_of_axies,
                                           mocked_checksum,
                                           mocked_contract,
                                           mocked_get_data,
                                           _):
    a = Axies("ronin:abc1")
    axies_to_morph = a.find_axies_to_morph()
    mocked_contract.assert_called_with(address="checksum", abi=AXIE_ABI)
    mocked_number_of_axies.assert_called()
    mocked_checksum.assert_has_calls(calls=[
        call(AXIE_CONTRACT), call(a.acc)
    ])
    mocked_get_data.assert_called()
    assert axies_to_morph == []


@freeze_time('2021-01-14 01:10:05')
@patch("web3.eth.Eth.contract.functions.tokenOfOwnerByIndex")
@patch("axie_utils.Axies.get_morph_date_and_body",
       return_value=(datetime(2021, 1, 14, 1, 10, 5)+timedelta(days=2), None))
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("axie_utils.Axies.number_of_axies", return_value=1)
def test_find_axies_to_morph_not_hatch_time(mocked_number_of_axies,
                                            mocked_checksum,
                                            mocked_contract,
                                            mocked_get_data,
                                            _):
    a = Axies("ronin:abc1")
    axies_to_morph = a.find_axies_to_morph()
    mocked_contract.assert_called_with(address="checksum", abi=AXIE_ABI)
    mocked_number_of_axies.assert_called()
    mocked_checksum.assert_has_calls(calls=[
        call(AXIE_CONTRACT), call(a.acc)
    ])
    mocked_get_data.assert_called()
    assert axies_to_morph == []


@patch("web3.eth.Eth.contract.functions.tokenOfOwnerByIndex")
@patch("axie_utils.Axies.get_morph_date_and_body", return_value=(datetime(2021, 1, 14, 0, 0, 0), None))
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("axie_utils.Axies.number_of_axies", return_value=1)
@freeze_time('2021-01-14 01:10:05')
def test_find_axies_to_morph(mocked_number_of_axies,
                             mocked_checksum,
                             mocked_contract,
                             mocked_get_data,
                             _):
    a = Axies("ronin:abc1")
    axies_to_morph = a.find_axies_to_morph()
    mocked_contract.assert_called_with(address="checksum", abi=AXIE_ABI)
    mocked_number_of_axies.assert_called()
    mocked_checksum.assert_has_calls(calls=[
        call(AXIE_CONTRACT), call(a.acc)
    ])
    mocked_get_data.assert_called()
    assert len(axies_to_morph) == 1


@freeze_time('2021-01-14 01:10:05')
def test_get_morph_date_body():
    birth_date = datetime.timestamp(datetime.now())
    morph_date = datetime.fromtimestamp(birth_date) + timedelta(days=5)
    body_shape = "foo"
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        json={"data": {"axie": {"bodyShape": body_shape, "birthDate": birth_date}}})
        a = Axies("ronin:abc1")
        resp = a.get_morph_date_and_body(123)
    assert resp == (morph_date, body_shape)


@freeze_time('2021-01-14 01:10:05')
def test_get_morph_date_body_no_json():
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql")
        a = Axies("ronin:abc1")
        resp = a.get_morph_date_and_body(123)
    assert resp == (None, None)


@pytest.mark.parametrize("mocked_json", [
    ({}),
    ({"foo": "bar"}),
    ({"data": {"foo": "bar"}}),
    ({"data": {"axie": "bar"}}),
    ({"data": {"axie": {"bar": "foo"}}}),
    ({"data": {"axie": {"bodyShape": "foo"}}}),
    ({"data": {"axie": {"birthDate": "foo"}}})
])
@freeze_time('2021-01-14 01:10:05')
def test_get_morph_date_body_malformed_json(mocked_json):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql", json=mocked_json)
        a = Axies("ronin:abc1")
        resp = a.get_morph_date_and_body(123)
    assert resp == (None, None)


def test_get_axie_details_success():
    mocked_json = {
        'data': {
            'axie': {
                'id': '123',
                'class': 'Beast',
                'parts': [
                    {'id': 'eyes-clear', 'name': 'Clear', 'class': 'Aquatic', 'type': 'Eyes'},
                    {'id': 'ears-inkling', 'name': 'Inkling', 'class': 'Aquatic', 'type': 'Ears'},
                    {'id': 'back-goldfish', 'name': 'Goldfish', 'class': 'Aquatic', 'type': 'Back'},
                    {'id': 'mouth-risky-fish', 'name': 'Risky Fish', 'class': 'Aquatic', 'type': 'Mouth'},
                    {'id': 'horn-shoal-star', 'name': 'Shoal Star', 'class': 'Aquatic', 'type': 'Horn'},
                    {'id': 'tail-nimo', 'name': 'Nimo', 'class': 'Aquatic', 'type': 'Tail'}
                ]
            }
        }
    }
    expected_response = {
        'eyes': 'clear',
        'ears': 'inkling',
        'back': 'goldfish',
        'mouth': 'risky fish',
        'horn': 'shoal star',
        'tail': 'nimo',
        'class': 'beast'
    }
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql", json=mocked_json)
        a = Axies("ronin:abc1")
        resp = a.get_axie_details(123)
    assert resp == expected_response


def test_get_axie_details_incomplete_data():
    mocked_json = {'data': {'axie': {'id': '123'}}}
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql", json=mocked_json)
        a = Axies("ronin:abc1")
        resp = a.get_axie_details(123)
    assert resp == None

def test_get_axie_details_fail_req():
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql", status_code=500)
        a = Axies("ronin:abc1")
        resp = a.get_axie_details(123)
    assert resp == None